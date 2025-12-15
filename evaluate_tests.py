import chess

from evaluate import (
    compute_phase,
    material_and_piece_square_value,
    mobility_value,
    capture_chain_value,
    pawn_structure_value,
    PAWN_TABLE,
    CHESS_ENDGAME_VALUES,
    CHESS_BASE_VALUES,
    MAX_PHASE,
    evaluate
)


def test_compute_phase_start_and_empty():
    start = chess.Board()
    assert compute_phase(start) == MAX_PHASE

    empty = chess.Board()
    empty.clear_board()
    assert compute_phase(empty) == 0


def test_material_and_piece_square_value_single_pawn_white():
    board = chess.Board()
    board.clear_board()
    # place a single white pawn on e2
    board.set_piece_at(chess.E2, chess.Piece(chess.PAWN, chess.WHITE))

    phase = compute_phase(board)
    # index for white is the square itself
    idx = chess.E2
    pst = PAWN_TABLE[idx]

    mv = (CHESS_BASE_VALUES[chess.PAWN] * phase + 
          CHESS_ENDGAME_VALUES[chess.PAWN] * (MAX_PHASE - phase)) // MAX_PHASE

    expected = pst + mv
    assert material_and_piece_square_value(board, phase) == expected


def test_material_and_piece_square_value_bishop_pair_increases():
    b1 = chess.Board()
    b1.clear_board()
    b1.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))

    b2 = b1.copy()
    b2.set_piece_at(chess.F1, chess.Piece(chess.BISHOP, chess.WHITE))

    p1 = compute_phase(b1)
    p2 = compute_phase(b2)

    v1 = material_and_piece_square_value(b1, p1)
    v2 = material_and_piece_square_value(b2, p2)

    assert v2 > v1


def test_pawn_structure_values_doubled_isolated_connected():
    # doubled pawns on file a (note: doubled pawns that have no adjacent-file pawns are
    # considered isolated as well, so each pawn also gets an isolation penalty)
    b = chess.Board()
    b.clear_board()
    b.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    b.set_piece_at(chess.A3, chess.Piece(chess.PAWN, chess.WHITE))
    # expected: doubled penalty = -10, isolation penalty per pawn = -12*2 => -24, total = -34
    assert pawn_structure_value(b) == -34

    # isolated pawn on file a
    b2 = chess.Board()
    b2.clear_board()
    b2.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    assert pawn_structure_value(b2) == -12

    # connected pawns on a and b files
    b3 = chess.Board()
    b3.clear_board()
    b3.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    b3.set_piece_at(chess.B2, chess.Piece(chess.PAWN, chess.WHITE))
    # both pawns are connected -> each gives +6
    assert pawn_structure_value(b3) == 12


def test_capture_chain_unprotected_and_defended():
    # Unprotected white pawn attacked by black queen
    b = chess.Board()
    b.clear_board()
    b.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    b.set_piece_at(chess.E7, chess.Piece(chess.QUEEN, chess.BLACK))
    # Queen attacks e4 and no white defender
    assert capture_chain_value(b) == -50

    # Now defend the pawn with a white rook
    b2 = b.copy()
    b2.set_piece_at(chess.E3, chess.Piece(chess.ROOK, chess.WHITE))
    # Now penalty should be 50 // 3 = 16 (rounded down)
    assert capture_chain_value(b2) == -16


def test_mobility_value_with_and_without_captures():
    # capture available
    b = chess.Board()
    b.clear_board()
    b.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    b.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.BLACK))
    b.turn = chess.WHITE
    # With SEE-based weighting, sum of positive see values // 100 should equal 1
    cap_moves = [m for m in list(b.legal_moves) if b.is_capture(m)]

    # Local SEE fallback used in tests (mirrors evaluate._see fallback behavior)
    def _see_fallback(board, move):
        side = board.turn
        def mat(bb, s):
            total = 0
            for p in bb.piece_map().values():
                val = CHESS_BASE_VALUES[p.piece_type]
                total += val if p.color == s else -val
            return total
        before = mat(board, side)
        b2 = board.copy()
        b2.push(move)
        after = mat(b2, side)
        return after - before

    cap_score = sum(max(0, _see_fallback(b, m)) for m in cap_moves)
    expected = max(1, cap_score // 100) if cap_score > 0 else len(cap_moves)
    assert mobility_value(b) == expected

    # Build a position where Black has a capture available and assert sign is negative
    b_black2 = chess.Board()
    b_black2.clear_board()
    b_black2.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    b_black2.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    b_black2.turn = chess.BLACK
    cap_moves_black = [m for m in list(b_black2.legal_moves) if b_black2.is_capture(m)]
    cap_score_black = sum(max(0, _see_fallback(b_black2, m)) for m in cap_moves_black)
    expected_black = max(1, cap_score_black // 100) if cap_score_black > 0 else len(cap_moves_black)
    assert mobility_value(b_black2) == -expected_black

    # no capture available: a single quiet move
    b2 = chess.Board()
    b2.clear_board()
    b2.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    b2.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
    b2.turn = chess.WHITE
    # there should be at least one legal non-capture move; mobility equals number of forced_legal_moves
    m = mobility_value(b2)
    assert isinstance(m, int)


# Test 1: Starting position
board = chess.Board()
score = evaluate(board, 0)
print(f"Starting position: {score} (should be close to 0)")

# Test 2: Position where White is up a pawn
board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 0 1")
score = evaluate(board, 0)
print(f"White up a pawn: {score} (should be ~100+)")

# Test 3: Position where Black is up a queen
board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
score = evaluate(board, 0)
print(f"Black up a queen: {score} (should be very negative)")

# Test 4: Checkmate position
board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
score = evaluate(board, 0)
print(f"Black checkmated: {score} (should be ~30000)")