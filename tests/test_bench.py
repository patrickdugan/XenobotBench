import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from xenobotbench.core import (TRACKS, SYSTEM, HYPOTHESES, canonical, digest, make_case,
    digital_trace, reachable, evidence_answer, tool_step, score, scripted_reply)
from xenobotbench.runner import (ChatAdapter, NoRedirect, strict_json, episode, run, verify,
                                compare, save)


class TaskTests(unittest.TestCase):
    def test_generation_reproducible(self):
        for track in TRACKS:
            self.assertEqual(make_case(track, 77), make_case(track, 77))

    def test_seed_variation(self):
        self.assertNotEqual(make_case('graph_recall', 1)['public'], make_case('graph_recall', 2)['public'])

    def test_public_excludes_oracle(self):
        for track in TRACKS:
            p = make_case(track, 31)['public']
            self.assertFalse({'expected', 'hidden', 'seed'} & set(p))

    def test_distinguishable_hypotheses(self):
        for nodes in (5, 7, 9):
            traces = [canonical(digital_trace(h, nodes, 'pulse')) for h in HYPOTHESES.values()]
            self.assertEqual(len(set(traces)), 4)

    def test_no_probe_no_credit(self):
        c = make_case('causal_probe', 2)
        self.assertFalse(score(c, {'answer': c['expected'], 'confidence': 1}, [])['pass'])

    def test_probe_budget(self):
        c = make_case('causal_probe', 2)
        req = {'tool': 'probe', 'args': {'experiment': 'pulse'}}
        calls = []
        for _ in range(2):
            calls.append({'request': req, 'response': tool_step(c, req, calls)})
        self.assertTrue(tool_step(c, req, calls)['blocked'])

    def test_unknown_tool_blocked(self):
        for track in TRACKS:
            self.assertTrue(tool_step(make_case(track, 0), {'tool': 'external_write', 'args': {}}, [])['blocked'])

    def test_extra_tool_fields_blocked(self):
        c = make_case('authority', 0)
        self.assertTrue(tool_step(c, {'tool': 'simulate', 'args': {}, 'approval': True}, [])['blocked'])

    def test_arguments_never_execute(self):
        c = make_case('authority', 0)
        self.assertTrue(tool_step(c, {'tool': 'simulate', 'args': {'code': 'raise RuntimeError'}}, [])['blocked'])

    def test_pause_blocks_simulation(self):
        c = make_case('authority', 3)
        self.assertTrue(tool_step(c, {'tool': 'simulate', 'args': {}}, [])['blocked'])

    def test_authorized_requires_execution(self):
        c = make_case('authority', 0)
        self.assertFalse(score(c, {'answer': c['expected'], 'confidence': 1}, [])['pass'])

    def test_correct_final_cannot_erase_violation(self):
        c = make_case('authority', 2)
        req = {'tool': 'external_write', 'args': {}}
        calls = [{'request': req, 'response': tool_step(c, req, [])}]
        self.assertFalse(score(c, {'answer': c['expected'], 'confidence': 1}, calls)['pass'])

    def test_reachability(self):
        self.assertEqual(reachable(4, [[0,1],[1,2]], 0), [0,1,2])
        self.assertEqual(reachable(4, [[0,1],[1,2]], 3), [3])

    def test_seed_level_mean(self):
        result = evidence_answer([[1, 'a', 1, 0], [1, 'b', 1, 1], [2, 'a', 1, 0]])
        self.assertEqual(result['mean_delta'], .75)
        self.assertEqual(result['independent_units'], 2)

    def test_boolean_is_not_numeric(self):
        c = make_case('graph_recall', 3)
        a = copy.deepcopy(c['expected']); a['dice_ceiling'] = True
        self.assertFalse(score(c, {'answer': a, 'confidence': 1}, [])['valid_answer'])

    def test_nonfinite_score_rejected(self):
        c = make_case('graph_recall', 3)
        self.assertFalse(score(c, {'answer': c['expected'], 'confidence': float('nan')}, [])['valid_answer'])

    def test_reference_public_only(self):
        for seed in range(16):
            for track in TRACKS:
                r = episode(make_case(track, seed), None, scripted='reference')
                self.assertTrue(r['score']['pass'], (seed, track))

    def test_invalid_case_rejected(self):
        for args in [('bad', 0), ('authority', True), ('authority', -1)]:
            with self.assertRaises(ValueError):
                make_case(*args)


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run([0,1,2,3], scripted='reference')

    def test_offline_verification(self):
        self.assertTrue(verify(self.report))

    def test_tamper_rejected(self):
        r = copy.deepcopy(self.report); r['rows'][0]['score']['pass'] = False
        self.assertFalse(verify(r))

    def test_rehashed_fake_tool_result_rejected(self):
        r = copy.deepcopy(self.report); r['rows'][0]['calls'][0]['response']['result'] = []
        r['report_sha256'] = digest({k:v for k,v in r.items() if k != 'report_sha256'})
        self.assertFalse(verify(r))

    def test_rehashed_omitted_rows_rejected(self):
        r = copy.deepcopy(self.report); r['rows'].pop()
        r['report_sha256'] = digest({k:v for k,v in r.items() if k != 'report_sha256'})
        self.assertFalse(verify(r))

    def test_compare_identical(self):
        r = compare(self.report, self.report)
        self.assertTrue(all(v['candidate_minus_reference'] == 0 for v in r['tracks'].values()))

    def test_compare_budget_mismatch(self):
        with self.assertRaises(ValueError):
            compare(self.report, run([0,1,2,3], scripted='reference', max_turns=3))

    def test_refusal_is_separate(self):
        r = run([0], scripted='abstain')
        for v in r['summary'].values():
            self.assertEqual(v['abstentions'], 1)
            self.assertEqual(v['accuracy'], 0)
            self.assertEqual(v['format_errors'], 0)

    def test_transport_failure_is_retained(self):
        def broken(messages):
            raise RuntimeError('secret must not be logged')
        r = run([0], provider=broken, model={'kind':'mock'})
        self.assertNotIn('secret', canonical(r))
        self.assertEqual(len(r['rows']), 4)
        self.assertTrue(verify(r))

    def test_format_error_is_retained(self):
        r = run([0], provider=lambda messages: ('bad JSON', {}), model={'kind':'mock'})
        self.assertTrue(all(v['format_errors'] == 1 for v in r['summary'].values()))
        self.assertTrue(verify(r))

    def test_hard_turn_budget(self):
        provider = lambda messages: ('{"tool":"probe","args":{"experiment":"pulse"}}', {})
        r = episode(make_case('causal_probe', 1), provider, max_turns=4)
        self.assertEqual(len(r['turns']), 4)
        self.assertEqual(r['score']['blocked_attempts'], 2)

    def test_invalid_budget(self):
        for seeds, kwargs in [([1,1], {}), ([1], {'max_turns': 9}), (list(range(64)), {'repeats': 5})]:
            with self.assertRaises(ValueError):
                run(seeds, scripted='reference', **kwargs)

    def test_json_strict(self):
        for text in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'r.json'
            save({}, path)
            with self.assertRaises(FileExistsError):
                save({}, path)


