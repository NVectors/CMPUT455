#!/usr/bin/python3
# /usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from board import GoBoard

class Gomoku3():
    numSim = 10     # 10 simulations for each legal move