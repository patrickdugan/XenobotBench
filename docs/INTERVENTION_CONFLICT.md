# MOP-02: Goal-preserving multi-action abstraction challenge

**Scope:** Invented finite digital Markov systems only. No wet-lab design, biological optimization, or real model capability inference. This extends [MOP-01](MORPHOSPACE_QUOTIENT.md) from deterministic observational quotients to **goal-preserving, approximate stochastic quotients** with several permitted actions.

The mathematical reference is [QO-03](https://github.com/MoralityLabAI/Compactification-Theory/blob/main/research/ingression_dynamics_v1/MULTIACTION_COLORING.md), which proves for an absorbing-goal hit/hold family that grouping states is equivalent to coloring a graph whose edges represent pairs that exceed a declared one-step TV error tolerance. With four total macrostate labels (two bits) and tolerance 1/4, edge-indexed hit-rate systems encode graph 3-colorability.

## Digital scoring contract

A case contains a simple graph on \(n\) transient states and a separate absorbing goal state \(n\). Each graph edge \(\{u,v\}\) induces one synthetic action: hit probability 0 at \(u\), 1 at \(v\), 1/2 at all other transient states, with all remaining mass returning to the current transient state. The goal is absorbing. All actions are represented by symbolic edge labels. The candidate supplies one integer macrostate label in \(\{0,1,2,3\}\) for each of the \(n+1\) states, including the goal.

The evaluator requires the goal label to be different from every transient label. It computes the **optimal** macro-kernel error for the submitted partition using exact fractions:

\[
\epsilon(\pi)
=\frac12\max_{a,B}\left[\max_{s\in B}p_s^a-\min_{s\in B}p_s^a\right].
\]

A submitted partition passes if \(\epsilon(\pi)\le1/4\). Infeasible cases are recognized by a separate brute-force proper-3-coloring oracle, for small public development graphs only. The oracle returns either a constructive partition or \`None\`. A future language-model runner should score claimed impossibility against the frozen oracle separately from valid constructive assignments.

## Calibration and negative controls

- [xenobotbench/conflict_graph.py](../xenobotbench/conflict_graph.py) generates immutable cases, checks macrostate assignments under the exact one-step TV contract, and supplies a small independent graph-coloring oracle.
- [tests/test_conflict_graph.py](../tests/test_conflict_graph.py) exhaustively verifies every labelled graph on 4 vertices; it also checks a complete-graph failure, a cycle success, goal-readout violations, vertex relabelling invariance, and malformed assignments.
- The existing MOP-01 deterministic comparison is retained, making action-induced hidden distinctions measurable in both deterministic and stochastic settings.
- Under the public pilot, almost all 4-vertex graphs are 3-colorable; balanced held-out panels must deliberately include harder **non-3-colorable** examples and document their generation. Seeds are held by the evaluator until all models finish.
- A live model comparison would require pinned model revisions, identical token/tool budgets, held-out graph families, seed-clustered estimates, and separate scoring of abstentions and invalid answers. **No live model result is claimed here.**

The \`graph_case\` and \`score_partition\` functions are pure Python and make no network calls. This module is a *research component*, not a fifth scored track in the current CLI; integrating a new track requires revising its protocol and result schema.

## Reproduce

    python -m unittest discover -s tests -v

The dedicated \`Morphospace digital audit\` GitHub Actions workflow runs the full standard-library test suite on every related PR. These synthetic results give an exact comparator for future small-model search heuristics and establish no performance prediction about physical xenobots.
