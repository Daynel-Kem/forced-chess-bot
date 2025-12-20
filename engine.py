import time
import sys
import chess

# from evaluate import evaluate
from forced_chess import forced_legal_moves
from bbsearch import iterative_deepening, TT

MAX_DEPTH = 50

class WinBoardEngine:
    def __init__(self):
        self.board = chess.Board()
        self.force_mode = False
        self.my_color = chess.BLACK 
        self.depth = MAX_DEPTH

        self.my_time = 1 * 60 * 100 # Each player only gets 1 min in our version
        self.opp_time = 1 * 60 * 100
        self.increment = 0
        self.moves_to_go = 40
        self.sudden_death = False

        # the amount of games the engine got flagged is horrendous
        self.panic = False

    # Helper Functions
    def send(self, msg):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()

    def debug(self, msg):
        sys.stderr.write(msg + '\n')

    def in_panic_mode(self) -> bool:
        # milliseconds on xboard clock
        time_left_sec = self.my_time / 100

        # sudden death = no safety net
        if self.sudden_death:
            return time_left_sec < 3.0

        # normal time control
        return (
            time_left_sec < 2.0 or
            (time_left_sec / max(1, self.moves_to_go)) < 0.25
        )

    # Move Handling
    def parse_move(self, move_str):
        try:
            return chess.Move.from_uci(move_str)
        except:
            return None
        
    def make_engine_move(self):
        if self.board.is_game_over():
            return
        
        # If there's only one move, just do that
        moves = forced_legal_moves(self.board)
        if len(moves) == 1:
            move = moves[0]
            self.board.push(move)
            self.send(f"move {move.uci()}")
            return

        # Use iterative deepening search to pick a move
        BASE_TIME = 0.6 # seconds
        MAX_TIME  = 1.2 # never exceed this
        if self.sudden_death or self.moves_to_go is None:
            moves_to_go = 20
        else:
            moves_to_go = max(1, self.moves_to_go)

        time_per_move = min(
            MAX_TIME,
            max(BASE_TIME, (self.my_time / 100) / moves_to_go)
        )

        panic = self.in_panic_mode()

        if panic:
            time_per_move = min(time_per_move, 0.2)

        start_time = time.time()
        res = iterative_deepening(self.board, max_depth=self.depth, time_limit=time_per_move, panic=panic)
        elapsed_time = time.time() - start_time

        # decrement remaining time
        self.my_time -= int(elapsed_time * 100)
        if self.my_time < 0:
            self.my_time = 0

        score = res.score
        move = res.best_move

        # offer a draw if we're losing lmao, see what happens
        TIME_THRESHOLD = 0.2
        DRAW_THRESHOLD = 2000
        elapsed_time = (1 - self.my_time / (self.moves_to_go * time_per_move * 100)) * 100

        send_draw = False
        if self.my_color == chess.WHITE and score <= -DRAW_THRESHOLD:
            send_draw = True
        elif self.my_color == chess.BLACK and score >= DRAW_THRESHOLD:
            send_draw = True

        if not self.force_mode and send_draw and elapsed_time > TIME_THRESHOLD:
            self.send("draw")

        if move is None:
            return

        # push the move and send it to the GUI
        self.board.push(move)
        self.send(f"move {move.uci()}")

        if self.moves_to_go > 1:
            self.moves_to_go -= 1
        else:
            self.moves_to_go = 40  # or sudden-death reset
            

    # Winboard Protocol Handling
    def handle_command(self, cmd):
        self.debug(f"CMD: {cmd}")

        if cmd == "xboard":
            return
        
        if cmd.startswith("protover"):
            self.send("feature ping=1 setboard=1 colors=0 usermove=1")
            self.send("feature done=1")
            return
        
        if cmd == "new":
            self.board.reset()
            self.force_mode = False
            self.my_color = chess.BLACK
            self.my_time = 1 * 60 * 100 # Each player only gets 1 min in our version
            self.opp_time = 1 * 60 * 100
            self.increment = 0
            self.moves_to_go = 40
            self.panic = False
            self.sudden_death = False
            TT.clear()
            return
        
        if cmd == "quit":
            sys.exit(0)

        if cmd == "force":
            self.force_mode = True
            return
        
        if cmd == "go":
            self.force_mode = False
            self.my_color = self.board.turn
            self.make_engine_move()
            return
        
        if cmd == "white":
            self.my_color = chess.WHITE
            return
        
        if cmd == "black":
            self.my_color = chess.BLACK
            return

        if cmd.startswith("setboard"):
            fen = cmd[len("setboard "):]
            self.board.set_fen(fen)
            return
        
        if cmd.startswith("usermove"):
            move_str = cmd.split()[1]
            move = self.parse_move(move_str)

            if move and move in self.board.legal_moves:
                self.board.push(move)

                if not self.force_mode and self.board.turn == self.my_color:
                    if not self.board.is_game_over():
                        self.make_engine_move()

            return
        
        if cmd.startswith("ping"):
            self.send(f"pong {cmd.split()[1]}")
            return
        
        if cmd in ("draw", "offer draw"):
            self.send("decline")
            return
        
        # Time Management
        if cmd.startswith("level"):
            _, moves, minutes, inc = cmd.split()
            self.moves_to_go = max(1, int(moves))
            self.increment = int(inc) * 100
            self.my_time = int(minutes) * 60 * 100
            self.opp_time = self.my_time
            self.sudden_death = False
            return

        if cmd.startswith("st"):
            seconds = int(cmd.split()[1])
            self.my_time = seconds * 100
            self.opp_time = self.my_time
            self.sudden_death = True
            return

        if cmd.startswith("time"):
            self.my_time = int(cmd.split()[1])
            return

        if cmd.startswith("otim"):
            self.opp_time = int(cmd.split()[1])
            return
        

    # Main Function Loop
    def loop(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                self.handle_command(line.strip())
            except KeyboardInterrupt:
                self.debug("Keyboard Interrupt caught in main loop")
                continue

def main():
    engine = WinBoardEngine()
    engine.loop()

if __name__ == "__main__":
    main()