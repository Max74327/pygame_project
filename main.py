import pygame
from classes import *


def main():
    pygame.init()
    screen = pygame.display.set_mode(size)
    # поле 5 на 7
    board = Board(25, 25)
    board.set_view(cell_size=30, left=0, top=0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos)
        screen.fill((25, 25, 25))
        board.render(screen)
        pygame.display.flip()


main()