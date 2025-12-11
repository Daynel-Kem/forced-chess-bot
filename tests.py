from bbsearch import minimax, TT
import chess

def run_test(fen, depth):
    board = chess.Board(fen)

    print("Initial position:")
    print(board)

    score = minimax(board, depth, -10**9, 10**9, board.turn, 0)

    print(f"\nScore returned: {score}")
    print(f"TT entries used: {TT.count_used() if hasattr(TT, 'count_used') else '?'}")

# Example tests:
run_test(chess.STARTING_FEN, depth=3)
run_test("8/8/8/8/8/2k5/3p4/3K4 w - - 0 1", depth=5)  # simple endgame
run_test("rnbqkbnr/pppppppp/8/8/1P6/8/P1PPPPPP/RNBQKBNR b KQkq - 0 1", depth=6)