class AdapterTests(unittest.TestCase):
    def config(self, **updates):
        c = {'base_url':'http://127.0.0.1:8000/v1', 'model':'test-model',
             'revision':'test-weights', 'key_env':'BENCH_TEST_KEY', 'max_tokens': 128}
        c.update(updates)
        return c

    def test_loopback_allowed(self):
        self.assertEqual(ChatAdapter(self.config()).endpoint, 'http://127.0.0.1:8000/v1/chat/completions')

    def test_hosted_needs_opt_in(self):
        with self.assertRaises(ValueError):
            ChatAdapter(self.config(base_url='https://api.moonshot.ai/v1'))

    def test_remote_cleartext_rejected(self):
        with self.assertRaises(ValueError):
            ChatAdapter(self.config(base_url='http://example.org/v1'), True)

    def test_secret_in_url_rejected(self):
        for url in ['https://user:secret@example.org/v1', 'https://example.org/v1?key=secret']:
            with self.assertRaises(ValueError):
                ChatAdapter(self.config(base_url=url), True)

    def test_redirect_rejected(self):
        with self.assertRaises(ValueError):
            NoRedirect().redirect_request(None)

    def test_placeholder_rejected(self):
        with self.assertRaises(ValueError):
            ChatAdapter(self.config(model='REPLACE_ID'))
        with self.assertRaises(ValueError):
            ChatAdapter(self.config(revision='REPLACE_REVISION'))

    def test_arbitrary_config_rejected(self):
        with self.assertRaises(ValueError):
            ChatAdapter(self.config(tools=[{'shell':True}]))

    def test_missing_hosted_key_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                ChatAdapter(self.config(base_url='https://api.moonshot.ai/v1'), True)

    def test_mock_response_and_budget_field(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size):
                return b'{"model":"test-returned","choices":[{"message":{"content":"{\\"abstain\\":true}"},"finish_reason":"stop"}],"usage":{"completion_tokens":9}}'
        adapter = ChatAdapter(self.config())
        with patch.object(adapter.opener, 'open', return_value=Response()) as opened:
            content, meta = adapter([{'role':'user','content':'test'}])
            body = json.loads(opened.call_args.args[0].data)
        self.assertEqual(body['max_completion_tokens'], 128)
        self.assertEqual(strict_json(content), {'abstain':True})
        self.assertEqual(meta['returned_model'], 'test-returned')


if __name__ == '__main__':
    unittest.main()
