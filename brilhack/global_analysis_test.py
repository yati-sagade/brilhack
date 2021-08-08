import unittest
from .basic_blocks import BBProgram
from .global_analysis import dominators, dominator_tree


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
