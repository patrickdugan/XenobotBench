# Sources and provenance

Checked 2026-10-31. Sources motivate scope and integration; the benchmark equations and grading rules are authored here.

## Existing project work

- ALife xenobots v0.1: https://github.com/MoralityLabAI/ALife/tree/8eec325545e19e37188c84b19eb9d7ece5089f0e/xenobots
- Levinverse research integration: https://github.com/patrickdugan/levinverse/blob/main/research/integration.md
- Distributed-memory v0.2: conversation artifact `ALife_Xenobots_Distributed_Memory_v02.zip`. `xenobotbench/alife_fixture.json` pins the archive, upstream CSV, and upstream model hashes. The imported subset preserves quiet-corner and noisy-corner recall values for both targets at all 12 original holdout seeds. Publication of v0.2 to ALife main was not verified.

The v0.2 recall-ceiling derivation motivates the graph task. Evidence-audit questions use its actual archived synthetic output. This import performs no upstream simulator execution and supplies no independent biological validation.

## Published corporate workflow

Anthropic, 2026-09-23, "Claude discovers a novel enzyme system with CRISPR-like repeats": https://www.anthropic.com/research/claude-discovers-novel-enzyme-system

The vendor describes AI-led computational hypothesis generation, human review, and experiments performed by human scientists. This supports evaluating analysis and evidence-handling workflows. The article provides no demonstration of autonomous hazardous xenobot construction. No corporate model score is inferred from it.

## Model interface

- Kimi API overview: https://www.kimi.ai/help/kimi-api/api-overview
- Kimi API troubleshooting: https://www.kimi.ai/help/kimi-api/api-troubleshooting

These document a compatible Chat Completions interface, model identifiers, completion-token parameters, and product-specific API keys. The example endpoint is `https://api.moonshot.ai/v1`. Provider access, pricing, and model aliases can change. The adapter was tested against mocked responses locally; a live credentialed run remains outstanding.
