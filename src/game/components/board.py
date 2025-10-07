import enum
from dataclasses import dataclass, field
from typing import List, Optional
from game.constraints import *


@dataclass
class PlayerBoard:
    """Represents a single player's board"""

    player_id: int

    # Pattern lines: list of lists, pattern_lines[i] holds up to (i+1) tiles
    pattern_lines: List[List[Optional[TileColor]]] = field(
        default_factory=lambda: [
            [None] * 1,
            [None] * 2,
            [None] * 3,
            [None] * 4,
            [None] * 5,
        ]
    )

    # Wall: 5x5 grid, True if tile is placed
    wall: List[List[bool]] = field(
        default_factory=lambda: [[False] * 5 for _ in range(5)]
    )

    # Floor line: list of tiles (can include starting player marker)
    floor_line: List[Optional[TileColor]] = field(default_factory=list)

    score: int = 0

    def get_wall_column_for_color(self, row: int, color: TileColor) -> int:
        """Get the column position where a color should be placed in a row"""
        return COLORED_WALL_PATTERN[row].index(color)

    def can_place_color_in_pattern_line(self, row: int, color: TileColor) -> bool:
        """Check if a color can be placed in a specific pattern line"""
        # Check if pattern line already has tiles
        if any(self.pattern_lines[row]):
            existing_color = next(
                tile for tile in self.pattern_lines[row] if tile is not None
            )
            if existing_color != color:
                return False

        # Check if wall already has this color in the corresponding row
        col = self.get_wall_column_for_color(row, color)
        if self.wall[row][col]:
            return False

        return True

    def is_pattern_line_complete(self, row: int) -> bool:
        """Check if a pattern line is completely filled"""
        return all(tile is not None for tile in self.pattern_lines[row])

    def has_completed_horizontal_line(self) -> bool:
        """Check if any horizontal wall line is complete"""
        return any(all(row) for row in self.wall)
