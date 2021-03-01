import signal
from board_util import GoBoardUtil
from board import GoBoard
import numpy as np
import random
from sys import stdin, stdout, stderr


class ZobristHasher:

    def __init__(self, boardSize):
        self.zobristArray = []
        self.boardIndices = boardSize*boardSize

        for _ in range(self.boardIndices):
            self.zobristArray.append([random.getrandbits(64) for _ in range(3)])

    def hash(self, board):
        hashCode = self.zobristArray[0][board[0]]
        for i in range(1,self.boardIndices):
            hashCode = hashCode ^ self.zobristArray[i][board[i]]
        
        return hashCode


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
        raise TimeoutError

    def point_to_coord(self, point, boardsize):
        """
        Transform point given as board array index 
        to (row, col) coordinate representation.
        Special case: PASS is not transformed
        """
        NS = boardsize + 1
        return divmod(point, NS)

    def solve(self, board, time, tt, hasher):
        # Set alarm
        signal.alarm(time)
        boardCopy = board.copy()
        ttBlack, ttWhite = tt

        try:
            
            score, move = self.minimax(boardCopy, -1 * self.infinity, self.infinity, ttBlack, ttWhite, hasher) # Get the score and best move
    
            if(score == 0):
                return "draw", move
            elif(score > 0):

                win = board.current_player
                return self.int_to_color[win], move
            else:
                win = GoBoardUtil.opponent(board.current_player)
                return self.int_to_color[win], None

        except TimeoutError:
            return "unknown", None

        finally:
            signal.alarm(0)

    def storeResult(self, result, tt, hashCode):
        tt.store(hashCode, result)


    def minimax(self, board, alpha, beta, ttBlack, ttWhite, hasher):

        if(board.current_player == 1):
            tt = ttBlack
        else:
            tt = ttWhite

        size  = len(board.board)
        board1d = []

        for i in range(size):
            if board.board[i] != 3:
                board1d.append(board.board[i])
    
        hashCode = hasher.hash(board1d)
   

        result = tt.lookup(hashCode)

        if result:
            return result
        
        outcome =  board.detect_five_in_a_row()

        # Check if terminal board
        if (board.get_empty_points().size == 0 or outcome):
            result = self.evaluate_score_endgame(board, outcome), None
            self.storeResult(result, tt, hashCode)
            return result
            

        # Order moves by heuristic
        moves = board.get_empty_points()
        self.board = board

        #TODO: Right now timeouts while calculating best move using Heuristic
        moves = sorted(moves, key = self.evaluate_move_heuristic, reverse = True)
        

        #Choose best move
        best = moves[0]

        for m in moves:

            board.play_move(m, board.current_player)
            if(self.check_double_threat(board, m)):
                result = self.infinity, m
                board.undo_move(m)
                self.storeResult(result, tt, hashCode)
                return result
            else:
                board.undo_move(m)
            

        for m in moves:
            board.play_move(m, board.current_player)
            value, _ = self.minimax(board, -beta, -alpha, ttBlack, ttWhite, hasher)
            value = -value
            if value > alpha:
                alpha = value
                best = m
            board.undo_move(m)
            if value >= beta: 
                result = beta, m
                self.storeResult(result, tt, hashCode) 
                return result
            

        result = alpha, best
        self.storeResult(result, tt, hashCode)
        return result

    def check_double_threat(self, board, m):
        mr, mc= self.point_to_coord(m, board.size)
        mr = mr -1
        mc = mc -1
        board2d = GoBoardUtil.get_twoD_board(board)
        thrtCnt = 0


        try:
            if(mr + 4 < board.size and board2d[mr + 1, mc] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr+2, mc] and board2d[mr+3, mc] == 0  and board2d[mr+4, mc] == 0):
                #stdout.write("yo\n")
                thrtCnt+=1
        except IndexError:
            pass
        try:
            if(mr - 4 >= 0 and board2d[mr - 1, mc] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr-2, mc] and board2d[mr-3, mc] == 0  and board2d[mr-4, mc] == 0):
               # stdout.write("yo2\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mc + 4 < board.size and board2d[mr , mc + 1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr, mc+2] and board2d[mr, mc+3] == 0 and board2d[mr, mc+4] == 0):
                #stdout.write("yo3\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mc - 4 >= 0 and board2d[mr, mc-1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr, mc-2] and board2d[mr, mc-3] == 0 and board2d[mr, mc-4] == 0):
                #stdout.write("yo4\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mc - 4 >= 0 and mr - 4 >= 0 and board2d[mr -1, mc-1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr -2, mc-2] and board2d[mr-3, mc-3] == 0 and board2d[mr-4, mc-4] == 0):
                #stdout.write("yo5\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mr + 4 < board.size and mc + 4 < board.size and board2d[mr+1, mc+1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr+2, mc+2] and board2d[mr+3, mc+3] == 0 and board2d[mr+4, mc+4] == 0):
                #stdout.write("yo6\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mr + 4 < board.size and mc - 4 >= 0  and board2d[mr+1, mc-1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr+2, mc-2] and board2d[mr+3, mc-3] == 0) and board2d[mr+4, mc-4] == 0:
                #stdout.write("yo7\n")
                thrtCnt+=1
        except IndexError:
            pass

        try:

            if(mc + 4 < board.size and mr - 4 >= 0 and board2d[mr-1, mc+1] == board2d[mr, mc] and board2d[mr, mc] == board2d[mr-2, mc+2] and board2d[mr-3, mc+3] == 0 and board2d[mr-4, mc+4] == 0):
                #stdout.write("yo8\n")
                thrtCnt+=1
        except IndexError:
            pass
        
        #stdout.write(str(thrtCnt) + "\n")
        if(thrtCnt >=2):
            #stdout.write(str(mr) + "\n" +str(mc) +"\n")
            return True
        else:
            return False

    def evaluate_score_endgame(self, board, outcome):
        if(outcome):
            return self.infinity * -1
        else:
            return 0
    
    def evaluate_move_heuristic(self, move):
        self.board.play_move(move, self.board.current_player)
        score = -self.evaluate_state_heuristic()
        self.board.undo_move(move)
        return score
    
    def evaluate_state_heuristic(self):
        outcome = self.board.detect_five_in_a_row()
        if(outcome != 0):
            return -10000
   
        score = 0
        lines = self.board.rows + self.board.cols + self.board.diags

        for line in lines:
            for i in range(len(line) - 5):
                line_score = 0
                myCount, oppCount = self.count_stones(line[i:i+5])
                line_score = self.weights[myCount] - self.weights[oppCount]
                if myCount >= 1 and oppCount >= 1:
                    line_score = 0
                score += line_score

        return score
            

    def count_stones(self, line):

        countBlack = 0
        countWhite = 0

        for stone in line:
            stoneColor = self.board.board[stone]

            if stoneColor == 1:
                countBlack += 1
            elif stoneColor == 2:
                countWhite += 1

        if(self.board.current_player == 1):
            myCount = countBlack
            oppCount = countWhite
        else:
            myCount = countWhite
            oppCount = countBlack

        return myCount, oppCount