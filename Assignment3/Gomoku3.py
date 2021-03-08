#!/usr/bin/python3
# /usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from board import GoBoard

class Gomoku3(object):
    def __init__(self):
        self.numSimulations = 10 # 10 simulations for each legal move

    def name(self):
        return "Simulation Player ({0} sim.)".format(self.numSimulations)

    def genmove(self):
        assert not self.endOfGame()    #TO DO
        moves = GoBoardUtil.generate_legal_moves(self.board, self.current_player)
        numMoves = len(moves)
        score = [0] * numMoves
        for i in range(numMoves):
            move = moves[i]
            score[i] = self.simulate(self.board, move)
        #print(score)
        bestIndex = score.index(max(score))
        best = moves[bestIndex]
        #print("Best move:", best, "score", score[best])
        assert best in GoBoardUtil.generate_legal_moves(self.board, self.current_player)
        return best

    def simulate(self, state, move):
        stats = [0] * 3
        state.play(move)
        moveNr = state.moveNumber()
        for _ in range(self.numSimulations):
            winner, _ = state.simulate()
            stats[winner] += 1
            state.resetToMoveNumber(moveNr)
        assert sum(stats) == self.numSimulations
        assert moveNr == state.moveNumber()
        state.undoMove()
        eval = (stats[BLACK] + 0.5 * stats[EMPTY]) / self.numSimulations
        if state.toPlay == WHITE:
            eval = 1 - eval
        return eval

Gomoku3()