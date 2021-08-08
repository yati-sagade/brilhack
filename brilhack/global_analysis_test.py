import unittest
from .basic_blocks import BBProgram
from .global_analysis import dominators, dominator_tree, extract_natural_loops, is_cfg_reducible


class GlobalAnalysisTest(unittest.TestCase):
    def test_dominators(self):
        cfg = [[1], [5, 2], [3, 4], [4], [1], [6], []]
        self.assertEqual(dominators(cfg), [
            {0},
            {0, 1},
            {0, 1, 2},
            {0, 1, 2, 3},
            {0, 1, 2, 4},
            {0, 1, 5},
            {0, 1, 5, 6},
        ])

    def test_dominator_tree(self):
        cfg = [[1], [5, 2], [3, 4], [4], [1], [6], []]
        self.assertEqual(dominator_tree(cfg), [
            {1},
            {5, 2},
            {3, 4},
            set(),
            set(),
            {6},
            set(),
        ])

    def test_extract_natural_loops(self):
        self.assertEqual(
            extract_natural_loops(
                cfg=[[1], [5, 2], [3, 4], [4], [1], [6], []]), [{1, 2, 3, 4}])

        # This CFG is not reducible, since the only loop it contains is not
        # a natural loop (node 3 forms a back-edge with header node 1, but
        # there is an external 2->3 edge that makes the loop not natural).
        self.assertEqual(extract_natural_loops(cfg=[[1, 2], [3], [3], [1]]),
                         [])

    def test_is_cfg_reducible(self):
        self.assertTrue(
            is_cfg_reducible(cfg=[[1], [5, 2], [3, 4], [4], [1], [6], []]))
        self.assertFalse(is_cfg_reducible(cfg=[[1, 2], [2], [1]]))
        self.assertFalse(is_cfg_reducible(cfg=[[1, 2], [3], [3], [1]]))
