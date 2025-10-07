import random
from dataclasses import dataclass, field
from typing import List
from game.components.board import PlayerBoard
from game.constraints import *


@dataclass
class GameState:
    """Complete game state"""

    num_players: int
    player_boards: List[PlayerBoard]

    # Factory displays: list of lists of tiles
    factory_displays: List[List[TileColor]] = field(default_factory=list)

    # Center area: tiles moved from factories
    center: List[TileColor] = field(default_factory=list)

    # Tile bag for drawing
    bag: List[TileColor] = field(default_factory=list)

    # Box lid: discarded tiles
    box_lid: List[TileColor] = field(default_factory=list)

    # Game state tracking
    current_player: int = 0
    starting_player: int = 0
    starting_player_marker_taken: bool = False
    round_number: int = 1
    game_ended: bool = False

    def initialize_game(self):
        """Set up initial game state"""
        # Fill bag with tiles
        self.bag = [color for color in TileColor for _ in range(TILES_PER_COLOR)]
        random.shuffle(self.bag)

        # Create factory displays
        num_factories = FACTORY_DISPLAYS[self.num_players]
        self.factory_displays = [[] for _ in range(num_factories)]

        # Fill factories
        self.refill_factories()

        # Starting player has marker
        self.current_player = self.starting_player

    def refill_factories(self):
        """Fill all factory displays with tiles from bag"""
        for factory in self.factory_displays:
            factory.clear()
            for _ in range(TILES_PER_FACTORY):
                if not self.bag:
                    # Refill bag from box lid
                    self.bag = self.box_lid.copy()
                    self.box_lid.clear()
                    random.shuffle(self.bag)

                if self.bag:
                    factory.append(self.bag.pop())
