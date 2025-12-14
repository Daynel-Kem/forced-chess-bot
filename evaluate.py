import chess
from forced_chess import forced_legal_moves

# Piece Square Tables
PAWN_TABLE = [
    0,0,0,0,0,0,0,0,
    50,50,50,50,50,50,50,50,
    10,10,20,30,30,20,10,10,
    5,5,10,25,25,10,5,5,
    0,0,0,20,20,0,0,0,
    5,-5,-10,0,0,-10,-5,5,
    5,10,10,-20,-20,10,10,5,
    0,0,0,0,0,0,0,0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,0,0,0,0,-20,-40,
    -30,0,10,15,15,10,0,-30,
    -30,5,15,20,20,15,5,-30,
    -30,0,15,20,20,15,0,-30,
    -30,5,10,15,15,10,5,-30,
    -40,-20,0,5,5,0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,0,0,0,0,0,0,-10,
    -10,0,5,10,10,5,0,-10,
    -10,5,5,10,10,5,5,-10,
    -10,0,10,10,10,10,0,-10,
    -10,10,10,10,10,10,10,-10,
    -10,5,0,0,0,0,5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
    0,0,0,0,0,0,0,0,
    5,10,10,10,10,10,10,5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    0,0,0,5,5,0,0,0
]

QUEEN_TABLE = [
    -20,-10,-10,-5,-5,-10,-10,-20,
    -10,0,0,0,0,0,0,-10,
    -10,0,5,5,5,5,0,-10,
    -5,0,5,5,5,5,0,-5,
    0,0,5,5,5,5,0,-5,
    -10,5,5,5,5,5,0,-10,
    -10,0,5,0,0,0,0,-10,
    -20,-10,-10,-5,-5,-10,-10,-20
]

KING_MIDDLE_GAME_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20,20,0,0,0,0,20,20,
    20,30,10,0,0,10,30,20
]

KING_END_GAME_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PIECE_SQUARE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}

# Phase (endgame, middlegame)
PHASE_WEIGHTS = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4
}
MAX_PHASE = 24

# Material Value Table (adjusted for forced capture)
CHESS_BASE_VALUES = {
    chess.PAWN: 120,
    chess.KNIGHT: 270,
    chess.BISHOP: 315,
    chess.ROOK: 550,
    chess.QUEEN: 1000,
    chess.KING: 0,
}

CHESS_ENDGAME_VALUES = {
    chess.PAWN: 140,
    chess.KNIGHT: 220,
    chess.BISHOP: 360,
    chess.ROOK: 620,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# The final evaluatio function
def evaluate(position: chess.Board) -> int:
    phase = compute_phase(position)
	
    # If its checkmate, return extremely high value for whoever won
    if position.is_game_over():
        return -30000 if position.turn == chess.WHITE else 30000
	
    # If its stalemate or no winner, then return 0
    if position.is_stalemate() or position.is_insufficient_material():
        return 0
    
    # Return the final calculated value
    return (material_and_piece_square_value(position, phase) +
            # positional_value(position) +
            king_safety_value(position) + 
            mobility_value(position) + 
            capture_chain_value(position) +
			# piece_activity_value(position) +
            pawn_structure_value(position) 
			)

def material_and_piece_square_value(board: chess.Board, phase):
    ps_value = 0
    mat_value = 0
	
    for square, piece in board.piece_map().items():
        idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
		
        if piece.piece_type == chess.KING:
            mg = KING_MIDDLE_GAME_TABLE[idx]
            eg = KING_END_GAME_TABLE[idx]
            pst = (mg * phase + eg * (MAX_PHASE - phase)) // MAX_PHASE
            mv = 0
        else:
            pst = PIECE_SQUARE_TABLES[piece.piece_type][idx]
            mv = (CHESS_BASE_VALUES[piece.piece_type] * phase + 
						  CHESS_ENDGAME_VALUES[piece.piece_type] * (MAX_PHASE - phase)) // MAX_PHASE

        ps_value += pst if piece.color == chess.WHITE else -pst
        mat_value += mv if piece.color == chess.WHITE else -mv
		
    total_value = ps_value + mat_value
    # Bishop Pair Bonus
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        total_value += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        total_value -= 30

    return total_value

def positional_value(board: chess.Board):
    pass


def king_safety_value(board: chess.Board):
    # Calculate if Game State (Endgame or not)
    value = 0
    return value
	


def mobility_value(board: chess.Board):
	legal_moves = list(forced_legal_moves(board))
	capture_moves = 0
	
	for move in legal_moves:
		if board.is_capture(move):
			capture_moves += 1
	if capture_moves > 0:
		mobility = capture_moves
	else:
		mobility = len(legal_moves)
	return mobility if board.turn == chess.WHITE else -mobility


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


def pawn_structure_value(board: chess.Board):
	score = 0
	
	white_pawns = board.pieces(chess.PAWN, chess.WHITE)
	black_pawns = board.pieces(chess.PAWN, chess.BLACK)
	
	def file_counts(pawns):
		counts = {}
		for sq in pawns:
			f = chess.square_file(sq)
			counts[f] = counts.get(f, 0) + 1
		return counts
		
	wp = file_counts(white_pawns)
	bp = file_counts(black_pawns)
	
	for f, cnt in wp.items():
		if cnt > 1:
			score -= 10 * (cnt - 1)
	for f, cnt in bp.items():
		if cnt > 1:
			score += 10 * (cnt - 1)
		
	def is_isolated(files, f):
		files_list = set(files.keys())
		return (f - 1 not in files_list) and (f + 1 not in files_list)
		
	def is_connected(files, f):
		files_list = set(files.keys())
		return (f - 1 in files_list) or (f + 1 in files_list)
		
	for sq in white_pawns:
		f = chess.square_file(sq)
		if is_isolated(wp, f):
			score -= 12
	
	for sq in black_pawns:
		f = chess.square_file(sq)
		if is_isolated(bp, f):
			score += 12
			
	for sq in white_pawns:
		f = chess.square_file(sq)
		if is_connected(wp, f):
			score += 6
			
	for sq in black_pawns:
		f = chess.square_file(sq)
		if is_connected(bp, f):
			score -= 6
	
	return score


def piece_activity_value(board: chess.Board):
    pass
    
# helper function to compute the phase
def compute_phase(board: chess.Board):
    phase = 0
    for piece_type, w in PHASE_WEIGHTS.items():
        phase += w * (
            len(board.pieces(piece_type, chess.WHITE)) +
            len(board.pieces(piece_type, chess.BLACK))
        )
    return min(phase, MAX_PHASE)


