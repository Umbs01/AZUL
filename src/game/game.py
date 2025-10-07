from game.components.gameState import GameState
from components.board import PlayerBoard
from constraints import *
from typing import List


class Game:

    def __init__(self, num_players: bool = False):
        self.state = GameState(
            num_players=num_players,
            player_boards=[PlayerBoard(i) for i in range(num_players)],
        )
        self.state.initialize_game()

    def get_legal_moves(self, player_id: int) -> List[Move]:
        """Generate all legal moves for current player"""
        pass

    def execute_move(self, move: Move) -> None:
        """Execute a move and update game state"""
        pass

    def is_factory_offer_complete(self) -> bool:
        """Check if Factory Offer phase is done"""
        pass

    def wall_tiling_phase(self) -> None:
        """Execute wall tiling for all players"""
        pass

    def _wall_tile_for_player(self, board: PlayerBoard) -> None:
        """Execute wall tiling for one player"""
        pass

    def _calculate_tile_score(self, board: PlayerBoard, row: int, col: int) -> int:
        """Calculate points for placing a tile on the wall"""
        pass

    def calculate_end_game_bonus(self, board: PlayerBoard) -> int:
        """Calculate end game bonuses"""
        pass

    def check_game_end(self) -> bool:
        """Check if game should end"""
        pass

    def get_winner(self) -> int:
        """Determine winner (returns player_id)"""
        pass
