# MOP-01: Morphospace observability as a digital finite-state quotient

**Scope:** 2026-11-04 mathematics and digital benchmark construction. These are **invented deterministic finite-state systems**. The note makes no xenobot or anthrobot engineering claim and contains no laboratory or organism-design procedure.

Michael Levin's interviews (supplied transcripts, November 2026) ask when cell collectives begin behaving as new individuals and how a newly embodied system obtains competencies. The **testable computational precursor** is simpler: when can we regard two substrate states as behaviorally indistinguishable under a declared intervention interface?

## 1. Experiment-relative identity

Let S be a finite state set, A a finite menu of purely digital interventions, F_a:S→S known deterministic transitions, and o:S→O an observation map. Let F_w denote composition for action word w, with F_empty=id. Define

    s ≡ t  iff  o(F_w(s))=o(F_w(t)) for every finite word w∈A*.  (1)

This equivalence is **interface-relative behavioral identity**: it depends on which interventions and readouts an evaluator permits.

**Proposition MOP-01/T1.** Relation (1) is the coarsest equivalence which (i) equates states only when their current observations agree and (ii) is preserved by every action F_a.

*Proof.* Equality of all observations is reflexive, symmetric and transitive. If s≡t then for any a and suffix w, o(F_w(F_a(s)))=o(F_w(F_a(t))), proving action stability. Conversely, any action-stable observation-respecting equivalence implies by induction on word length that equivalent states agree after every action word. Therefore it refines ≡. QED.

**Proposition MOP-01/T2 (finite termination and witness length).** Start from the partition by current observation. Repeatedly split blocks according to the vector of their successor-block IDs under every action. With n=|S|, this process stabilizes in at most n-1 strict refinements. At stabilization it equals (1). Two inequivalent states admit a distinguishing word of length at most n-1.

*Proof.* A strict refinement adds at least one block; there can be at most n blocks. Inductively, the partition after k refinements identifies states agreeing on all words of length ≤k. Stability gives equality for all lengths. Any split occurring at iteration k is witnessed by a word of length at most k. QED. This is classical finite Moore-machine partition refinement, applied here to morphology-inspired observability.

The minimum number of fixed-length labels for the resulting k distinct classes is ceil(log2(k)); this is a **cardinality** lower bound. It excludes the program needed to compute the quotient and the bytes needed to specify interface/actions.

## 2. Exact counterexample to single-snapshot identity

Let S={0,1,2,3}, observation o(0)=o(1)=0 and o(2)=o(3)=1. An action \`toggle\` maps 0→2, 1→1, 2→0, 3→3; an action \`restore\` maps 0→0, 1→0, 2→2, 3→2.

With only \`restore\`, the quotient has 2 classes. Add \`toggle\`: the quotient has 4 classes because states 0 and 1 have identical current readouts but diverge after one toggle, as do 2 and 3. The module and tests compute the quotients and the shortest distinguishing words.

**Consequence.** An apparent change in "number of individuals" from a behavioral quotient can result from changing the observer's interface alone. A scientific claim about an organism-level entity must freeze the observation and perturbation contract first.

## 3. A prospective morphospace benchmark track

An evaluation instance gives the agent:
- the public observation and a bounded menu of safe synthetic action probes;
- a hidden initial state and an exact digital transition oracle;
- a budget for probes, with strict tool receipts.

The task is to predict the quotient, give a shortest distinguishing sequence for a selected pair, or abstain when the selected actions cannot distinguish that pair. Scoring should distinguish hypothesis accuracy, valid tool receipts and overconfident unsupported claims.

**Blinded test:** construct hidden states from held-out transition families and expose identical budgets to all models. Track paired accuracy by seed, exact action counts, malformed outputs and all attempts. Preserve the repository's authority restrictions and source hashes.

**Controls:** action-menu ablation, observation-map coarsening, action-label permutation, unseen graph isomorphisms, shuffled probes, and deliberately indistinguishable pairs. Report both the true quotient under the chosen interface and the agent's estimate. Do not infer biological capability or model consciousness from a digital quotient.

## 4. Relationship to existing mathematics

- The exact deterministic quotient is a special finite instance of the interface-relative future-test idea in [EvalMath IRC-02](https://github.com/MoralityLabAI/EvalMath/blob/main/paper/interface_relative_compactification.md), but uses fully observed states and deterministic interventions.
- [Compactification-Theory IDQ-01](https://github.com/MoralityLabAI/Compactification-Theory/tree/research/ingression-quotients-20261104/research/ingression_dynamics_v1) gives an exact intervention-commutation theorem and a stochastic error bound.
- The optional next-generation benchmark should register a recovery goal and test whether abstract classes preserve intervention-conditioned reachability. That is a new experimental endpoint.

**Status:** T1/T2 have proofs above; finite examples are executable; no model run and no biological observation. Run: \`python -m unittest discover -s tests -p test_morphospace_quotient.py -v\`.
