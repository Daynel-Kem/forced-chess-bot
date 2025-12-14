import chess
from dataclasses import dataclass
from typing import List, Optional
from transposition import Transposition_Table
import time
from forced_chess import forced_legal_moves
# from evaluate import evaluate
from test_evaluate import evaluate

TT = Transposition_Table(size=100000)

@dataclass
class SearchResult:
    best_move: Optional[chess.Move]
    score: int
    depth: int
    time_taken: float
    pv: List[chess.Move]

TT = Transposition_Table(size=2000000)

# Max Player = True means the player is playing White pieces
# Max Player = False means the player is playing Black pieces
def minimax(board: chess.Board, depth, alpha, beta, max_player, depth_from_root, pv=None):
    # Transposition Table Logic
    entry = TT.lookup(board)
    if entry and entry.depth >= depth:
        if entry.flag == "EXACT":
            return entry.score, entry.best_move
        elif entry.flag == "UPPERBOUND":
            beta = min(beta, entry.score)
        elif entry.flag == "LOWERBOUND":
            alpha = max(alpha, entry.score)

        if alpha >= beta:
            return entry.score, entry.best_move
		
	# include quiescence search to the rood note (y u gotta be so rude~)
    if depth == 0 or board.is_game_over():
        score = quiescence_search(board, alpha, beta, maximizing_player=max_player)
        return score, None
	
	# keeping track of best move for best TT and for engine
    best_move = None
	# keep original window for TT flag determination
    orig_alpha, orig_beta = alpha, beta

	# Move Ordering
    pv_move = None
    if pv is not None and depth_from_root < len(pv):
        pv_move = pv[depth_from_root]

    moves = order_moves(board, forced_legal_moves(board), pv_move)

    if max_player:
        m_eval = -float("inf")
        for move in moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, False, depth_from_root+1)
            board.pop()

            if evaluation > m_eval:
                m_eval = evaluation
                best_move = move

            m_eval = max(m_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
    
    else:
        m_eval = float("inf")
        for move in moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, True, depth_from_root+1)
            board.pop()

            if evaluation < m_eval:
                m_eval = evaluation
                best_move = move

            m_eval = min(m_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break

	# determine TT flag relative to the original window
    if m_eval <= orig_alpha:
        flag = "UPPERBOUND"
    elif m_eval >= orig_beta:
        flag = "LOWERBOUND"
    else:
        flag = "EXACT"    
    # store remaining depth (depth is depth_remaining)
    TT.store(board, depth, m_eval, flag, best_move=best_move)

    return m_eval, best_move
     
# Iterative Deepening
def iterative_deepening(board: chess.Board, max_depth: int = 50, 
						time_limit:float = None):
						
	start_time = time.time()
	# stats.reset()
	
	best_move = None
	best_score = -float("inf") 
	pv = []
	
	window = 25
	
	def time_up():
		if time_limit is None:
			return False
		return (time.time() - start_time) >= time_limit
		
	for depth in range(1, max_depth + 1):
		if time_up():
			break

		if depth == 1 or best_move is None:
			alpha = -999999   
			beta = 999999
		else:
			alpha = best_score - window
			beta = best_score + window
			
		score, move = minimax(board, depth, alpha, beta, max_player=board.turn, depth_from_root=0, pv=pv)  
		if score <= alpha and not time_up():
			alpha = -float("inf")
			beta = float("inf")
			score, move = minimax(board, depth, alpha, beta, max_player=board.turn, depth_from_root=0, pv=pv)
		elif score >= beta and not time_up():
			alpha = -float("inf")
			beta = float("inf")
			score, move = minimax(board, depth, alpha, beta, max_player=board.turn, depth_from_root=0, pv=pv)
			
		# I changed how minimax works so it returns the best move itself, so ima comment this out
		# moves = list(forced_legal_moves(board))
		# if moves:
		# 	best_move = max(
		# 		moves, 
		# 		key = lambda mv: TT.lookup(board, mv).score if TT.lookup(board, mv) else -999999
		# 		)
		# else:
		# 	best_move = None

		best_move = move
		best_score = score

		# PV stuff: build a PV for this depth (validate moves and avoid cycles)
		local_pv = []
		board_copy = board.copy()
		next_move = best_move
		visited = set()
		MAX_PV = max(1, depth)

		while next_move and len(local_pv) < MAX_PV:
			# ensure the candidate is legal in the current position
			if next_move not in board_copy.legal_moves:
				break

			local_pv.append(next_move)
			board_copy.push(next_move)

			# simple cycle protection via zobrist
			zob = chess.polyglot.zobrist_hash(board_copy)
			if zob in visited:
				break
			visited.add(zob)

			entry = TT.lookup(board_copy)
			next_move = entry.best_move if entry and entry.best_move else None

		# assign PV for this depth (don't accumulate across depths)
		pv = local_pv
	
		
		elapsed = time.time() - start_time
		
		print(f"[Depth {depth}] score={score} best_move={best_move} "
				f"time={elapsed:.2f}s")

		if abs(score) > 29000:
			print(f"Mate confirmed at depth {depth}")
			break
		
		if time_up():
			break
			
	return SearchResult(best_move = best_move, score = best_score, depth = depth,
						#nodes_searched = stats.nodes, 
						time_taken = time.time() - start_time, pv=pv)
					
# Quiescence Search					
def quiescence_search(board: chess.Board, alpha: int, beta: int, maximizing_player,
						depth_left: int = None) -> int:

	stand_pat = evaluate(board)

	# If a depth limit is provided and exhausted, stop
	if depth_left is not None and depth_left <= 0:
		return stand_pat

	if maximizing_player:
		if stand_pat >= beta:
			return beta
		if stand_pat > alpha:
			alpha = stand_pat
	else:
		if stand_pat <= alpha:
			return alpha
		if stand_pat < beta:
			beta = stand_pat
		
	moves = forced_legal_moves(board)
	tactical_moves = []
	
	for move in moves:
		if board.is_capture(move):
			tactical_moves.append(move)
		else:
			board.push(move)
			# direct check after the move
			gives_check = board.is_check()
			# robust discovered-check detection: check whether the mover now attacks the opponent king
			mover_color = not board.turn
			opp_king_sq = board.king(board.turn)
			if opp_king_sq is not None and board.is_attacked_by(mover_color, opp_king_sq):
				gives_check = True
			board.pop()
			if gives_check:
				tactical_moves.append(move)
	
	if not tactical_moves:
		return stand_pat

	for move in tactical_moves:
		board.push(move)
		next_depth = depth_left - 1 if depth_left is not None else None
		score = quiescence_search(board, alpha, beta, not maximizing_player, next_depth)
		board.pop()

		if maximizing_player:
			if score >= beta:
				return beta
			if score > alpha:
				alpha = score
		else:
			if score <= alpha:
				return alpha
			if score < beta:
				beta = score
	
	return alpha if maximizing_player else beta

# Move Ordering	
def order_moves(board: chess.Board, moves: List[chess.Move], 
				pv_move: Optional[chess.Move] = None) -> List[chess.Move]:
	PIECE_VALUES = {chess.PAWN: 100, 
					chess.KNIGHT: 320,
					chess.BISHOP: 330,
					chess.ROOK: 500,
					chess.QUEEN: 900,
					chess.KING: 20000,}
	
	# transpo table lookup
	tt_entry = TT.lookup(board)
	tt_move = tt_entry.best_move if tt_entry else None
	
	def score(move: chess.Move) -> int:
		s = 0
		if pv_move is not None and move == pv_move:
			return 2_000_000
			
		if tt_move is not None and move == tt_move:
			return 1_500_000
			
		if board.is_capture(move):
			victim_piece = board.piece_at(move.to_square)
			attacker_piece = board.piece_at(move.from_square)
			
			victim_value = PIECE_VALUES[victim_piece.piece_type] if victim_piece else PIECE_VALUES[chess.PAWN]	
			attacker_value = PIECE_VALUES[attacker_piece.piece_type] if attacker_piece else 0

			s += 50_000 + 10 * victim_value - attacker_value
			
			board.push(move)
			if board.is_check():
				s += 20_000
			board.pop()
			
			if move.promotion:
				s += 40_000 + PIECE_VALUES.get(move.promotion, 0)
				
			return s
		return s
		
	return sorted(moves, key = score, reverse = True) 
