import signal
from board_util import GoBoardUtil
from board import GoBoard
import numpy as np

class TranspositionTable(object):
# Written by Martin Mueller
# Table is stored in a dictionary, with board code as key, 
# and minimax score as the value

    # Empty dictionary
    def __init__(self):
        self.table = {}

    # Used to print the whole table with print(tt)
    def __repr__(self):
        return self.table.__repr__()
        
    def store(self, code, score):
        self.table[code] = score
    
    # Python dictionary returns 'None' if key not found by get()
    def lookup(self, code):
        return self.table.get(code)

class GomokuSolver:
    def __init__(self):
        self.int_to_color = {1:"b", 2:"w"}
        self.infinity = 10000
        self.weights = [0, 2, 8, 16, 64, 10000]
        signal.signal(signal.SIGALRM, self.handler)

    def handler(self, signum, frame):
        raise Exception

    def call_search(self, board):
        tt = TranspositionTable() # use separate table for each color
        return self.minimax(board, -1 * self.infinity, self.infinity, tt) # Get the score and best move


    def solve(self, board, time):
        # Set alarm
        signal.alarm(time)
        boardCopy = board.copy()
        try:
            #score, move = self.minimax(boardCopy, -1 * self.infinity, self.infinity) # Get the score and best move
            score, move = self.call_search(boardCopy)
            
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

    def storeResult(self, score, win_move):
        #tt.store(state.code(), result)
        result = score, win_move
        return result

    def minimax(self, board, alpha, beta, tt):
        outcome =  board.detect_five_in_a_row()

        # Check if terminal board
        if (board.get_empty_points().size == 0 or outcome):
            #return self.evaluate_score_endgame(board, outcome), None
            return self.storeResult(self.evaluate_score_endgame(board,outcome), None)

        # Order moves by heuristic
        moves = board.get_empty_points()
        self.board = board

        #TODO: Right now timeouts while calculating best move using Heuristic
        #moves = sorted(moves, key = self.evaluate_move_heuristic, reverse = True)

        # Choose best move
        best = moves[0]

        for m in moves:
            board.play_move(m, board.current_player)
            value, _ = self.minimax(board, -beta, -alpha, tt)
            value = -value
            if value > alpha:
                alpha = value
                best = m
            board.undo_move(m)
            if value >= beta:
                #result = beta, m
                #return result
                return self.storeResult(beta, m)

        #result = alpha, best
        #return result
        return self.storeResult(alpha, best)

    def evaluate_score_endgame(self, board, outcome):
        if(outcome):
            return self.infinity * -1
        else:
            return 0
    
    def evaluate_move_heuristic(self, move):
        self.board.play_move(m, self.board.current_player)
        score = -self.evaluate_state_heuristic()
        self.board.undo_move(m)
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
            stoneColor = self.board.board[stone]

            if stoneColor == 1:
                countBlack += 1
            elif stoneColor == 2:
                countWhite += 1
            else:
                countEmpty += 1

        if(self.board.current_player == 1):
            myCount = countBlack
            oppCount = countWhite
        else:
            myCount = countWhite
            oppCount = countBlack

        return myCount, oppCount, countEmpty