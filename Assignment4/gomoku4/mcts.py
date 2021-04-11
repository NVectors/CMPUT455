#!/usr/bin/python3
"""
This function is loosely based on https://github.com/Rochester-NRT/RocAlphaGo/blob/develop/AlphaGo/mcts.py
"""
import os, sys
import numpy as np
import random
from board_util import GoBoardUtil, BLACK, WHITE, PASS, EMPTY
#from feature_moves import FeatureMoves
from gtp_connection import point_to_coord, format_point



PASS = "pass"

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

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move_gomoku(move, color)

def uct_val(node, child, exploration, max_flag):
    if child._n_visits == 0:
        return float("inf")
    if max_flag:
        return float(child._black_wins) / child._n_visits + exploration * np.sqrt(
            np.log(node._n_visits) / child._n_visits
        )
    else:
        return float(
            child._n_visits - child._black_wins
        ) / child._n_visits + exploration * np.sqrt(
            np.log(node._n_visits) / child._n_visits
        )


class TreeNode(object):
    """
    A node in the MCTS tree.
    """

    version = 0.22
    name = "MCTS Player"

    def __init__(self, parent):
        """
        parent is set when a node gets expanded
        """
        self._parent = parent
        self._children = {}  # a map from move to TreeNode
        self._n_visits = 0
        self._black_wins = 0
        self._expanded = False
        self._move = None

    def expand(self, board, color):
        """
        Expands tree by creating new children.
        """
        moves = board.get_empty_points()
        for move in moves:
            if move not in self._children:
                if board.is_legal_gomoku(move, color):
                    self._children[move] = TreeNode(self)
                    self._children[move]._move = move
        self._expanded = True

    def select(self, exploration, max_flag):
        """
        Select move among children that gives maximizes UCT. 
        If number of visits are zero for a node, value for that node is infinite, so definitely will get selected

        It uses: argmax(child_num_black_wins/child_num_vists + C * sqrt(2 * ln * Parent_num_vists/child_num_visits) )
        Returns:
        A tuple of (move, next_node)
        """
        return max(
            self._children.items(),
            key=lambda items: uct_val(self, items[1], exploration, max_flag),
        )

    def update(self, leaf_value):
        """
        Update node values from leaf evaluation.
        Arguments:
        leaf_value -- the value of subtree evaluation from the current player's perspective.
        
        Returns:
        None
        """
        self._black_wins += leaf_value
        self._n_visits += 1

    def update_recursive(self, leaf_value):
        """
        Like a call to update(), but applied recursively for all ancestors.

        Note: it is important that this happens from the root downward so that 'parent' visit
        counts are correct.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.update_recursive(leaf_value)
        self.update(leaf_value)

    def is_leaf(self):
        """
        Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def is_root(self):
        return self._parent is None


