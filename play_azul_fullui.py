"""
play_azul_fullui.py
Azul-lite with pretty UI, 2–4 players, Prolog rules + multi-AI

Gameplay:
    - Click a factory (or the center), then click a pattern row on YOUR board.
    - Player mix is read from config.json: ["human","greedy","random","minimax"]
    - Uses azul.pl for legality & scoring.
    - Agents live in agents.py

Requirements:
    pip install pygame pyswip
"""

# -----------------------------
# Imports
# -----------------------------
import json
import sys
import random
from copy import deepcopy
from collections import Counter
from typing import List, Tuple, Optional

import pygame
from pyswip import Prolog

from agents import RandomAgent, GreedyAgent, MiniMaxAgent


# -----------------------------
# Constants & Colors
# -----------------------------
WINDOW_WIDTH = 1208
WINDOW_HEIGHT = 728

BG_COLOR = (139, 90, 43)     # wood-like background
CARD_BG = (225, 225, 225)
CARD_EDGE = (60, 60, 60)

BOARD_WIDTH = 450
BOARD_HEIGHT = 290
TOP_BAR_HEIGHT = 90

PATTERN_CELL_SIZE = 35
WALL_CELL_SIZE = 22
FLOOR_CELL_SIZE = 28
MARGIN = 3

COLORS = ["blue", "green", "red", "yellow", "gray"]  # 5 colors for this variant

COLOR_RGB = {
    "blue":   (60, 100, 200),
    "green":  (80, 190, 140),
    "red":    (200, 70, 70),
    "yellow": (220, 200, 60),
    "gray":   (120, 120, 120),
    "beige":  (245, 235, 200),
}

FLOOR_PENALTIES = [-1, -1, -2, -2, -2, -3, -3]

# Wall pattern (visual target grid only)
WALL_TARGET = [
    ["blue", "yellow", "red", "gray", "green"],
    ["green", "blue", "yellow", "red", "gray"],
    ["gray", "green", "blue", "yellow", "red"],
    ["red", "gray", "green", "blue", "yellow"],
    ["yellow", "red", "gray", "green", "blue"],
]


# -----------------------------
# Utility Functions
# -----------------------------
def factories_for_players(n: int) -> int:
    """Number of factories depending on player count."""
    return {2: 5, 3: 7, 4: 9}[n]


