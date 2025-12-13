import chess

def evaluate(board: chess.Board):
    """Simple static evaluation for a forced-capture chess variant."""
    
    # --- Piece values ---
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 300,
        chess.BISHOP: 300,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }
    
    score = 0
    
    # --- Material value ---
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = PIECE_VALUES[piece.piece_type]
            score += val if piece.color == chess.WHITE else -val
    
    # --- Pawn structure value ---
    def pawn_structure_value(board: chess.Board):
        score = 0
        wp = {f: 0 for f in range(8)}
        bp = {f: 0 for f in range(8)}
        
        for sq in board.pieces(chess.PAWN, chess.WHITE):
            wp[chess.square_file(sq)] += 1
        for sq in board.pieces(chess.PAWN, chess.BLACK):
            bp[chess.square_file(sq)] += 1
        
        for f, cnt in wp.items():
            if cnt > 1:
                score -= 10 * (cnt - 1)
            if cnt > 0 and (wp.get(f-1,0) == 0 and wp.get(f+1,0) == 0):
                score -= 12  # isolated
        for f, cnt in bp.items():
            if cnt > 1:
                score += 10 * (cnt - 1)
            if cnt > 0 and (bp.get(f-1,0) == 0 and bp.get(f+1,0) == 0):
                score += 12  # isolated
        return score
    
    score += pawn_structure_value(board)
    
    # --- Capture vulnerability value ---
    def capture_chain_value(board: chess.Board):
        score = 0
        CHAIN_PENALTY = 50
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type != chess.KING:
                attacked = board.is_attacked_by(not piece.color, sq)
                if attacked:
                    defended = board.is_attacked_by(piece.color, sq)
                    penalty = CHAIN_PENALTY if not defended else CHAIN_PENALTY // 3
                    score -= penalty if piece.color == chess.WHITE else -penalty
        return score
    
    score += capture_chain_value(board)
    
    # --- Mobility value ---
    def mobility_value(board: chess.Board):
        legal_moves = list(board.legal_moves)  # replace with forced_legal_moves if needed
        capture_moves = sum(1 for m in legal_moves if board.is_capture(m))
        mobility = capture_moves if capture_moves > 0 else len(legal_moves)
        return mobility if board.turn == chess.WHITE else -mobility
    
    score += mobility_value(board)
    
    return score
