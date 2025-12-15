import chess

def forced_legal_moves(board):
    # Return forced capture legal moves
    legal_moves = list(board.legal_moves)
    captures = [m for m in legal_moves if board.is_capture(m)]
    return captures if captures else legal_moves
