from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER
#from profilehooks import profile

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def game_end(board):
    game_end, winner = board.check_game_end_gomoku()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if game_end:
        return 1 if winner == board.current_player else -1
    if board_full:
        return 0
    return None

def alphabeta(board,alpha,beta):
    #print(GoBoardUtil.get_twoD_board(board),alpha,beta)
    result=game_end(board)
    if (result!=None):
        return result
    solvePoint=board.list_solve_point()
    if solvePoint:
        #print(solvePoint[0])
        board.play_move_gomoku(solvePoint[0],board.current_player)
        result=-alphabeta(board,-beta,-alpha)
        if(result>alpha):
            alpha=result
        undo(board,solvePoint[0])
        if(result>=beta):
            return beta
    else:
        for m in GoBoardUtil.generate_legal_moves_gomoku(board):
            board.play_move_gomoku(m,board.current_player)
            result=-alphabeta(board,-beta,-alpha)
            if(result>alpha):
                alpha=result
            undo(board,m)
            if(result>=beta):
                return beta
    return alpha

#@profile
"""
if have winning move, return _,winning_move
else return have_draw,"NoMove"
"""
def solve(board):
    result=game_end(board)
    if (result!=None):
        return result,"First"
    alpha,beta=-1,1
    haveDraw=False
    solvePoint=board.list_solve_point()
    if solvePoint:
        #print(solvePoint[0])
        board.play_move_gomoku(solvePoint[0],board.current_player)
        result=-alphabeta(board,-beta,-alpha)
        undo(board,solvePoint[0])
        if(result==1):
            return True,solvePoint[0]
        elif(result==0):
            haveDraw=True
    else: 
        for m in GoBoardUtil.generate_legal_moves_gomoku(board):
            board.play_move_gomoku(m,board.current_player)
            result=-alphabeta(board,-beta,-alpha)
            #print(GoBoardUtil.get_twoD_board(board))
            #print(result)
            undo(board,m)
            if(result==1):
                return True,m
            elif(result==0):
                haveDraw=True
    return haveDraw,"NoMove"


    """

    for m in board.legal_moves():
        history_set.add(str(board.get_twoD_board())+str(board.current_player))
        board.move(m, board.current_player)
        result,move=None, None
        if board.end_of_game():
            result,move = isSuccess(board, komi), "NoMove"
        elif str(board.get_twoD_board())+str(board.current_player) in history_set:
            board.undo_move()
            continue
        if result==None and move==None:
            result, move = negamaxBoolean(board, komi, history_set)
        success = not result
        board.undo_move()

        history_set.remove(str(board.get_twoD_board())+str(board.current_player))
        if success:
            return True, m
    return False, "NoMove"
    """