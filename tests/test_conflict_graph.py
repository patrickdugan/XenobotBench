import itertools
import unittest
from xenobotbench.conflict_graph import (
    graph_case, score_partition, brute_three_color_oracle, all_four_vertex_cases,
)


class ConflictGraphTests(unittest.TestCase):
    def test_all_64_four_vertex_cases(self):
        cases = list(all_four_vertex_cases())
        self.assertEqual(len(cases), 64)
        for case in cases:
            witness = brute_three_color_oracle(case)
            all_assignments = itertools.product(range(4), repeat=case["vertices"]+1)
            accepted = any(score_partition(case, a)["accepted"]
                           for a in all_assignments)
            self.assertEqual(accepted, witness is not None)

    def test_complete_four_is_rejected(self):
        case = graph_case(4, itertools.combinations(range(4), 2))
        self.assertIsNone(brute_three_color_oracle(case))

    def test_cycle_four_is_accepted(self):
        case = graph_case(4, ((0, 1), (1, 2), (2, 3), (3, 0)))
        answer = brute_three_color_oracle(case)
        self.assertIsNotNone(answer)
        self.assertTrue(score_partition(case, answer)["accepted"])

    def test_goal_must_stay_distinct(self):
        case = graph_case(2, ((0, 1),))
        failure = score_partition(case, (0, 1, 0))
        self.assertFalse(failure["accepted"])
        self.assertEqual(failure["reason"], "goal readout is not exact")

    def test_out_of_budget_and_boolean_labels(self):
        case = graph_case(2, ())
        for labels in ((0, 1), (0, 1, 4), (True, 1, 3)):
            self.assertFalse(score_partition(case, labels)["accepted"])

    def test_vertex_permutation_invariance(self):
        case = graph_case(4, ((0, 1), (1, 2), (2, 3), (3, 0)))
        perm = (3, 1, 0, 2)
        mapped = graph_case(4, ((perm[u], perm[v]) for u, v in case["edges"]))
        witness = brute_three_color_oracle(case)
        labels = [None] * 5
        for old in range(4):
            labels[perm[old]] = witness[old]
        labels[-1] = witness[-1]
        self.assertEqual(score_partition(case, witness)["tv_defect"],
                         score_partition(mapped, labels)["tv_defect"])

    def test_deduplicate_and_bad_graph(self):
        case = graph_case(3, ((1, 0), (0, 1)))
        self.assertEqual(case["edges"], ((0, 1),))
        for n, edges in ((0, ()), (3, ((0, 0),)), (3, ((2, 3),))):
            with self.assertRaises(ValueError):
                graph_case(n, edges)


if __name__ == "__main__":
    unittest.main()
