
# play_azul.py - Minimal Azul-lite console game using PySWIP + Prolog rules.
# ------------------------------------------------------
# Features:
# - 2 players
# - 5 colors, standard 5x5 wall pattern
# - Factories (5 for 2P), each holds 4 tiles
# - Center
# - Pattern lines with capacities 1..5
# - Legal placement/wall-scoring done by Prolog (azul.pl)
# - Floor penalties
#
# Controls (on your turn):
#   f <factory_index> <color> <row>   -> take all <color> from factory k, push rest to center, place to pattern line <row>
#   c <color> <row>                   -> take all <color> from center, place to pattern line <row>
#   show                              -> show state
#   help                              -> print help
# Round ends automatically when all factories and center are empty.
# Then completed pattern lines move to wall and score.
#
# End condition: when any player completes a full horizontal row on wall.
# Then game ends after scoring bonuses (not implemented; you can add using Prolog predicates).
#
# You need: pip install pyswip

import random
from collections import Counter, defaultdict
from pyswip import Prolog

COLORS = ["blue","yellow","red","black","white"]
ROW_CAP = {1:1,2:2,3:3,4:4,5:5}

# Floor penalties for the first 7 tiles
FLOOR_PENALTIES = [-1,-1,-2,-2,-2,-3,-3]

class Player:
    def __init__(self, name):
        self.name = name
        # pattern lines: row -> {"color": None or color, "count": int}
        self.pattern = {r: {"color": None, "count": 0} for r in range(1,6)}
        # wall grid: 5x5 ints (0/1)
        self.wall = [[0]*5 for _ in range(5)]
        self.score = 0
        self.floor = []  # list of overflow tiles (up to 7 counted for penalties)

    def floor_penalty(self):
        n = min(len(self.floor), len(FLOOR_PENALTIES))
        return sum(FLOOR_PENALTIES[:n])

    def has_completed_row(self):
        # any full row on wall
        for r in range(5):
            if sum(self.wall[r]) == 5:
                return True
        return False

    def render(self, prolog):
        # Show pattern, wall w/ pattern colors mapping, score, floor
        print(f"\n== {self.name} ==")
        print("Score:", self.score)
        print("Pattern lines:")
        for r in range(1,6):
            cap = ROW_CAP[r]
            col = self.pattern[r]["color"]
            cnt = self.pattern[r]["count"]
            filled = (col or ".")*cnt + "."*(cap-cnt)
            print(f"  Row {r} [{cap}]: color={col}  [{filled}]")
        print("Wall: (1=tile placed)")
        for r in range(5):
            print(" ", self.wall[r])
        print("Floor:", self.floor)

