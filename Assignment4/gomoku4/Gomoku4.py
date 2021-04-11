#!/usr/bin/env python
#/usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY
from simple_board import SimpleGoBoard

import random
import numpy as np
from mcts import MCTS

"""

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move_gomoku(move, color)

def game_result(board):
    game_end, winner = board.check_game_end_gomoku()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if game_end:
        #return 1 if winner == board.current_player else -1
        return winner
    if board_full:
        return 'draw'
    return None
"""

class GomokuSimulationPlayer(object):
    """
    For each move do `n_simualtions_per_move` playouts,
    then select the one with best win-rate.
    playout could be either random or rule_based (i.e., uses pre-defined patterns) 
    """
    def __init__(self, n_simualtions_per_move=10, playout_policy='random', board_size=7):
        assert(playout_policy in ['random', 'rule_based'])
        self.n_simualtions_per_move=n_simualtions_per_move
        self.board_size=board_size
        self.playout_policy=playout_policy

        #NOTE: pattern has preference, later pattern is ignored if an earlier pattern is found
        self.pattern_list=['Win', 'BlockWin', 'OpenFour', 'BlockOpenFour', 'Random']

        self.name="Gomoku4"
        self.version = 3.0
        self.best_move=None
        self.MCTS = MCTS()
        self.parent = None
    
    def set_playout_policy(self, playout_policy='random'):
        assert(playout_policy in ['random', 'rule_based'])
        self.playout_policy=playout_policy

    """

    def _random_moves(self, board, color_to_play):
        return GoBoardUtil.generate_legal_moves_gomoku(board)
    
    def policy_moves(self, board, color_to_play):
        if(self.playout_policy=='random'):
            return "Random", self._random_moves(board, color_to_play)
        else:
            assert(self.playout_policy=='rule_based')
            assert(isinstance(board, SimpleGoBoard))
            ret=board.get_pattern_moves()
            if ret is None:
                return "Random", self._random_moves(board, color_to_play)
            movetype_id, moves=ret
            return self.pattern_list[movetype_id], moves
    
    def _do_playout(self, board, color_to_play):
        res=game_result(board)
        simulation_moves=[]
        while(res is None):
            _ , candidate_moves = self.policy_moves(board, board.current_player)
            playout_move=random.choice(candidate_moves)
            play_move(board, playout_move, board.current_player)
            simulation_moves.append(playout_move)
            res=game_result(board)
        for m in simulation_moves[::-1]:
            undo(board, m)
        if res == color_to_play:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == GoBoardUtil.opponent(color_to_play))
            return -1.0
"""
    def reset(self):
        self.MCTS = MCTS()

    def update(self, move):
        self.parent = self.MCTS._root
        self.MCTS.update_with_move(move)

    def get_move(self, board, toplay):
        move = self.MCTS.get_move(
            board, 
            toplay,
            #komi=self.komi,
            limit=100,
            #check_selfatari=self.check_selfatari,
            #use_pattern=self.use_pattern,
            num_simulation=100,
            exploration=0.4,
            simulation_policy='random',
            #in_tree_knowledge=self.in_tree_knowledge,
        )
        self.update(move)
        return move

    def get_node_depth(self, root):
        MAX_DEPTH = 100
        nodesAtDepth = [0] * MAX_DEPTH
        count_at_depth(root, 0, nodesAtDepth)
        prev_nodes = 1
        return nodesAtDepth

    def get_properties(self):
        return dict(version=self.version, name=self.__class__.__name__,)

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(GomokuSimulationPlayer(), board)
    con.start_connection()

if __name__=='__main__':
    run()
