import pygame

from game.components.gameState import GameState


class BaseUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Azul")

    def draw(self, game_state: GameState):
        self.screen.fill((255, 255, 255))
        pygame.display.flip()

    def handle_event(self, event):
        pass

    def run(self, game_state: GameState):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)
            self.draw(game_state)
        pygame.quit()


if __name__ == "__main__":
    pygame.init()
    game_state = GameState(num_players=2, player_boards=[])
    ui = BaseUI()
    ui.run(game_state)