def draw_tile(surface, x, y, size, color, pattern: str = "grid"):
    """Draw a single tile with optional pattern."""
    if color == "empty":
        pygame.draw.rect(surface, (220, 220, 220), (x, y, size, size))
        pygame.draw.rect(surface, (100, 100, 100), (x, y, size, size), 1)
        return

    bg = COLOR_RGB.get(color, (255, 255, 255))
    pygame.draw.rect(surface, bg, (x, y, size, size), border_radius=3)
    pygame.draw.rect(surface, (20, 20, 20), (x, y, size, size), 2, border_radius=3)

    # Patterns
    if pattern == "v":
        for i in range(0, size, 3):
            pygame.draw.line(surface, (0, 0, 0), (x+i, y), (x+i, y+size), 1)
    elif pattern == "h":
        for i in range(0, size, 3):
            pygame.draw.line(surface, (0, 0, 0), (x, y+i), (x+size, y+i), 1)
    elif pattern == "d":
        for i in range(-size, size*2, 5):
            pygame.draw.line(surface, (255, 255, 255), (x+i, y), (x+i+size, y+size), 1)
    else:  # grid
        spacing = max(3, size // 5)
        for i in range(spacing, size, spacing):
            pygame.draw.line(surface, (0, 0, 0), (x+i, y), (x+i, y+size), 1)
            pygame.draw.line(surface, (0, 0, 0), (x, y+i), (x+size, y+i), 1)


# -----------------------------
# Data Structures
# -----------------------------
class Player:
    """Represents one Azul player."""
    def __init__(self, name, ptype="human"):
        self.name = name
        self.ptype = ptype
        self.pattern = {r: {"color": None, "count": 0} for r in range(1, 6)}
        self.wall = [[0] * 5 for _ in range(5)]
        self.score = 0
        self.floor = []

    def floor_penalty(self) -> int:
        n = min(len(self.floor), len(FLOOR_PENALTIES))
        return sum(FLOOR_PENALTIES[:n])

    def has_completed_row(self) -> bool:
        return any(sum(r) == 5 for r in self.wall)


class AzulGame:
    """Core Azul game logic (rules, Prolog calls, state updates)."""
    def __init__(self, prolog: Prolog, player_types, seed=42):
        self.rng = random.Random(seed)
        self.prolog = prolog
        self.players = [Player(f"P{i+1}", t) for i, t in enumerate(player_types)]
        self.N = len(self.players)

        if self.N not in (2, 3, 4):
            raise ValueError("Players must be 2–4")

        self.current = 0

        # Bag + discard (20 per color)
        self.bag = [c for c in COLORS for _ in range(20)]
        self.discard = []
        self.center = []

        # Factories
        self.n_factories = factories_for_players(self.N)
        self.factories = [[] for _ in range(self.n_factories)]
        self.refill_factories()

        # Agents
        self.agents = []
        for p in self.players:
            if p.ptype == "human":
                self.agents.append(None)
            elif p.ptype == "random":
                self.agents.append(RandomAgent(self.prolog))
            elif p.ptype == "greedy":
                self.agents.append(GreedyAgent(self.prolog))
            elif p.ptype == "minimax":
                self.agents.append(MiniMaxAgent(self.prolog, depth=2))
            else:
                self.agents.append(None)

    # -------------------------
    # Mechanics
    # -------------------------
    def draw_tiles(self, n: int) -> List[str]:
        out = []
        for _ in range(n):
            if not self.bag:
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

    def is_round_empty(self) -> bool:
        return (all(len(f) == 0 for f in self.factories) and len(self.center) == 0)

    def next_player(self):
        self.current = (self.current + 1) % self.N

    def legal_wall_target(self, row, color, player):
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in grid) + "]"
        list(self.prolog.query(f"legal_placement({row}, '{color}', {py_to_pl})."))
        return True

    def prolog_score(self, row, color, player):
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in grid) + "]"
        col_res = list(self.prolog.query(f"wall_column_for({row}, '{color}', C)."))
        if not col_res:
            return 0, None
        col = col_res[0]["C"]
        sc_res = list(self.prolog.query(f"score_for_placement({py_to_pl}, {row}, '{color}', S)."))
        if not sc_res:
            return 0, col
        return int(sc_res[0]["S"]), col


# -----------------------------
# UI Helper Functions
# -----------------------------
def draw_factory(surface, x, y, tiles):
    pygame.draw.circle(surface, (255, 255, 255), (x, y), 45)
    pygame.draw.circle(surface, (0, 0, 0), (x, y), 45, 3)
    positions = [(-16, -16), (16, -16), (-16, 16), (16, 16)]
    for i, (dx, dy) in enumerate(positions):
        if i < len(tiles):
            t = tiles[i]
            draw_tile(surface, x+dx-14, y+dy-14, 28, t, "grid")


