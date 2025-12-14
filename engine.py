import time
import sys
import chess

# from evaluate import evaluate
# from bbsearch import minimax
from forced_chess import forced_legal_moves

from test_evaluate import evaluate
from bbsearch import iterative_deepening

DEFAULT_DEPTH = 7

class WinBoardEngine:
    def __init__(self):
        self.board = chess.Board()
        self.force_mode = False
        self.my_color = chess.BLACK 
        self.depth = DEFAULT_DEPTH

        self.my_time = 1 * 60 * 100 # Each player only gets 1 min in our version
        self.opp_time = 1 * 60 * 100
        self.increment = 0
        self.moves_to_go = 40
        self.sudden_death = False

    # Helper Functions
    def send(self, msg):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()

    def debug(self, msg):
        sys.stderr.write(msg + '\n')

    def set_depth(self, depth):
        self.depth = depth

    # Move Handling
    def parse_move(self, move_str):
        try:
            return chess.Move.from_uci(move_str)
        except:
            return None
        
    def make_engine_move(self):
        if self.board.is_game_over():
            return
        # Use iterative deepening search to pick a move
        res = iterative_deepening(self.board, max_depth=self.depth, time_limit=self.my_time)

        move = res.best_move
        if move is None:
            return

        # push the move and send it to the GUI
        self.board.push(move)
        self.send(f"move {move.uci()}")
            

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
            self.moves_to_go = int(moves)
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