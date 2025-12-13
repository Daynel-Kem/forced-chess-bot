import chess
from forced_chess import forced_legal_moves

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
	
    PIECE_SQUARE_TABLES = {
		chess.PAWN: PAWN_TABLE,
		chess.KNIGHT: KNIGHT_TABLE,
		chess.BISHOP: BISHOP_TABLE,
		chess.ROOK: ROOK_TABLE,
		chess.QUEEN: QUEEN_TABLE,
		chess.KING: KING_MIDDLE_GAME_TABLE
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
    


def is_endgame(board: chess.Board):
	white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
	black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
	
	white_pieces = (
		len(board.pieces(chess.KNIGHT, chess.WHITE)) +
		len(board.pieces(chess.BISHOP, chess.WHITE)) +
		len(board.pieces(chess.ROOK, chess.WHITE)) +
		white_queens
	)
	black_pieces = (
		len(board.pieces(chess.KNIGHT, chess.BLACK)) +
		len(board.pieces(chess.BISHOP, chess.BLACK)) +
		len(board.pieces(chess.ROOK, chess.BLACK)) +
		black_queens
	)					
	return (white_queens == 0 and black_queens == 0) or (white_pieces <= 2 and black_pieces <= 2)