class MCTS(object):
    def __init__(self):
        self._root = TreeNode(None)
        self.toplay = BLACK

    def _playout(self, board, color):
        """
        Run a single playout from the root to the given depth, getting a value at the leaf and
        propagating it back through its parents. State is modified in-place, so a copy must be
        provided.

        Arguments:
        board -- a copy of the board.
        color -- color to play
        

        Returns:
        None
        """
        node = self._root
        # This will be True olny once for the root
        if not node._expanded:
            node.expand(board, color)
        while not node.is_leaf():
            # Greedily select next move.
            max_flag = color
            move, next_node = node.select(self.exploration, max_flag)
            if move != PASS:
                assert board.is_legal_gomoku(move, color)
            if move == PASS:
                move = None
            board.play_move_gomoku(move, color)
            color = GoBoardUtil.opponent(color)
            node = next_node
        assert node.is_leaf()
        if not node._expanded:
            node.expand(board, color)

        assert board.current_player == color
        leaf_value = self._evaluate_rollout(board, color)
        # Update value and visit count of nodes in this traversal.
        node.update_recursive(leaf_value)


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
    
    def _evaluate_rollout(self, board, color_to_play):
        """
        Use the rollout policy to play until the end of the game, returning +1 if the current
        player wins, -1 if the opponent wins, and 0 if it is a tie.
        
        winner = FeatureMoves.playGame(
            board,
            toplay,
            komi=self.komi,
            limit=self.limit,
            random_simulation=self.simulation_policy,
            use_pattern=self.use_pattern,
            check_selfatari=self.check_selfatari,
        )
        if winner == BLACK:
            return 1
        else:
            return 0

        """

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
        if res == BLACK:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == WHITE)
            return -1.0


    def get_move(
        self,
        board,
        toplay,
        #komi,
        limit = 100,
        #check_selfatari,
        #use_pattern,
        num_simulation = 100,
        exploration = 0.4,
        simulation_policy = 'random',
        #in_tree_knowledge,
    ):
        """
        Runs all playouts sequentially and returns the most visited move.
        """
        if self.toplay != toplay:
            sys.stderr.write("Dumping the subtree! \n")
            sys.stderr.flush()
            self._root = TreeNode(None)
        #self.komi = komi
        self.limit = limit
        #self.check_selfatari = check_selfatari
        #self.use_pattern = use_pattern
        self.toplay = toplay
        self.exploration = exploration
        self.playout_policy = simulation_policy
        #self.in_tree_knowledge = in_tree_knowledge
        for n in range(num_simulation):
            board_copy = board.copy()
            self._playout(board_copy, toplay)
        # choose a move that has the most visit
        moves_ls = [
            (move, node._n_visits) for move, node in self._root._children.items()
        ]
        if not moves_ls:
            return None
        moves_ls = sorted(moves_ls, key=lambda i: i[1], reverse=True)
        move = moves_ls[0]
        # self.print_stat(board, self._root, toplay)
        # self.good_print(board,self._root,self.toplay,10)
        if move[0] == PASS:
            return None
        assert board.is_legal_gomoku(move[0], toplay)
        return move[0]

    def update_with_move(self, last_move):
        """
        Step forward in the tree, keeping everything we already know about the subtree, assuming
        that get_move() has been called already. Siblings of the new root will be garbage-collected.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
        else:
            self._root = TreeNode(None)
        self._root._parent = None
        self.toplay = GoBoardUtil.opponent(self.toplay)

    def point_to_string(self, board_size, point):
        if point == None or point == PASS:
            return "Pass"
        x, y = point_to_coord(point, board_size)
        return format_point((x, y))

    def int_to_color(self, i):
        """convert number representing player color to the appropriate character """
        int_to_color = {BLACK: "b", WHITE: "w"}
        try:
            return int_to_color[i]
        except:
            raise ValueError("Provided integer value for color is invalid")

    def good_print(self, board, node, color, num_nodes):
        cboard = board.copy()
        sys.stderr.write("\nTaking a tour of selection policy in tree! \n\n")
        sys.stderr.write(str(cboard.get_twoD_board()))
        while not node.is_leaf():
            if node._move != None:
                pointString = self.point_to_string(board.size, node._move)
            else:
                pointString = "Root"
            sys.stderr.write(
                "\nMove {}: {} children, {} visits\n".format(
                    pointString, len(node._children), node._n_visits
                )
            )
            moves_ls = []
            max_flag = color == BLACK
            for move, child in node._children.items():
                uctval = uct_val(node, child, self.exploration, max_flag)
                moves_ls.append((move, uctval, child))
            moves_ls = sorted(moves_ls, key=lambda i: i[1], reverse=True)

            if moves_ls:
                sys.stderr.write(
                    "\nPrinting {} of {} children with highest UCT value \n\n".format(
                        num_nodes, pointString
                    )
                )
                sys.stderr.flush()
                for i in range(num_nodes):
                    move = moves_ls[i][0]
                    child_val = moves_ls[i][1]
                    child_node = moves_ls[i][2]
                    if move != PASS:
                        sys.stderr.write(
                            "\nChild point:{} ;UCT Value {}; Number of visits: {}; Number of Black wins: {}\n".format(
                                self.point_to_string(cboard.size, move),
                                child_val,
                                child_node._n_visits,
                                child_node._black_wins,
                            )
                        )
                        sys.stderr.flush()
                    else:
                        sys.stderr.write(
                            "\nChild {}: value {}, {} visits, {} Black wins\n"
                            .format(
                                move,
                                child_val,
                                child_node._n_visits,
                                child_node._black_wins
                            )
                        )
            # Greedily select next move.
            max_flag = color == BLACK
            move, next_node = node.select(self.exploration, max_flag)
            if move == PASS:
                move = None
            assert cboard.is_legal(move, color)
            pointString = self.point_to_string(cboard.size, move)
            cboard.play_move(move, color)
            sys.stderr.write(
                "\nBoard in simulation after chosing child {} in tree. \n".format(
                    pointString
                )
            )
            sys.stderr.write(str(cboard.get_twoD_board()))
            sys.stderr.flush()
            color = GoBoardUtil.opponent(color)
            node = next_node
        assert node.is_leaf()
        cboard.current_player = color
        leaf_value = self._evaluate_rollout(cboard, color)
        sys.stderr.write(
            "\nWinner of simulation (Black = 0): {}\n".format(leaf_value)
        )
        sys.stderr.flush()

    def print_stat(self, board, root, color):
        s_color = self.int_to_color(color)
        sys.stderr.write("Number of children: {}\n"
                         .format(len(root._children)))
        sys.stderr.write("Number of root visits: {}\n"
                         .format(root._n_visits))
        sys.stderr.flush()
        stats = []
        for move, node in root._children.items():
            if color == BLACK:
                wins = node._black_wins
            else:
                wins = node._n_visits - node._black_wins
            visits = node._n_visits
            if visits:
                win_rate = round(float(wins) / visits, 2)
            else:
                win_rate = 0
            if move == PASS:
                move = None
            pointString = self.point_to_string(board.size, move)
            stats.append((pointString, win_rate, wins, visits))
        sys.stderr.write(
            "Statistics: {} \n".format(sorted(stats, key=lambda i: i[3], reverse=True))
        )
        sys.stderr.flush()