class AzulGame:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.players = [Player("P1"), Player("P2")]
        self.current = 0  # index of current player
        # Bag: 20 of each color
        self.bag = []
        for c in COLORS:
            self.bag += [c]*20
        self.discard = []
        self.center = []
        self.n_factories = 5  # 2 players -> 5 factories
        self.factories = [[] for _ in range(self.n_factories)]
        # Prolog
        self.prolog = Prolog()
        self.prolog.consult("azul.pl")
        # Setup first round
        self.refill_factories()

    def draw_tiles(self, n):
        out = []
        for _ in range(n):
            if not self.bag:
                # refill from discard
                self.bag = self.discard[:]
                self.discard = []
                self.rng.shuffle(self.bag)
            if not self.bag:
                break
            out.append(self.bag.pop())
        return out

    def refill_factories(self):
        for i in range(self.n_factories):
            self.factories[i] = self.draw_tiles(4)

    def is_round_empty(self):
        if any(self.factories[i] for i in range(self.n_factories)):
            return False
        if self.center:
            return False
        return True

    def next_player(self):
        self.current = 1 - self.current

    def show_state(self):
        print("\n=== FACTORIES ===")
        for i, f in enumerate(self.factories):
            print(f"F{i}: {Counter(f)} -> {f}")
        print("=== CENTER ===", Counter(self.center), "->", self.center)
        self.players[0].render(self.prolog)
        self.players[1].render(self.prolog)
        print(f"Current turn: {self.players[self.current].name}")

    def legal_wall_target(self, row, color, player: Player):
        # call Prolog: legal_placement(Row, Color, Grid)
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in row) + "]" for row in grid) + "]"
        q = f"legal_placement({row},{color},{py_to_pl})."
        # color atom must be quoted; build properly
        q = f"legal_placement({row}, {color}, {py_to_pl})."
        # In PySWIP we should pass arguments, but for simplicity we format:
        try:
            list(self.prolog.query(f"legal_placement({row}, {color}, {py_to_pl})."))
            return True
        except Exception:
            # If color atom needs quoting
            try:
                list(self.prolog.query(f"legal_placement({row}, '{color}', {py_to_pl})."))
                return True
            except Exception:
                return False

    def prolog_score(self, row, color, player: Player):
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in grid) + "]"
        # Ask for column first to show placement
        col_res = list(self.prolog.query(f"wall_column_for({row}, '{color}', C)."))
        if not col_res:
            return 0, None
        col = col_res[0]["C"]
        # Score based on current grid (before placing this tile)
        sc_res = list(self.prolog.query(f"score_for_placement({py_to_pl}, {row}, '{color}', S)."))
        if not sc_res:
            return 0, col
        return int(sc_res[0]["S"]), col

    def take_from_factory(self, pid, factory_idx, color, row):
        player = self.players[pid]
        if factory_idx < 0 or factory_idx >= self.n_factories:
            print("Invalid factory index.")
            return False
        factory = self.factories[factory_idx]
        if color not in factory:
            print("Factory doesn't have that color.")
            return False
        # Check pattern line capacity & color consistency
        cap = ROW_CAP[row]
        line = player.pattern[row]
        if line["color"] not in (None, color):
            print("Row already has a different color.")
            return False
        if not self.legal_wall_target(row, color, player):
            print("Illegal target: color already placed in that row or cell not empty.")
            return False
        picked = [t for t in factory if t == color]
        rest = [t for t in factory if t != color]
        self.factories[factory_idx] = []
        # Rest go to center
        self.center.extend(rest)
        # Place into pattern line; overflow to floor
        available = cap - line["count"]
        to_line = min(available, len(picked))
        overflow = len(picked) - to_line
        if line["color"] is None and to_line > 0:
            line["color"] = color
        line["count"] += to_line
        player.floor.extend([color]*overflow)
        print(f"{self.players[pid].name} took {len(picked)} {color} from F{factory_idx}; {len(rest)} moved to center; {overflow} overflow to floor.")
        return True

    def take_from_center(self, pid, color, row):
        player = self.players[pid]
        if color not in self.center:
            print("Center doesn't have that color.")
            return False
        cap = ROW_CAP[row]
        line = player.pattern[row]
        if line["color"] not in (None, color):
            print("Row already has a different color.")
            return False
        if not self.legal_wall_target(row, color, player):
            print("Illegal target: color already placed in that row or cell not empty.")
            return False
        count = sum(1 for t in self.center if t == color)
        self.center = [t for t in self.center if t != color]
        available = cap - line["count"]
        to_line = min(available, count)
        overflow = count - to_line
        if line["color"] is None and to_line > 0:
            line["color"] = color
        line["count"] += to_line
        player.floor.extend([color]*overflow)
        print(f"{self.players[pid].name} took {count} {color} from center; {overflow} overflow to floor.")
        return True

    def end_round(self):
        # Move completed lines to wall and score
        for p in self.players:
            for row in range(1,6):
                cap = ROW_CAP[row]
                line = p.pattern[row]
                if line["count"] == cap and line["color"]:
                    color = line["color"]
                    sc, col = self.prolog_score(row, color, p)
                    if col is None:
                        continue
                    # Place on wall
                    p.wall[row-1][col-1] = 1
                    p.score += sc
                    # Move leftover (cap-1 tiles) to discard
                    self.discard.extend([color]*(cap-1))
                    # Clear line
                    p.pattern[row] = {"color": None, "count": 0}
                    print(f"{p.name} placed {color} at row {row}, col {col} for +{sc} points.")
            # Floor penalties
            pen = p.floor_penalty()
            if pen < 0:
                p.score += pen
                print(f"{p.name} floor penalty {pen} points.")
            p.floor = []

        # New round setup
        self.center = []
        self.refill_factories()

    def check_end_game(self):
        return any(p.has_completed_row() for p in self.players)

    def play(self):
        print("Welcome to Azul-lite (console). Type 'help' for commands.")
        while True:
            self.show_state()
            # Check end condition before drafting new round?
            if self.check_end_game():
                print("A player completed a row! Game over.")
                break

            # Drafting phase
            while not self.is_round_empty():
                player = self.players[self.current]
                cmd = input(f"{player.name} turn > ").strip().split()
                if not cmd:
                    continue
                if cmd[0] == "help":
                    print("Commands:")
                    print("  f <factory_idx> <color> <row>  e.g., f 2 red 3")
                    print("  c <color> <row>                e.g., c blue 1")
                    print("  show")
                    continue
                if cmd[0] == "show":
                    self.show_state()
                    continue
                ok = False
                try:
                    if cmd[0] == "f" and len(cmd) == 4:
                        k = int(cmd[1])
                        color = cmd[2]
                        row = int(cmd[3])
                        ok = self.take_from_factory(self.current, k, color, row)
                    elif cmd[0] == "c" and len(cmd) == 3:
                        color = cmd[1]
                        row = int(cmd[2])
                        ok = self.take_from_center(self.current, color, row)
                    else:
                        print("Bad command. Type 'help'.")
                except Exception as e:
                    print("Error:", e)
                    ok = False
                if ok:
                    self.next_player()
            # End of round
            print("\n--- End of round: scoring & refill ---")
            self.end_round()

            if self.check_end_game():
                print("A player completed a row! Game over.")
                break

        # Final scores
        print("\n=== Final Scores ===")
        for p in self.players:
            print(p.name, p.score)
        winner = max(self.players, key=lambda x: x.score)
        print("Winner:", winner.name)

if __name__ == "__main__":
    game = AzulGame(seed=42)
    game.play()
