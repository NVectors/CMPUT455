import signal
from board_util import GoBoardUtil
from board import GoBoard
import numpy as np


class GomokuSolver:
    def __init__(self):
        self.int_to_color = {1:"b", 2:"w"}
        self.infinity = 10000
        self.weights = [0, 2, 8, 16, 64, 10000]
        signal.signal(signal.SIGALRM, self.handler)

    def handler(self, signum, frame):
        raise Exception

    def solve(self, board, time):
        # Set alarm
        signal.alarm(time)
        boardCopy = board.copy()
        try:
            score, move = self.minimax(boardCopy, -1 * self.infinity, self.infinity) # Get the score and best move

            if(score == 0):
                return "draw", move
            elif(score > 0):
                win = board.current_player
                return self.int_to_color[win], move
            else:
                win = GoBoardUtil.opponent(board.current_player)
                return self.int_to_color[win], None

        except Exception:
            return "unknown", None

        finally:
            signal.alarm(0)

    def minimax(self, state, alpha, beta):
        outcome =  state.detect_five_in_a_row()

        # Check if terminal state
        if (state.get_empty_points().size == 0 or outcome):
            return self.evaluate_score_endgame(state, outcome), None

        # Order moves by heuristic
        moves = state.get_empty_points()
        self.state = state

        #TODO: Right now timeouts while calculating best move using Heuristic
        #moves = sorted(moves, key = self.evaluate_move_heuristic, reverse = True)

        # Choose best move
        best = moves[0]

        for m in moves:
            state.play_move(m, state.current_player)
            value, _ = self.minimax(state, -beta, -alpha)
            value = -value
            if value > alpha:
                alpha = value
                best = m
            state.undo_move(m)
            if value >= beta:
                result = beta, m
                return result

        result = alpha, best
        return result

    def evaluate_score_endgame(self, state, outcome):
        if(outcome):
            return self.infinity * -1
        else:
            return 0
    
    def evaluate_move_heuristic(self, move):
        self.state.play_move(m, self.state.current_player)
        score = -self.evaluate_state_heuristic()
        self.state.undo_move(m)
        return score
    
    def evaluate_state_heuristic(self):
        score = 0
        line = self.rows + self.cols + self.diags

        for line in lines:
            for i in range(len(line) - 5):
                line_score = 0
                myCount, oppCount, countEmpty = count_stones(line[i:i+5])
                line_score = self.weights[myCount] - self.weights[oppCount]
                score += line_score

        return score
            

    def count_stones(self, line):

        countBlack = 0
        countWhite = 0
        countEmpty = 0

        for stone in line:
            stoneColor = self.state.board[stone]

            if stoneColor == 1:
                countBlack += 1
            elif stoneColor == 2:
                countWhite += 1
            else:
                countEmpty += 1

        if(self.state.current_player == 1):
            myCount = countBlack
            oppCount = countWhite
        else:
            myCount = countWhite
            oppCount = countBlack

        return myCount, oppCount, countEmpty