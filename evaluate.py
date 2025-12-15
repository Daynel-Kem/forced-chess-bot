import chess
from forced_chess import forced_legal_moves

# Piece Square Tables
PAWN_TABLE = [
    0,0,0,0,0,0,0,0,
    50,50,50,50,50,50,50,50,
    10,10,20,30,30,20,10,10,
    5,5,10,25,25,10,5,5,
    0,0,-30,20,-30,0,0,0,
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
def evaluate(position: chess.Board, depth_from_root) -> int:
    phase = compute_phase(position)
	
    # If its checkmate, return extremely high value for whoever won
    if position.is_checkmate():
        return -30000 + depth_from_root if position.turn == chess.WHITE else 30000 - depth_from_root
	
    # If its stalemate or no winner, then return 0
    if position.is_stalemate() or position.is_insufficient_material():
        return 0
    
    # Return the final calculated value
    return (material_and_piece_square_value(position, phase) +
            king_safety_value(position, phase) + 
            mobility_value(position) + 
            capture_chain_value(position) +
			pawn_promotion_bonus_value(position) +
            0.5 * pawn_structure_value(position) + 
            aggressive_play_value(position) +
            trap_play_value(position)
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
            
        
        # Pawn promotion potential
        promotion_bonus = 0
        if piece.piece_type == chess.PAWN:
            rank = chess.square_rank(square)
            if piece.color == chess.WHITE and rank == 6:  # 7th rank
                promotion_bonus = 800
            elif piece.color == chess.BLACK and rank == 1:  # 2nd rank
                promotion_bonus = 800

        ps_value += pst if piece.color == chess.WHITE else -pst
        mat_value += (mv + promotion_bonus) if piece.color == chess.WHITE else -(mv + promotion_bonus)
		
    total_value = ps_value + mat_value
    # Bishop Pair Bonus
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        total_value += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        total_value -= 30

    return total_value

# just realized that this is just the same as piece square values lol
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


def king_safety_value(board: chess.Board, phase):
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
                new_rank, new_file = rank + dr, file + df
                if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
                    king_zone.append(chess.square(new_file, new_rank))
        
        attacked_on_king_zone = 0

        for sq in king_zone:
            for attacker in board.attackers(not color, sq):
                move = chess.Move(attacker, sq)

                # Must be a capture AND pseudo-legal
                if board.is_capture(move) and not board.is_pinned(not color, attacker):
                    attacked_on_king_zone += 1
                    break  # only count the square once
        
        safety_penalty = attacked_on_king_zone * (20 * phase // MAX_PHASE)
        
        if color == chess.WHITE:
            score -= safety_penalty
        else:
            score += safety_penalty

    return score
	

def mobility_value(board: chess.Board):
    legal_moves = list(forced_legal_moves(board))
    capture_moves = [m for m in legal_moves if board.is_capture(m)]
    capture_count = len(capture_moves)

    if capture_count == 0:
        mobility = 5 + len(legal_moves)
    elif capture_count == 1:
        mobility = -10
    else:
        mobility = -20 * capture_count
		
    # Penalize bad queen forced captures
    if capture_count > 0 and all(
        board.piece_at(m.from_square).piece_type == chess.QUEEN
        for m in capture_moves):
        mobility -= 30
		
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


# Bro the engine does not promote pawns when it totally can, gotta add a bonus here
def pawn_promotion_bonus_value(board: chess.Board):
    value = 0
    for color in [chess.WHITE, chess.BLACK]:
          pawns = board.pieces(chess.PAWN, color)
          for sq in pawns:
                file = chess.square_file(sq)
                file_squares = [chess.square(file, r) for r in range(8)]
                opponent_color = not color

                opponent_pawns_on_file = any(board.piece_at(s) and board.piece_at(s).piece_type == chess.PAWN
                                             and board.piece_at(s).color == opponent_color
                                             for s in file_squares)

                if not opponent_pawns_on_file:
                      rank = chess.square_rank(sq)
                      advance = rank if color == chess.WHITE else 7 - rank
                      value += 10 * advance if color == chess.WHITE else -10 * advance
    return value


# also the engine plays like a sissy and runs out of time so ima make it more aggressive
def aggressive_play_value(board: chess.Board):
    """
    Returns a score bonus for aggressive tactical opportunities:
    - attacking pieces (undefended ones get extra)
    - checks and discovered checks
    - rooks/queens on open/half-open files
    - pressure around enemy king
    """
    score = 0

    # Attack bonuses
    ATTACK_BONUS = {chess.PAWN: 10, chess.KNIGHT: 30, chess.BISHOP: 30,
                    chess.ROOK: 50, chess.QUEEN: 90}

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        color = piece.color
        opponent_color = not color

        for target_sq in board.attacks(sq):
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color == opponent_color:
                # Base attack bonus
                bonus = ATTACK_BONUS.get(target_piece.piece_type, 0)

                # Extra if the attacked piece is undefended
                if not board.is_attacked_by(opponent_color, target_sq):
                    bonus *= 1.5

                score += bonus if color == chess.WHITE else -bonus

    # Check or discovered check bonus
    if board.is_check():
        score += 50 if board.turn == chess.WHITE else -50

    # Rooks or Queens on open or half-open files
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.piece_type in [chess.ROOK, chess.QUEEN]:
            file = chess.square_file(sq)
            # Count pawns on this file
            pawns_on_file = sum(1 for r in range(8) 
                                if board.piece_at(chess.square(file, r)) 
                                and board.piece_at(chess.square(file, r)).piece_type == chess.PAWN)
            if pawns_on_file == 0:  # open file
                bonus = 20
            elif pawns_on_file == 1:  # half-open
                bonus = 10
            else:
                bonus = 0
            score += bonus if piece.color == chess.WHITE else -bonus

    # Pressure near the enemy king
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is None:
            continue
        opponent_color = not color
        king_zone = []
        rank = chess.square_rank(king_sq)
        file = chess.square_file(king_sq)
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0:
                    continue
                new_rank = rank + dr
                new_file = file + df
                if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
                    king_zone.append(chess.square(new_file, new_rank))

        # Count attackers near the king
        attackers = sum(1 for sq in king_zone if board.is_attacked_by(opponent_color, sq))
        pressure_bonus = 15 * attackers
        score += pressure_bonus if color == chess.BLACK else -pressure_bonus

    return score
 

def trap_play_value(board: chess.Board):
    """
    Bonus for creating tactical threats (traps) against opponent:
    - forks (2+ attackers on high-value pieces)
    - skewers (piece in line with king or queen)
    - pins (piece pinned against king)
    - potential sacrifices (attacking piece vs higher-value target)
    """
    score = 0
    PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}

    for color in [chess.WHITE, chess.BLACK]:
        opponent_color = not color

        # Fork detection: a single piece attacking 2+ high-value enemy pieces
        for sq in board.pieces(chess.KNIGHT, color) | board.pieces(chess.BISHOP, color) | \
                  board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color):
            attacks = list(board.attacks(sq))
            high_value_targets = [t for t in attacks if board.piece_at(t) and board.piece_at(t).color == opponent_color 
                                  and PIECE_VALUES.get(board.piece_at(t).piece_type,0) >= 300]  # Knights/Bishops+
            if len(high_value_targets) >= 2:
                score += 40 * len(high_value_targets) if color == chess.WHITE else -40 * len(high_value_targets)

        # Pin detection opponent piece pinned to king
        king_sq = board.king(opponent_color)
        if king_sq is not None:
            for sq in board.pieces(chess.KNIGHT, color) | board.pieces(chess.BISHOP, color) | \
                      board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color):
                for target_sq in board.attacks(sq):
                    if board.is_pinned(opponent_color, target_sq):
                        score += 25 if color == chess.WHITE else -25

        # Skewer detection (approximation)
        for sq in board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color) | board.pieces(chess.BISHOP, color):
            for target_sq in board.attacks(sq):
                target_piece = board.piece_at(target_sq)
                if target_piece and target_piece.color == opponent_color and target_piece.piece_type != chess.KING:
                    # see if directly behind is the king or queen
                    direction = (chess.square_file(target_sq) - chess.square_file(sq),
                                 chess.square_rank(target_sq) - chess.square_rank(sq))
                    behind_sq = target_sq
                    while True:
                        behind_sq = chess.square(chess.square_file(behind_sq)+direction[0],
                                                 chess.square_rank(behind_sq)+direction[1])
                        if behind_sq < 0 or behind_sq > 63:
                            break
                        behind_piece = board.piece_at(behind_sq)
                        if behind_piece:
                            if behind_piece.color == opponent_color and behind_piece.piece_type in [chess.QUEEN, chess.KING]:
                                score += 30 if color == chess.WHITE else -30
                            break

        # Potential sacrifices: attacking higher-value targets with lower-value pieces
        for sq in board.pieces(chess.PAWN, color) | board.pieces(chess.KNIGHT, color) | board.pieces(chess.BISHOP, color):
            for target_sq in board.attacks(sq):
                target_piece = board.piece_at(target_sq)
                attacker_piece = board.piece_at(sq)
                if target_piece and target_piece.color == opponent_color:
                    if PIECE_VALUES[attacker_piece.piece_type] < PIECE_VALUES[target_piece.piece_type]:
                        score += 15 if color == chess.WHITE else -15

    return score

# helper function to compute the phase
def compute_phase(board: chess.Board):
    phase = 0
    for piece_type, w in PHASE_WEIGHTS.items():
        phase += w * (
            len(board.pieces(piece_type, chess.WHITE)) +
            len(board.pieces(piece_type, chess.BLACK))
        )
    return min(phase, MAX_PHASE)


