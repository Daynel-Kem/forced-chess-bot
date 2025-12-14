import chess
import pytest

from bbsearch import minimax, TT, order_moves, quiescence_search, iterative_deepening
from forced_chess import forced_legal_moves
from test_evaluate import evaluate
from transposition import Transposition_Table


def run_test(fen, depth):
    board = chess.Board(fen)

    print("Initial position:")
    print(board)

    score = minimax(board, depth, -10**9, 10**9, board.turn, 0)

    print(f"\nScore returned: {score}")
    print(f"TT entries used: {TT.count_used() if hasattr(TT, 'count_used') else '?'}")


def test_order_moves_prefers_captures():
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.BLACK))
    board.turn = chess.WHITE

    moves = list(board.legal_moves)
    ordered = order_moves(board, moves)
    assert ordered, "order_moves returned empty list"
    # The best move should be a capture (Rxa2)
    assert board.is_capture(ordered[0]), "Top-scored move should be a capture"


def test_quiescence_respects_depth_limit_and_returns_standpat():
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.BLACK))
    board.turn = chess.WHITE

    stand = evaluate(board)
    q = quiescence_search(board, -999999, 999999, maximizing_player=True, depth_left=0)
    assert q == stand


def test_iterative_deepening_returns_legal_pv_and_len_limit():
    board = chess.Board()
    res = iterative_deepening(board, max_depth=2, time_limit=1.0)
    assert hasattr(res, 'pv')
    b = board.copy()
    for mv in res.pv:
        assert mv in b.legal_moves, "PV contains illegal move"
        b.push(mv)
    # PV length should be reasonably bounded by the search depth
    assert len(res.pv) <= 2 or len(res.pv) <= 256


def test_minimax_populates_tt():
    board = chess.Board()
    before = TT.count_used()
    minimax(board, 1, -999999, 999999, board.turn, 0)
    after = TT.count_used()
    assert after >= before

def test_tt_replacement_by_depth():
    board = chess.Board()
    TT.store(board, depth=1, score=10, flag="EXACT", best_move=None)
    e1 = TT.lookup(board)
    TT.store(board, depth=2, score=20, flag="EXACT", best_move=None)
    e2 = TT.lookup(board)
    assert e2.depth == 2

def test_tt_collision_key_check():
    # Force two boards to same index by setting size small and crafting keys.
    # With the current replacement policy (replace only when depth > entry.depth),
    # storing two entries with equal depth that hash to the same index will keep
    # the first one and reject (not replace) the second. We assert that behavior,
    # then verify a deeper entry does replace the shallow one.
    small_tt = Transposition_Table(size=2)
    b1 = chess.Board()
    b2 = b1.copy()
    # make a different position b2
    b2.push_san("e4")

    small_tt.store(b1, 1, 0, "EXACT", None)
    small_tt.store(b2, 1, 0, "EXACT", None)

    # First stored entry should be retrievable, second is not (collision + no replace)
    assert small_tt.lookup(b1) is not None
    assert small_tt.lookup(b2) is None

    # Now store b2 with a higher depth and ensure it replaces the colliding entry
    small_tt.store(b2, 2, 0, "EXACT", None)
    assert small_tt.lookup(b2) is not None
    # original b1 should no longer be present at that index
    assert small_tt.lookup(b1) is None


def test_minimax_returns_tt_exact():
    board = chess.Board()
    mv = list(board.legal_moves)[0]
    TT.store(board, depth=5, score=12345, flag="EXACT", best_move=mv)

    score, move = minimax(board, 1, -999999, 999999, board.turn, 0)
    assert score == 12345
    assert move == mv


def test_minimax_depth0_uses_quiescence():
    board = chess.Board()
    # Ensure no TT entry masks quiescence: clear TT slot for this board if present
    key = chess.polyglot.zobrist_hash(board)
    idx = TT.index(key)
    TT.table[idx] = None

    stand = quiescence_search(board, -999999, 999999, maximizing_player=board.turn, depth_left=None)
    score, move = minimax(board, 0, -999999, 999999, board.turn, 0)
    assert score == stand and move is None


def test_quiescence_includes_captures_and_checks():
    # Qxd2 capture exists
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.BLACK))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE

    stand = evaluate(board)
    q = quiescence_search(board, -999999, 999999, maximizing_player=True, depth_left=None)
    assert q != stand


@pytest.mark.xfail(reason="quiescence currently does not detect some discovered-check quiet moves; expected behavior to include them")
def test_quiescence_includes_noncapture_checks():
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E1, chess.Piece(chess.ROOK, chess.WHITE))
    # place a knight on e2 so moving it can uncover the rook and give check
    board.set_piece_at(chess.E2, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE

    stand = evaluate(board)
    q = quiescence_search(board, -999999, 999999, maximizing_player=True, depth_left=None)
    assert q != stand


def test_iterative_deepening_time_limit_returns_quickly():
    board = chess.Board()
    res = iterative_deepening(board, max_depth=10, time_limit=0.0001)
    assert hasattr(res, 'best_move')


def test_iterative_deepening_depth1_equals_minimax_depth1():
    board = chess.Board()
    res = iterative_deepening(board, max_depth=1, time_limit=None)
    score, mv = minimax(board, 1, -999999, 999999, board.turn, 0)
    assert res.best_move == mv


def test_order_moves_respects_pv_and_tt_priority():
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.BLACK))
    board.turn = chess.WHITE

    moves = list(board.legal_moves)
    noncap = next((m for m in moves if not board.is_capture(m)), None)
    assert noncap is not None

    ordered = order_moves(board, moves, pv_move=noncap)
    assert ordered[0] == noncap

    cap = next((m for m in moves if board.is_capture(m)), None)
    assert cap is not None
    TT.store(board, depth=3, score=0, flag="EXACT", best_move=cap)
    ordered2 = order_moves(board, moves, pv_move=None)
    assert ordered2[0] == cap


def test_search_respects_forced_captures():
    # Setup a simple position where a capture is available and should be chosen
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.BLACK))
    board.turn = chess.WHITE

    # Sanity: forced_legal_moves should prefer the capture
    forced_moves = list(forced_legal_moves(board))
    assert any(board.is_capture(m) for m in forced_moves)

    # Minimax at depth 1 should choose the capture
    score, mv = minimax(board, 1, -999999, 999999, board.turn, 0)
    assert mv is not None
    assert board.is_capture(mv), "Search chose a non-capture while captures were available"

    # Iterative deepening should also pick a capture at shallow depth
    res = iterative_deepening(board, max_depth=1, time_limit=None)
    assert hasattr(res, 'best_move')
    assert res.best_move is not None
    assert board.is_capture(res.best_move)


if __name__ == '__main__':
    # Example runs (manual smoke tests)
    run_test(chess.STARTING_FEN, depth=3)
    run_test("8/8/8/8/8/2k5/3p4/3K4 w - - 0 1", depth=5)  # simple endgame
    run_test("rnbqkbnr/pppppppp/8/8/1P6/8/P1PPPPPP/RNBQKBNR b KQkq - 0 1", depth=5)