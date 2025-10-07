from enum import Enum


class TileColor(Enum):
    BLUE = "blue"
    YELLOW = "yellow"
    RED = "red"
    BLACK = "black"
    WHITE = "white"


# Game constants
TILES_PER_COLOR = 20
TILES_PER_FACTORY = 4
PATTERN_LINES = 5
WALL_SIZE = 5
FLOOR_LINE_SIZE = 7

# {num_players: num_factories}
FACTORY_DISPLAYS = {2: 5, 3: 7, 4: 9}

FLOOR_PENALTIES = [-1, -1, -2, -2, -2, -3, -3]

COLORED_WALL_PATTERN = [
    [TileColor.BLUE, TileColor.YELLOW, TileColor.RED, TileColor.BLACK, TileColor.WHITE],
    [TileColor.WHITE, TileColor.BLUE, TileColor.YELLOW, TileColor.RED, TileColor.BLACK],
    [TileColor.BLACK, TileColor.WHITE, TileColor.BLUE, TileColor.YELLOW, TileColor.RED],
    [TileColor.RED, TileColor.BLACK, TileColor.WHITE, TileColor.BLUE, TileColor.YELLOW],
    [TileColor.YELLOW, TileColor.RED, TileColor.BLACK, TileColor.WHITE, TileColor.BLUE],
]