def draw_center(surface, x, y, tiles):
    pygame.draw.circle(surface, (200, 180, 150), (x, y), 60)
    for i, t in enumerate(tiles):
        dx = (i % 5) * 22 - 44
        dy = (i // 5) * 22 - 22
        draw_tile(surface, x+dx, y+dy, 20, t, "grid")


def draw_player_board(surface, rect, player: Player):
    x, y, w, h = rect
    pygame.draw.rect(surface, CARD_BG, rect, border_radius=10)
    pygame.draw.rect(surface, CARD_EDGE, rect, 3, border_radius=10)

    # Header
    name_text = pygame.font.Font(None, 28).render(f"{player.name} ({player.ptype})", True, (0, 0, 0))
    surface.blit(name_text, (x+16, y+10))
    score_text = pygame.font.Font(None, 28).render(f"Score: {player.score}", True, (0, 0, 0))
    surface.blit(score_text, (x+w-120, y+10))

    # Pattern rows
    pattern_start_x, pattern_start_y = x+20, y+50
    for row in range(1, 6):
        slots = row
        y_pos = pattern_start_y + (row-1)*(PATTERN_CELL_SIZE+MARGIN)
        for col in range(slots):
            x_pos = pattern_start_x + (5-row)*(PATTERN_CELL_SIZE+MARGIN) + col*(PATTERN_CELL_SIZE+MARGIN)
            rect_cell = pygame.Rect(x_pos, y_pos, PATTERN_CELL_SIZE, PATTERN_CELL_SIZE)
            pygame.draw.rect(surface, (210, 210, 220), rect_cell)
            pygame.draw.rect(surface, (100, 100, 100), rect_cell, 1)
            if col < player.pattern[row]["count"]:
                c = player.pattern[row]["color"]
                draw_tile(surface, x_pos, y_pos, PATTERN_CELL_SIZE, c, "grid")

    # Arrow
    arrow_x, arrow_y = x+230, y+140
    pygame.draw.polygon(surface, (150, 150, 150), [(arrow_x, arrow_y-12), (arrow_x+20, arrow_y), (arrow_x, arrow_y+12)])

    # Wall with faded target
    wall_start_x, wall_start_y = x+260, y+50
    for rr in range(5):
        for cc in range(5):
            rx = wall_start_x + cc*(WALL_CELL_SIZE+2)
            ry = wall_start_y + rr*(WALL_CELL_SIZE+2)
            faded = tuple(min(255, int(v*0.45)) for v in COLOR_RGB[WALL_TARGET[rr][cc]])
            pygame.draw.rect(surface, faded, (rx, ry, WALL_CELL_SIZE, WALL_CELL_SIZE))
            if player.wall[rr][cc] == 1:
                draw_tile(surface, rx, ry, WALL_CELL_SIZE, WALL_TARGET[rr][cc], "grid")
            pygame.draw.rect(surface, (160, 160, 160), (rx, ry, WALL_CELL_SIZE, WALL_CELL_SIZE), 1)

    # Floor
    floor_start_x, floor_start_y = x+10, y+240
    for i in range(7):
        rx = floor_start_x + i*(FLOOR_CELL_SIZE+MARGIN)
        ry = floor_start_y
        pygame.draw.rect(surface, (240, 220, 220), (rx, ry, FLOOR_CELL_SIZE, FLOOR_CELL_SIZE))
        pygame.draw.rect(surface, (100, 100, 100), (rx, ry, FLOOR_CELL_SIZE, FLOOR_CELL_SIZE), 1)
        if i < len(player.floor):
            draw_tile(surface, rx, ry, FLOOR_CELL_SIZE, player.floor[i], "grid")
        pen_text = pygame.font.Font(None, 18).render(str(FLOOR_PENALTIES[i]), True, (120, 0, 0))
        surface.blit(pen_text, (rx+8, ry+FLOOR_CELL_SIZE+4))


def layout_rects(N):
    margin = 8
    bw, bh = 400, 300
    if N == 2:
        return [
            (margin, margin+TOP_BAR_HEIGHT, bw, bh),
            (WINDOW_WIDTH-bw-margin, WINDOW_HEIGHT-bh-margin, bw, bh)
        ]
    elif N == 3:
        return [
            (margin, margin+TOP_BAR_HEIGHT, bw, bh),
            (WINDOW_WIDTH-bw-margin, margin+TOP_BAR_HEIGHT, bw, bh),
            (margin, WINDOW_HEIGHT-bh-margin, bw, bh)
        ]
    else:  # N == 4
        return [
            (margin, margin+TOP_BAR_HEIGHT, bw, bh),
            (WINDOW_WIDTH-bw-margin, margin+TOP_BAR_HEIGHT, bw, bh),
            (margin, WINDOW_HEIGHT-bh-margin, bw, bh),
            (WINDOW_WIDTH-bw-margin, WINDOW_HEIGHT-bh-margin, bw, bh)
        ]


def hit_factory(game: AzulGame, pos):
    fx = WINDOW_WIDTH//2 - 100
    fy = TOP_BAR_HEIGHT + 40
    idx = 0
    for r in range((game.n_factories+1)//2):
        for c in range(2):
            if idx >= game.n_factories:
                break
            cx = fx + c*160
            cy = fy + r*110
            x, y = pos
            if (x-cx)**2 + (y-cy)**2 <= 45**2:
                return idx, (cx, cy)
            idx += 1
    return None, (0, 0)


def draw_factories(surface, game: AzulGame):
    fx = WINDOW_WIDTH//2 - 120
    fy = TOP_BAR_HEIGHT + 40
    idx = 0
    for r in range((game.n_factories+1)//2):
        for c in range(2):
            if idx >= game.n_factories:
                break
            cx = fx + c*240
            cy = fy + r*110
            draw_factory(surface, cx, cy, game.factories[idx])
            draw_text = pygame.font.Font(None, 24).render(str(idx), True, (0, 0, 0))
            surface.blit(draw_text, (cx-6, cy+50))
            idx += 1


def draw_top_bar(screen, players_display, round_counter, max_rounds):
    pygame.draw.rect(screen, (60, 60, 60), (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
    font = pygame.font.Font(None, 28)

    positions = [10, 310, 610, 910]
    for pos, p in zip(positions, players_display):
        name_text = font.render(p["name"], True, (255, 255, 255))
        screen.blit(name_text, (pos, 15))
        time_box_x = pos + 200
        pygame.draw.rect(screen, (200, 230, 255), (time_box_x, 8, 70, 25), border_radius=5)
        time_text = font.render(p["time"], True, (0, 100, 200))
        screen.blit(time_text, (time_box_x+8, 12))

    bar_y, bar_height = 45, 20
    pygame.draw.rect(screen, (255, 255, 255), (10, bar_y, WINDOW_WIDTH-20, bar_height), border_radius=5)
    progress_text = pygame.font.Font(None, 24).render("Game in Progress", True, (0, 100, 200))
    screen.blit(progress_text, (WINDOW_WIDTH//2 - 90, bar_y+2))

    progress_width = int((round_counter/max_rounds) * (WINDOW_WIDTH - 240))
    pygame.draw.rect(screen, (0, 150, 255), (10, bar_y, progress_width, bar_height), border_radius=5)

    counter_text = font.render(f"{round_counter}/{max_rounds}", True, (0, 100, 200))
    screen.blit(counter_text, (WINDOW_WIDTH - 110, bar_y+2))
    mult_text = font.render("× 1", True, (0, 100, 200))
    screen.blit(mult_text, (WINDOW_WIDTH - 50, bar_y+25))


# -----------------------------
# Main Loop
# -----------------------------
def main():
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {"players": ["human", "greedy", "random", "greedy"]}

    player_types = cfg.get("players", ["human", "greedy"])[:4]
    if len(player_types) < 2:
        player_types = ["human", "greedy"]

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Azul")
    clock = pygame.time.Clock()

    prolog = Prolog()
    prolog.consult("azul.pl")

    game = AzulGame(prolog, player_types, seed=42)

    players_display = [
        {"name": "guest100023(1500)", "time": "09:12"},
        {"name": "CPU", "time": "10:00"},
        {"name": "CPU", "time": "10:00"},
        {"name": "CPU", "time": "10:00"},
    ]

    round_counter, max_rounds = 1, 28
    selected_source, selected_color = None, None

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # TODO: handle clicks + turns (kept minimal here)

        # ---- Rendering ----
        screen.fill(BG_COLOR)
        draw_top_bar(screen, players_display, round_counter, max_rounds)
        draw_factories(screen, game)
        draw_center(screen, WINDOW_WIDTH//2, TOP_BAR_HEIGHT+300, game.center)

        rects = layout_rects(game.N)
        for p, rect in zip(game.players, rects):
            draw_player_board(screen, rect, p)

        info = pygame.font.Font(None, 22).render(
            f"Turn: {game.players[game.current].name} | Selected: {selected_source} / {selected_color}",
            True, (255, 255, 255)
        )
        screen.blit(info, (16, WINDOW_HEIGHT-22))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    main()
# another ui version
"""
# play_azul_fullui.py - Azul-lite with pretty UI, 2–4 players, Prolog rules + multi-AI
# - Click a factory (or the center), then click a pattern row on YOUR board.
# - Player mix is read from config.json: ["human","greedy","random","minimax"]
# - Uses azul.pl for legality & scoring. Agents live in agents.py
#
# Requirements:
#   pip install pygame pyswip

import json
import sys
import random
import math
from copy import deepcopy
from collections import Counter

import pygame
from pyswip import Prolog

from agents import RandomAgent, GreedyAgent, MiniMaxAgent

# ----- Constants & Colors -----
WINDOW_WIDTH = 1208
WINDOW_HEIGHT = 728
BG_COLOR = (139, 90, 43)     # wood-like
CARD_BG = (225, 225, 225)
CARD_EDGE = (60, 60, 60)

PATTERN_CELL_SIZE = 35
WALL_CELL_SIZE = 22
FLOOR_CELL_SIZE = 28
MARGIN = 3

COLORS = ["blue","green","red","yellow","gray"]
COLOR_RGB = {
    "blue": (60,100,200),
    "green": (80,190,140),
    "red": (200,70,70),
    "yellow": (220,200,60),
    "gray": (120,120,120),
}
FLOOR_PENALTIES = [-1,-1,-2,-2,-2,-3,-3]

# Wall pattern (rotating target grid for visuals)
WALL_TARGET = [
    ["blue","yellow","red","gray","green"],
    ["green","blue","yellow","red","gray"],
    ["gray","green","blue","yellow","red"],
    ["red","gray","green","blue","yellow"],
    ["yellow","red","gray","green","blue"],
]

def factories_for_players(n):
    return {2:5, 3:7, 4:9}[n]

# ----- Tile Rendering -----
def draw_tile(surface, x, y, size, color):
    if color == "empty":
        pygame.draw.rect(surface, (220,220,220), (x,y,size,size))
        pygame.draw.rect(surface, (100,100,100), (x,y,size,size), 1)
        return
    bg = COLOR_RGB.get(color, (255,255,255))
    pygame.draw.rect(surface, bg, (x,y,size,size), border_radius=3)
    pygame.draw.rect(surface, (20,20,20), (x,y,size,size), 2, border_radius=3)

# ----- Game Data Structures -----
class Player:
    def __init__(self, name, ptype="human"):
        self.name = name
        self.ptype = ptype
        self.pattern = {r: {"color": None, "count": 0} for r in range(1,6)}
        self.wall = [[0]*5 for _ in range(5)]
        self.score = 0
        self.floor = []

    def floor_penalty(self):
        n = min(len(self.floor), len(FLOOR_PENALTIES))
        return sum(FLOOR_PENALTIES[:n])

    def has_completed_row(self):
        return any(sum(r)==5 for r in self.wall)

class AzulGame:
    def __init__(self, prolog: Prolog, player_types, seed=42):
        self.rng = random.Random(seed)
        self.prolog = prolog
        self.players = [Player(f"P{i+1}", t) for i,t in enumerate(player_types)]
        self.N = len(self.players)
        if self.N not in (2,3,4):
            raise ValueError("Players must be 2–4")
        self.current = 0

        # bag + discard (20 of each color)
        self.bag = []
        for c in COLORS:
            self.bag += [c]*20
        self.discard = []

        self.center = []
        self.n_factories = factories_for_players(self.N)
        self.factories = [[] for _ in range(self.n_factories)]
        self.refill_factories()

        # bind agents
        self.agents = []
        for p in self.players:
            if p.ptype == "human":
                self.agents.append(None)
            elif p.ptype == "random":
                self.agents.append(RandomAgent(self.prolog))
            elif p.ptype == "greedy":
                self.agents.append(GreedyAgent(self.prolog))
            elif p.ptype == "minimax":
                self.agents.append(MiniMaxAgent(self.prolog, depth=2))
            else:
                self.agents.append(None)

    def draw_tiles(self, n):
        out = []
        for _ in range(n):
            if not self.bag:
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
        return (all(len(f)==0 for f in self.factories) and len(self.center)==0)

    def next_player(self):
        self.current = (self.current + 1) % self.N

    def legal_wall_target(self, row, color, player):
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in grid) + "]"
        list(self.prolog.query(f"legal_placement({row}, '{color}', {py_to_pl})."))
        return True

    def prolog_score(self, row, color, player):
        grid = player.wall
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in grid) + "]"
        col_res = list(self.prolog.query(f"wall_column_for({row}, '{color}', C)."))
        if not col_res:
            return 0, None
        col = col_res[0]["C"]
        sc_res = list(self.prolog.query(f"score_for_placement({py_to_pl}, {row}, '{color}', S)."))
        if not sc_res:
            return 0, col
        return int(sc_res[0]["S"]), col

    def take_from_factory(self, pid, factory_idx, color, row):
        player = self.players[pid]
        if color not in self.factories[factory_idx]:
            return False, "Factory doesn't have that color."
        cap = row
        line = player.pattern[row]
        if line["color"] not in (None, color):
            return False, "Row has different color."
        try:
            self.legal_wall_target(row, color, player)
        except Exception:
            return False, "Illegal: color already placed in that row."
        picked = [t for t in self.factories[factory_idx] if t == color]
        rest = [t for t in self.factories[factory_idx] if t != color]
        self.factories[factory_idx] = []
        self.center.extend(rest)
        available = cap - line["count"]
        to_line = min(available, len(picked))
        overflow = len(picked) - to_line
        if line["color"] is None and to_line > 0:
            line["color"] = color
        line["count"] += to_line
        player.floor.extend([color]*overflow)
        return True, f"{len(picked)} {color} from F{factory_idx}, overflow {overflow}."

    def take_from_center(self, pid, color, row):
        player = self.players[pid]
        if color not in self.center:
            return False, "Center doesn't have that color."
        cap = row
        line = player.pattern[row]
        if line["color"] not in (None, color):
            return False, "Row has different color."
        try:
            self.legal_wall_target(row, color, player)
        except Exception:
            return False, "Illegal: color already placed in that row."
        count = sum(1 for t in self.center if t == color)
        self.center = [t for t in self.center if t != color]
        available = cap - line["count"]
        to_line = min(available, count)
        overflow = count - to_line
        if line["color"] is None and to_line > 0:
            line["color"] = color
        line["count"] += to_line
        player.floor.extend([color]*overflow)
        return True, f"{count} {color} from center, overflow {overflow}."

    def end_round(self, log):
        for p in self.players:
            for row in range(1,6):
                cap = row
                line = p.pattern[row]
                if line["count"] == cap and line["color"]:
                    color = line["color"]
                    sc, col = self.prolog_score(row, color, p)
                    if col is None:
                        continue
                    p.wall[row-1][col-1] = 1
                    p.score += sc
                    self.discard.extend([color]*(cap-1))
                    p.pattern[row] = {"color": None, "count": 0}
                    log.append(f"{p.name} placed {color} at r{row}, c{col} (+{sc}).")
            pen = p.floor_penalty()
            if pen < 0:
                p.score += pen
                log.append(f"{p.name} floor penalty {pen}.")
            p.floor = []
        self.center = []
        self.refill_factories()

    def check_end_game(self):
        return any(p.has_completed_row() for p in self.players)

# ----- UI Components -----
def draw_factory(surface, x, y, tiles):
    pygame.draw.circle(surface, (255,255,255), (x,y), 45)
    pygame.draw.circle(surface, (0,0,0), (x,y), 45, 3)
    positions = [(-16,-16),(16,-16),(-16,16),(16,16)]
    for i,(dx,dy) in enumerate(positions):
        if i < len(tiles):
            t = tiles[i]
            draw_tile(surface, x+dx-14, y+dy-14, 28, t)

def draw_center(surface, x, y, tiles):
    # Removed beige overlap circle
    for i,t in enumerate(tiles):
        dx = (i % 5)*22 - 44
        dy = (i // 5)*22 - 22
        draw_tile(surface, x+dx, y+dy, 20, t)

def draw_player_board(surface, rect, player: Player):
    x,y,w,h = rect
    pygame.draw.rect(surface, CARD_BG, rect, border_radius=10)
    pygame.draw.rect(surface, CARD_EDGE, rect, 3, border_radius=10)

    # header
    name_text = pygame.font.Font(None, 24).render(f"{player.name} ({player.ptype})", True, (0,0,0))
    surface.blit(name_text, (x+16, y+10))
    score_text = pygame.font.Font(None, 24).render(f"Score: {player.score}", True, (0,0,0))
    surface.blit(score_text, (x+w-120, y+10))

    # pattern rows
    pattern_start_x = x + 20
    pattern_start_y = y + 50
    for row in range(1,6):
        slots = row
        y_pos = pattern_start_y + (row-1)*(PATTERN_CELL_SIZE + MARGIN)
        for col in range(slots):
            x_pos = pattern_start_x + (5-row)*(PATTERN_CELL_SIZE+MARGIN) + col*(PATTERN_CELL_SIZE+MARGIN)
            rect_cell = pygame.Rect(x_pos, y_pos, PATTERN_CELL_SIZE, PATTERN_CELL_SIZE)
            pygame.draw.rect(surface, (210,210,220), rect_cell)
            pygame.draw.rect(surface, (100,100,100), rect_cell, 1)
            if col < player.pattern[row]["count"]:
                c = player.pattern[row]["color"]
                draw_tile(surface, x_pos, y_pos, PATTERN_CELL_SIZE, c)

    # wall
    wall_start_x = x + 260
    wall_start_y = y + 50
    for rr in range(5):
        for cc in range(5):
            rx = wall_start_x + cc*(WALL_CELL_SIZE+2)
            ry = wall_start_y + rr*(WALL_CELL_SIZE+2)
            faded = tuple(int(v*0.55) for v in COLOR_RGB[WALL_TARGET[rr][cc]])
            pygame.draw.rect(surface, faded, (rx,ry,WALL_CELL_SIZE,WALL_CELL_SIZE))
            if player.wall[rr][cc]==1:
                draw_tile(surface, rx, ry, WALL_CELL_SIZE, WALL_TARGET[rr][cc])
            pygame.draw.rect(surface, (80,80,80), (rx,ry,WALL_CELL_SIZE,WALL_CELL_SIZE), 1)

    # floor
    fx = x + 20; fy = y + 236
    fnt = pygame.font.Font(None, 18)
    for i in range(7):
        cell = pygame.Rect(fx+i*(FLOOR_CELL_SIZE+MARGIN), fy, FLOOR_CELL_SIZE, FLOOR_CELL_SIZE)
        pygame.draw.rect(surface, (245,220,220), cell)
        pygame.draw.rect(surface, (120,90,90), cell, 1)
        if i < len(player.floor):
            draw_tile(surface, cell.x, cell.y, FLOOR_CELL_SIZE, player.floor[i])
        surface.blit(fnt.render(str(FLOOR_PENALTIES[i]), True, (140,0,0)), (cell.x+8, cell.y+FLOOR_CELL_SIZE+2))

def layout_rects(N):
    margin = 8
    bw, bh = 380, 280
    if N == 2:
        return [(margin, margin, bw, bh),
                (WINDOW_WIDTH-bw-margin, WINDOW_HEIGHT-bh-margin, bw, bh)]
    elif N == 3:
        return [(margin, margin, bw, bh),
                (WINDOW_WIDTH-bw-margin, margin, bw, bh),
                (margin, WINDOW_HEIGHT-bh-margin, bw, bh)]
    else:
        return [(margin, margin, bw, bh),
                (WINDOW_WIDTH-bw-margin, margin, bw, bh),
                (margin, WINDOW_HEIGHT-bh-margin, bw, bh),
                (WINDOW_WIDTH-bw-margin, WINDOW_HEIGHT-bh-margin, bw, bh)]

def draw_factories(surface, game: AzulGame):
    cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
    radius = 160
    for idx, tiles in enumerate(game.factories):
        angle = 2 * math.pi * idx / game.n_factories
        fx = int(cx + radius * math.cos(angle))
        fy = int(cy + radius * math.sin(angle))
        draw_factory(surface, fx, fy, tiles)

# ----- Main Loop -----
def main():
    try:
        with open("config.json","r") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {"players": ["human","greedy","random","greedy"]}
    player_types = cfg.get("players", ["human","greedy"])[:4]
    if len(player_types) < 2:
        player_types = ["human","greedy"]

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Azul")
    clock = pygame.time.Clock()

    prolog = Prolog(); prolog.consult("azul.pl")
    game = AzulGame(prolog, player_types, seed=42)

    selected_source = None
    selected_color = None
    log = ["Click a factory (or the center), then click your pattern row."]

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # draw
        screen.fill(BG_COLOR)
        draw_factories(screen, game)
        draw_center(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2, game.center)
        rects = layout_rects(game.N)
        for p, rect in zip(game.players, rects):
            draw_player_board(screen, rect, p)
        pygame.display.flip()

    pygame.quit(); sys.exit(0)

if __name__ == "__main__":
    main()

"""