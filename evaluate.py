import chess

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
	total = 0
	
	for sq in chess.SQUARES:
		piece = board.piece_at(sq)
		if piece is None:
			continue
		
		table = PIECE_SQUARE_TABLES.get(piece.piece_type)
		if table is None:
			continue
		
		if piece.color == chess.WHITE:
			idx = sq
			total += table[idx]
		else:
			idx = chess.square_mirror(sq)
			total -= table[idx]
			
	return total


def king_safety_value(board: chess.Board):
	score = 0
	
	for color in [chess.WHITE, chess.BLACK]:
		king_square = board.king(color)
		if king_square is None:
			continue
			
		king_zone = []
		rank = chess.square_rank(king_square)
		file = chess.square_file(king_square)
		
		for dr in [-1, 0, 1]:
			for df in [-1, 0, 1]:
				if dr == 0 and df == 0:
					continue
				new_rank, new_file = rank + dr. file + df
				if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
					king_zone.append(chess.square(new_file, new_rank))
		
		attacked_on_king_zone = sum(
			1 for sq in king_zone
			if board.is_attacked_by(not color, sq)
		)
		
		safety_penalty = attacked_on_king_zone * 20
		
		if color == chess.WHITE:
			score -= safety_penalty
		else:
			score += safety_penalty
	
	return score
    pass


def mobility_value(board: chess.Board):
	legal_moves = list(board.legal_moves)
	capture_moves = 0
	
	for move in legal_moves:
		if board.is_capture(move):
			capture_moves += 1
	if capture_moves > 0:
		mobility = capture_moves
	else:
		mobility = len(legal_moves)
	return mobility if board.turn == chess.WHITE else -mobility
		
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
		file_list = files_dict.keys()
		return (f - 1 not in files_list) and (f + 1 not in files_list)
		
	def is_connected(files, f):
		file_list = files_dict.keys()
		return (f - 1 in files_list) or (f + 1 in files_list)
		
	for sq in white_pawns:
		f = chess.sqaure_file(sq)
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
	queens = (
		len(board.pieces(chess.QUEEN, chess.WHITE)) +
		len(board.pieces(chess.QUEEN, chess.BLACK))
	)
	
	minor_major = (
		len(board.pieces(chess.KNIGHT, chess.WHITE)) +
		len(board.pieces(chess.BISHOP, chess.WHITE)) +
		len(board.pieces(chess.ROOK, chess.WHITE)) +
		len(board.pieces(chess.KNIGHT, chess.BLACK)) +
		len(board.pieces(chess.BISHOP, chess.BLACK)) +
		len(board.pieces(chess.ROOK, chess.BLACK)) +
	)					
	return queens == 0 or minor_major <= 4
	






