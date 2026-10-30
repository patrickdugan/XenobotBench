# Local validation

40 unittest cases passed. Two complete scripted campaigns produced 96 episodes across four tracks and 12 seeds per campaign. Both records passed offline replay/regrading. The paired comparison completed successfully. The reference solver passed every task; the abstention baseline received zero task credit and its abstentions were counted separately.

Tests cover hypothesis identifiability, seed determinism, oracle-field exclusion, strict JSON, numeric types, probe and turn limits, pause enforcement, unauthorized calls, immutable output paths, budget mismatch, tamper detection, transport errors, API request construction, and redirect rejection.

Commands:

```bash
python -m unittest discover -s tests -v
python -m xenobotbench run --scripted reference --out results/reference.json
python -m xenobotbench run --scripted abstain --out results/abstain.json
python -m xenobotbench verify results/reference.json
python -m xenobotbench verify results/abstain.json
python -m xenobotbench compare results/reference.json results/abstain.json --out results/comparison.json
```

The accompanying smoke_summary.json records source and report hashes. API behavior was tested with mocked responses. No live Kimi, local LLM, or corporate model was evaluated. No paid service was called. GitHub CI execution has not been established.
