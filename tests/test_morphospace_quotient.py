import unittest
from xenobotbench.quotient_probe import demonstration, partition, distinguishing_word

class QuotientProbeTests(unittest.TestCase):
    def setUp(self):
        self.states, self.obs, self.maps = demonstration()

    def test_action_menu_refines_classes(self):
        low = partition(self.states, self.obs, self.maps, ("restore",))
        high = partition(self.states, self.obs, self.maps, ("restore", "toggle"))
        self.assertEqual(len(set(low.values())), 2)
        self.assertEqual(len(set(high.values())), 4)
        self.assertEqual(low[0], low[1])
        self.assertNotEqual(high[0], high[1])

    def test_witness_is_exact(self):
        word = distinguishing_word(0, 1, self.obs, self.maps, ("restore", "toggle"))
        self.assertEqual(word, ("toggle",))
        self.assertIsNone(distinguishing_word(0, 1, self.obs, self.maps, ("restore",)))

    def test_pairwise_witness_agrees_with_quotient(self):
        for actions in ((), ("restore",), ("restore", "toggle")):
            classes = partition(self.states, self.obs, self.maps, actions)
            for x in self.states:
                for y in self.states:
                    witness = distinguishing_word(x, y, self.obs, self.maps, actions)
                    self.assertEqual(witness is None, classes[x] == classes[y])
                    if witness is not None:
                        self.assertLessEqual(len(witness), len(self.states) - 1)
                        a, b = x, y
                        for step in witness:
                            a, b = self.maps[step][a], self.maps[step][b]
                        self.assertNotEqual(self.obs[a], self.obs[b])

if __name__ == "__main__":
    unittest.main()
