"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Parts of this code were originally based on the gtp module 
in the Deep-Go project by Isaac Henrion and Amos Storkey 
at the University of Edinburgh.
"""
import traceback
from sys import stdin, stdout, stderr

from numpy.lib.function_base import copy
from board_util import (
    GoBoardUtil,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    PASS,
    MAXSIZE,
    coord_to_point,
)
import numpy as np
import re
import random

POLICY = "random"


class GtpConnection:
    def __init__(self, go_engine, board, debug_mode=False):
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board: 
            Represents the current board state.
        """
        self.numSimulations = 10    # 10 sims required by the specs

        self._debug_mode = debug_mode
        self.go_engine = go_engine
        self.board = board
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
            "policy": self.policy_cmd,              # Policy type: random or rulebased
            # Set of moves considered by the sim policy
            "policy_moves": self.policy_moves_cmd
        }

        # used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, "Usage: boardsize INT"),
            "komi": (1, "Usage: komi FLOAT"),
            "known_command": (1, "Usage: known_command CMD_NAME"),
            "genmove": (1, "Usage: genmove {w,b}"),
            "play": (2, "Usage: play {b,w} MOVE"),
            "legal_moves": (1, "Usage: legal_moves {w,b}"),
        }

    def write(self, data):
        stdout.write(data)

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection. 
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(" \r\t")) == 0:
            return
        if command[0] == "#":
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]
        args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".format(
                    traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error("Unknown command")
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write("? {}\n\n".format(error_msg))
        stdout.flush()

    def respond(self, response=""):
        """ Send response to stdout """
        stdout.write("= {}\n\n".format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond("2")

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the  Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        # global POLICY
        self.reset(int(args[0]))
        # POLICY = "random"
        self.respond()

    def showboard_cmd(self, args):
        self.respond("\n" + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(" ".join(list(self.commands.keys())))

    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = " ".join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def play_cmd(self, args):
        """
        play a move args[1] for given color args[0] in {'b','w'}
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            color = color_to_int(board_color)
            if args[1].lower() == "pass":
                self.board.play_move(PASS, color)
                self.board.current_player = GoBoardUtil.opponent(color)
                self.respond()
                return
            coord = move_to_coord(args[1], self.board.size)
            if coord:
                move = coord_to_point(coord[0], coord[1], self.board.size)
            else:
                self.respond("unknown: {}".format(args[1]))
                return
            if not self.board.play_move(move, color):
                self.respond(
                    "illegal move: \"{}\" occupied".format(args[1].lower()))
                return
            else:
                self.debug_msg(
                    "Move: {}\nBoard:\n{}\n".format(board_move, self.board2d())
                )
            self.respond()
        except Exception as e:
            self.respond("illegal move: {}".format(str(e).replace('\'', '')))

    """ Assignment 3 Code inside Class starts here """

    def genmove_cmd(self, args):
        """
        Generate a move for the color args[0] in {'b', 'w'}, for the game of gomoku.
        """

        board_color = args[0].lower()
        color = color_to_int(board_color)

        result = self.board.detect_five_in_a_row()
        if result == GoBoardUtil.opponent(self.board.current_player):
            self.respond("resign")
            return
        if self.board.get_empty_points().size == 0:
            self.respond("pass")
            return

        moves = self.board.get_empty_points()
        if (POLICY == "random"):
            best_move = None
            best_ratio = 0

            for move in moves:
                win = 0  # Default value before simulating each move
                if best_move == None:
                    best_move = move
                # Num of simulations required for each move (Required: 10)
                for i in range(self.numSimulations):
                    if random_sim(self.board.copy(), color, color):
                        win += 1
                # Update after each move if it better than prev. move
                if (win/10) > best_ratio:
                    best_move = move
                    best_ratio = (win/10)

        elif (POLICY == "rule_based"):
            # TO-DO

            best_move = self.rules_sim(self.board, color)

        if best_move == PASS:
            self.respond("pass")
            return
        #move = self.go_engine.get_move(self.board, color)
        move_coord = point_to_coord(best_move, self.board.size)
        move_as_string = format_point(move_coord)
        if self.board.is_legal(best_move, color):
            self.board.play_move(best_move, color)
            self.respond(move_as_string.upper())
        else:
            self.respond("Illegal move: {}".format(move_as_string.upper()))

    def policy_cmd(self, args):
        if args[0] != "random" and args[0] != "rule_based":
            self.respond("Unknown Policy")
        else:
            global POLICY
            POLICY = args[0]
            self.respond("Policy set to " + POLICY)

    def policy_moves_cmd(self, args):
        """ Assignment 3 Code inside Class ends here """

        #print(POLICY)
        color = self.board.current_player
        outputString = ""
        moves = self.board.get_empty_points()
        moveStringList = []
        scoreDict = {5: [], 4:[], 3:[], 2:[], 1:[]}
        labelList = ["Random", "BlockOpenFour", "OpenFour", "BlockWin" , "Win"]
        varout = 0

        if (POLICY == "random"):
            outputString += "Random"
            for move in moves:
                move_coord = point_to_coord(move, self.board.size)
                move_as_string = format_point(move_coord)
                moveStringList.append(move_as_string)
            
            moveStringList.sort()

            for m in moveStringList:
                outputString += " " + m

        elif (POLICY == "rule_based"):
            for move in moves:
                move_coord = point_to_coord(move, self.board.size)
                move_as_string = format_point(move_coord)
                score = self.checkMove(self.board, move, color)
                scoreDict[score].append(move_as_string.upper())

            if(len(scoreDict[5]) >0):
                varout = 5
            elif(len(scoreDict[4]) >0):
                varout = 4
            elif(len(scoreDict[3]) >0):
                varout = 3
            elif(len(scoreDict[2]) >0):
                varout = 2
            elif(len(scoreDict[1]) >0):
                varout = 1

            
            if(varout != 0):
                scoreDict[varout].sort()
                outputString = labelList[varout - 1]
                for m in scoreDict[varout]:
                    outputString += " " + m


        if(len(moveStringList) == 0 and varout == 0):
            outputString = ""
        self.respond(outputString)

    def gogui_rules_game_id_cmd(self, args):
        self.respond("Gomoku")

    def gogui_rules_board_size_cmd(self, args):
        self.respond(str(self.board.size))

    def gogui_rules_legal_moves_cmd(self, args):
        if self.board.detect_five_in_a_row() != EMPTY:
            self.respond("")
            return
        empty = self.board.get_empty_points()
        output = []
        for move in empty:
            move_coord = point_to_coord(move, self.board.size)
            output.append(format_point(move_coord))
        output.sort()
        output_str = ""
        for i in output:
            output_str = output_str + i + " "
        self.respond(output_str.lower())
        return

    def gogui_rules_side_to_move_cmd(self, args):
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args):
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                #str += '.'
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)

    def gogui_rules_final_result_cmd(self, args):
        if self.board.get_empty_points().size == 0:
            self.respond("draw")
            return
        result = self.board.detect_five_in_a_row()
        if result == BLACK:
            self.respond("black")
        elif result == WHITE:
            self.respond("white")
        else:
            self.respond("unknown")

    def gogui_analyze_cmd(self, args):
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )

    def rules_sim(self, board, cur_color):
        emptyPoints = board.get_empty_points()

        if (emptyPoints.size == 0):
            return None

        MoveWins = []

        bestRuleMoves = self.best_rule_moves(board, cur_color)

        for move, moveScore in bestRuleMoves:
            winSimulation = self.simulate_move(board, move, cur_color)
            MoveWins.append(winSimulation)

        return bestRuleMoves[np.argmax(MoveWins)][0]


    def simulate_move(self, board, move, color):
        totalWins = 0

        for i in range(self.numSimulations):
            currentBoard = board.copy()

            currentBoard.play_move(move, color)
            opp = GoBoardUtil.opponent(color)

            winner = EMPTY
            numPasses = 0

            while currentBoard.get_empty_points().size != 0:
                currColor = currentBoard.current_player
                bestMoves = self.best_rule_moves(currentBoard, currColor)

                move, moveScore = random.choice(bestMoves)

                if moveScore == 5:
                    winner = currColor

                # If color didnt win then play random move
                currentBoard.play_move(move, currColor)

                if move == PASS:
                    numPasses += 1
                else:
                    numPasses = 0

                # End simulation if more than 2 passes
                if numPasses >= 2:
                    break

            if winner == color:
                totalWins += 1

            return totalWins


    def best_rule_moves(self, board, color):

        moveScores = []

        for move in board.get_empty_points():
            # TODO: Make checkMove and uncomment next line
            moveScore = self.checkMove(board, move, color)

            moveScores.append((move, moveScore))
        # Sorts in descending order according moveScore
        moveScores.sort(reverse=True, key=lambda x: x[1])

        bestMoveSet = []
        bestScore = 0

        for move in moveScores:
            if move[1] > bestScore:
                bestScore = move[1]
                bestMoveSet.append(move)

        return bestMoveSet

    def checkMove(self, board, move, color):
            """
            Score Values
                5 - WIN
                4 - BLOCKWIN
                3 - OPENFOUR
                2 - BLOCKOPEN4
                1 - RANDOM
            """

            WIN = 5
            BLOCKWIN = 4
            OPENFOUR = 3
            BLOCKOPEN4 = 2
            RANDOM = 1

            numBlocks = board.check_block_win(color)
            numOpenWins = board.check_open_four(color)
            numOpenBlocks = board.check_block_open_four(color)

            # Play the move
            board.play_move(move, color)

            maxScore = RANDOM

            if(board.detect_five_in_a_row() ==  color):
                maxScore == WIN

            elif(board.check_block_win(color) < numBlocks):
                maxScore == BLOCKWIN

            elif(board.check_open_four(color) > numOpenWins):
                maxScore = OPENFOUR

            elif(board.check_block_open_four(color) < numOpenBlocks):
                maxScore = BLOCKOPEN4

            

            board.undo_move(move)

            return maxScore


def point_to_coord(point, boardsize):
    """
    Transform point given as board array index 
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)


def format_point(move):
    """
    Return move coordinates as a string such as 'A1', or 'PASS'.
    """
    assert MAXSIZE <= 25
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    if move == PASS:
        return "PASS"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("invalid point: '{}'".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("\"{}\" wrong coordinate".format(s))
    return row, col


def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK, "w": WHITE, "e": EMPTY, "BORDER": BORDER}

    try:
        return color_to_int[c]
    except:
        raise KeyError("\"{}\" wrong color".format(c))


def random_sim(board, org_color, cur_color):
    # Check the base cases
    result = board.detect_five_in_a_row()
    # Winner occured
    if result == org_color:
        return True

    # Get list of playable points
    moves = board.get_empty_points().size
    if moves != 0:
        move = random.choice(board.get_empty_points())
    else:
        # Draw occured
        return False

    # Play a move
    board.play_move(move, cur_color)
    check = random_sim(board.copy(), org_color,
                       GoBoardUtil.opponent(cur_color))
    board.undo_move(move)

    return check


