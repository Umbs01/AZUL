import pygame
from game.gameState import GameState


class Game:
    def __init__(self):
        # init
        pygame.display.set_caption("AZUL")
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.last_tick = pygame.time.get_ticks()

        self.game_state = GameState()
        self.entities = pygame.sprite.Group()
        self.clock_tick = 60

        while True:
            self.loop()

    def loop(self):
        self.eventLoop()
        self.tick()
        self.draw()
        pygame.display.update()

    def eventLoop(self):
        pass

    def tick(self):
        pass

    def draw(self):
        pass
