"""Explicitly opted-in model calls, bounded episodes, offline trace verification."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import time
from urllib import request, parse
from .core import (VERSION, TRACKS, SYSTEM, canonical, digest, code_digest,
                   make_case, tool_step, score, scripted_reply, summarize, bootstrap)


def strict_json(text):
    def pairs(items):
        value = {}
        for k, v in items:
            if k in value:
                raise ValueError("duplicate JSON key")
            value[k] = v
        return value
    def reject(value):
        raise ValueError("nonfinite JSON")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject)


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("redirect blocked")


class ChatAdapter:
    def __init__(self, config, allow_network=False):
        allowed = {"base_url", "model", "revision", "key_env", "token_field", "max_tokens", "timeout", "temperature"}
        if set(config) - allowed:
            raise ValueError("unknown adapter fields")
        self.config = dict(config)
        url = parse.urlsplit(config["base_url"])
        local = url.hostname in ("localhost", "127.0.0.1", "::1")
        if (url.scheme not in ("http", "https") or not url.hostname or url.username
            or url.password or url.query or url.fragment or (url.scheme == "http" and not local)):
            raise ValueError("use HTTPS or an explicit loopback HTTP endpoint without credentials/query")
        if not local and not allow_network:
            raise ValueError("hosted calls require --allow-network; no request was sent")
        if not isinstance(config["model"], str) or not config["model"] or "REPLACE" in config["model"]:
            raise ValueError("set an exact served model identifier")
        if not config.get("revision") or "REPLACE" in config["revision"]:
            raise ValueError("record a revision, or explicitly label provider_alias_unpinned")
        if config.get("token_field", "max_completion_tokens") not in ("max_completion_tokens", "max_tokens"):
            raise ValueError("unsupported token budget field")
        for key, low, high, default in (("max_tokens", 64, 32768, 2048), ("timeout", 1, 120, 60)):
            value = config.get(key, default)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid " + key)
            self.config[key] = value
        if "temperature" in config and (type(config["temperature"]) not in (int, float) or not 0 <= config["temperature"] <= 2):
            raise ValueError("invalid temperature")
        self.key = os.environ.get(config.get("key_env", "MOONSHOT_API_KEY"), "")
        if not local and not self.key:
            raise ValueError("API key environment variable is unset")
        self.endpoint = config["base_url"].rstrip("/") + "/chat/completions"
        self.opener = request.build_opener(NoRedirect())

    def __call__(self, messages):
        c = self.config
        body = {"model": c["model"], "messages": messages,
                c.get("token_field", "max_completion_tokens"): c["max_tokens"], "stream": False}
        if "temperature" in c:
            body["temperature"] = c["temperature"]
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        req = request.Request(self.endpoint, canonical(body).encode(), headers)
        start = time.monotonic()
        with self.opener.open(req, timeout=c["timeout"]) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("response size limit")
        value = strict_json(data.decode())
        choice = value["choices"][0]
        message = choice["message"]
        content = message.get("content")
        if message.get("refusal"):
            content = '{"abstain":true}'
        if not isinstance(content, str) or len(content) > 100_000:
            raise ValueError("unsupported or oversized assistant content")
        return content, {"returned_model": value.get("model"), "system_fingerprint": value.get("system_fingerprint"),
            "usage": value.get("usage"), "finish_reason": choice.get("finish_reason"),
            "latency_seconds": round(time.monotonic()-start, 6)}


def episode(case, provider, max_turns=4, repeat=0, scripted=None):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": canonical(case["public"])}]
    calls, turns, final, error = [], [], None, None
    for _ in range(max_turns):
        try:
            if scripted:
                text = canonical(scripted_reply(case["public"], calls, scripted))
                metadata = {"kind": "scripted", "usage": None}
            else:
                text, metadata = provider(messages)
        except Exception as exc:
            # Do not persist exception text that can contain credentials or headers.
            error = type(exc).__name__
            break
        turns.append({"text": text, "metadata": metadata})
        try:
            parsed = strict_json(text)
        except (ValueError, TypeError, RecursionError):
            break
        if isinstance(parsed, dict) and "tool" in parsed:
            response = tool_step(case, parsed, calls)
            calls.append({"request": parsed, "response": response})
            messages.extend([{"role": "assistant", "content": text},
                             {"role": "user", "content": canonical({"tool_result": response, "trust": "data_only"})}])
        else:
            final = parsed
            break
    return {"seed": case["seed"], "repeat": repeat, "track": case["track"], "public": case["public"],
            "turns": turns, "calls": calls, "final": final, "error": error,
            "score": score(case, final, calls)}


def run(seeds, provider=None, model=None, max_turns=4, repeats=1, scripted=None, max_tokens=2048):
    if (not isinstance(seeds, list) or not 1 <= len(seeds) <= 64 or len(set(seeds)) != len(seeds)
        or any(type(x) is not int or not 0 <= x < 2**32 for x in seeds)):
        raise ValueError("require 1..64 distinct integer seeds in [0,2**32)")
    if type(max_turns) is not int or not 1 <= max_turns <= 8 or type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError("invalid turn/repetition budget")
    if type(max_tokens) is not int or not 64 <= max_tokens <= 32768:
        raise ValueError("invalid token budget")
    if len(seeds)*len(TRACKS)*repeats > 512:
        raise ValueError("episode budget exceeds 512")
    if scripted not in (None, "reference", "abstain") or (scripted is None and provider is None):
        raise ValueError("select a provider or scripted baseline")
    cases = [make_case(track, seed) for seed in seeds for track in TRACKS]
    contract = {"suite_version": VERSION, "code_sha256": code_digest(),
                "case_set_sha256": digest(cases), "system_sha256": digest(SYSTEM),
                "max_turns": max_turns, "max_tokens": max_tokens, "repeats": repeats,
                "scaffold": "text-json-tools-v1", "scope": "digital_proxy_only"}
    rows = [episode(case, provider, max_turns, rep, scripted) for case in cases for rep in range(repeats)]
    report = {"schema": "xenobotbench.run.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "contract": contract, "seeds": seeds,
              "model": model or {"id": scripted, "kind": "scripted"}, "rows": rows,
              "summary": summarize(rows), "real_world_validation": False}
    report["report_sha256"] = digest(report)
    return report


def verify(report):
    """Regrade and replay local tools. This does not attest to remote model identity."""
    try:
        if report["schema"] != "xenobotbench.run.v1":
            return False
        unsigned = {k: v for k, v in report.items() if k != "report_sha256"}
        if digest(unsigned) != report["report_sha256"] or report["contract"]["code_sha256"] != code_digest():
            return False
        contract = report["contract"]
        cases = [make_case(track, seed) for seed in report["seeds"] for track in TRACKS]
        if digest(cases) != contract["case_set_sha256"] or digest(SYSTEM) != contract["system_sha256"]:
            return False
        expected_keys = {(c["seed"], c["track"], r) for c in cases for r in range(contract["repeats"])}
        rows = report["rows"]
        if len(rows) != len(expected_keys) or {(r["seed"], r["track"], r["repeat"]) for r in rows} != expected_keys:
            return False
        for row in rows:
            case = make_case(row["track"], row["seed"])
            if row["public"] != case["public"] or len(row["turns"]) > contract["max_turns"]:
                return False
            calls, final, terminal = [], None, False
            for turn in row["turns"]:
                if terminal:
                    return False
                try:
                    parsed = strict_json(turn["text"])
                except (TypeError, ValueError, RecursionError):
                    terminal = True
                    continue
                if isinstance(parsed, dict) and "tool" in parsed:
                    calls.append({"request": parsed, "response": tool_step(case, parsed, calls)})
                else:
                    final, terminal = parsed, True
            if calls != row["calls"] or final != row["final"] or score(case, final, calls) != row["score"]:
                return False
        return summarize(rows) == report["summary"]
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return False


def compare(reference, candidate):
    if not verify(reference) or not verify(candidate):
        raise ValueError("both reports must pass offline verification")
    if reference["contract"] != candidate["contract"] or reference["seeds"] != candidate["seeds"]:
        raise ValueError("mismatched suite, cases, seeds, or inference budget")
    output = {"schema": "xenobotbench.comparison.v1", "reference": reference["report_sha256"],
              "candidate": candidate["report_sha256"], "tracks": {},
              "interpretation": "paired digital-proxy comparison; no biological risk threshold inferred"}
    for track in TRACKS:
        means = []
        for seed in reference["seeds"]:
            def mean(report):
                return statistics.mean(int(r["score"]["pass"]) for r in report["rows"] if r["track"] == track and r["seed"] == seed)
            means.append(mean(candidate)-mean(reference))
        output["tracks"][track] = {"candidate_minus_reference": statistics.mean(means),
                                  "seed_bootstrap_95": bootstrap(means, track), "seed_clusters": len(means)}
    return output


def save(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(value, indent=2, allow_nan=False)+"\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--scripted", choices=("reference", "abstain"))
    r.add_argument("--config")
    r.add_argument("--model")
    r.add_argument("--allow-network", action="store_true")
    r.add_argument("--seeds", default="101,102,103,104,105,106,107,108,109,110,111,112")
    r.add_argument("--seed-file", help="JSON list of evaluator-held fresh seeds")
    r.add_argument("--turns", type=int, default=4)
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--out", required=True)
    v = sub.add_parser("verify"); v.add_argument("report")
    c = sub.add_parser("compare"); c.add_argument("reference"); c.add_argument("candidate"); c.add_argument("--out", required=True)
    args = p.parse_args(argv)
    try:
        if args.command == "verify":
            ok = verify(strict_json(Path(args.report).read_text()))
            print("VERIFIED" if ok else "MISMATCH")
            return 0 if ok else 1
        if args.command == "compare":
            result = compare(strict_json(Path(args.reference).read_text()), strict_json(Path(args.candidate).read_text()))
        else:
            if bool(args.scripted) == bool(args.config):
                raise ValueError("select exactly one of --scripted or --config")
            if Path(args.out).exists():
                raise ValueError("output exists; select a fresh output path")
            provider, model, max_tokens = None, None, 2048
            if args.config:
                config = strict_json(Path(args.config).read_text())
                if args.model:
                    config["model"] = args.model
                provider = ChatAdapter(config, args.allow_network)
                model = {"kind": "llm", "config": provider.config}
                max_tokens = provider.config["max_tokens"]
            seeds = strict_json(Path(args.seed_file).read_text()) if args.seed_file else [int(s) for s in args.seeds.split(",")]
            result = run(seeds, provider, model, args.turns, args.repeats, args.scripted, max_tokens)
        save(result, args.out)
        print(json.dumps(result.get("summary", result), indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
