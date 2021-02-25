#!/usr/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from board import GoBoard
from endgamesolver import GomokuSolver
import signal
import numpy as np

class TimeoutException(Exception):
    pass


class Gomoku():
    def __init__(self):
        """
        Gomoku player that selects moves randomly from the set of legal moves.
        Passes/resigns only at the end of the game.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "GomokuAssignment2"
        self.version = 1.0

    def get_move(self, board, color):
        return GoBoardUtil.generate_random_move(board, color)


def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    Solver = GomokuSolver()
    con = GtpConnection(Gomoku(), board, Solver)
    con.start_connection()


if __name__ == "__main__":
    run()
