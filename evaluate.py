import chess

# The final evaluatio function
def evaluate(position: chess.Board):

    return (material_value(position) +
            positional_value(position) +
            king_safety_value(position) + 
            mobility_value(position) + 
            capture_chain_value(position) +
            pawn_structure_value(position))


def material_value(board: chess.Board):
    # Material Value = Piece Value + Optionality of Capture Decisions
    
    # Adjusted based on how well each piece improves or worsens in this variant
    CHESS_BASE_VALUES = {
        chess.PAWN: 120,
        chess.KNIGHT: 270,
        chess.BISHOP: 315,
        chess.ROOK: 550,
        chess.QUEEN: 1000,
        chess.KING: 0,
    }

    CHESS_ENDGAME_VALUES = {
        chess.PAWN: 160,
        chess.KNIGHT: 220,
        chess.BISHOP: 360,
        chess.ROOK: 620,
        chess.QUEEN: 900,
        chess.KING: 0,
    }

    value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            if piece.color == chess.WHITE:
                value += CHESS_BASE_VALUES[piece]
            else:
                value -= CHESS_BASE_VALUES[piece]
    return value



def positional_value(board: chess.Board):
    pass


def king_safety_value(board: chess.Board):
    # Calculate if Game State (Endgame or not)
    pass


def mobility_value(board: chess.Board):
	legal_move = list(board.legal_moves):
	capture_move = 0
	
	for move in legal_moves:
		if board.is_capture(move):
			capture_move += 1
		if capture_move > 0:
			mobility = capture_moves
		else:
			mobility = len(legal_moves)
		sign = 1
		if board.turn == chess.BLACK:
			sign = -1
		return sign * mobility
    pass


def capture_chain_value(board: chess.Board):
	score = 0
	CHAIN_PENALTY = 50
	
	for sq in chess.SQUARES:
		piece = board.piece_at(sq)
		
		if piece is not None and piece.piece_type != chess.KING:
			attacked = board.is_attacked_by(not piece.color, sq)
			
			if attacked:
				defended = board.is_attacked_by(piece.color, sq)
				penalty = CHAIN_PENALTY if not defended else CHAIN_PENALTY // 3
				
				if piece.color == chess.WHITE:
					score -= penalty
				else:
					score += penalty
	return score
    pass


def pawn_structure_value(board: chess.Board):

    pass


def piece_activity_value(board: chess.Board):
    pass

