# Offline MOMbot-inspired control validation

2026-10-31. Python 3.13. Standard-library only.

- `python -m unittest discover -s tests -v`: **23/23 pass**, using the isolated new tests.
- `python -m xenobotbench.mombot_safety run --policy reference`: **108 episodes / 12 independent seeds**, **108 passed**, 0 unsafe attempts, 204 authorized steps.
- `python -m xenobotbench.mombot_safety run --policy always_continue`: **108 episodes**, **36 passed**, 72 blocked unsafe continuations, 204 authorized steps before attempted violations.
- Both saved reports passed offline replay and regrading. A paired comparison completed over 12 seed clusters, with candidate-minus-reference pass rate -0.6667 and unsafe fraction +0.6667. The observed bootstrap intervals were degenerate because the test fixtures have identical outcome patterns across seeds.
- Tests cover missing/discordant data, unexpected observations, inclusive boundaries, trusted pause and revocation, untrusted approval and prompt-injection attempts, blocked continuation, overconservative stopping, malformed and abstained outputs, future-observation isolation, reproducibility, replay after tampering even when rehashed, duplicate JSON keys, non-finite values, seed cluster counting, panel mismatch, callback input immutability, and create-only output files.

This validation did not run the separate pre-existing XenobotBench v0.1 unit tests, any model, GPU, external API, or laboratory instrument. GitHub CI is unknown until the branch is pushed. Synthetic performance establishes only that the programmed reference policy and evaluator agree.
