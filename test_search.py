import chess
from test_evaluate import evaluate
from forced_chess import forced_legal_moves

MATE_SCORE = 10_000


def minimax(board, depth, alpha, beta, maximizing):
    # Terminal node
    if depth == 0 or board.is_game_over():
        return evaluate(board), None

    best_move = None

    if maximizing:
        best_score = float("-inf")

        for move in forced_legal_moves(board):
            board.push(move)
            score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        return best_score, best_move

    else:
        best_score = float("inf")

        for move in forced_legal_moves(board):
            board.push(move)
            score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()

            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)
            if beta <= alpha:
                break

        return best_score, best_move
