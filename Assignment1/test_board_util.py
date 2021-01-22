#!/usr/local/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

import unittest
from board_util import BLACK, GoBoardUtil
from board import GoBoard


class GoBoardUtilTestCase(unittest.TestCase):
    """Tests for board_util.py"""

    def test_size_2_legal_moves(self):
        size = 2
        goboard = GoBoard(size)
        moves = GoBoardUtil.generate_legal_moves(goboard, BLACK)
        self.assertEqual(
            moves,
            [goboard.pt(1, 1), goboard.pt(1, 2), goboard.pt(2, 1), goboard.pt(2, 2)],
        )


"""Main"""
if __name__ == "__main__":
    unittest.main()
