from tile_classes import *
import pygame
import random
size = width, height = 1000, 750


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Level:
    def __init__(self, sprites, level_data):
        self.board = Board(level_data[0], level_data[1], sprites[0], level_data[9:])
        self.hp = level_data[2]
        self.treasure = level_data[3]


class Board:
    def __init__(self, width, height, sprite, board_data):
        self.width = width
        self.height = height
        self.board = board_data
        self.left = 10
        self.top = 10
        self.cell_size = 30

    def set_view(self, cell_size, left=None, top=None):
        if not left is None:
            self.left = left
        if not top is None:
            self.top = top
        self.cell_size = cell_size

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                x_cell = self.left + x * self.cell_size
                y_cell = self.top + y * self.cell_size
                pygame.draw.rect(screen, pygame.Color(127, 127, 127), (x_cell, y_cell, self.cell_size, self.cell_size), 0)
                pygame.draw.rect(screen, (255, 255, 255), (x_cell, y_cell, self.cell_size, self.cell_size), 1)

    def get_cell(self, mouse_pos):
        cell_x = (mouse_pos[0] - self.left) // self.cell_size
        cell_y = (mouse_pos[1] - self.top) // self.cell_size
        if cell_x < 0 or cell_x > self.width or cell_y < 0 or cell_y > self.height:
            return None
        return cell_x, cell_y

    def on_click(self, cell):
        pass

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)


class Entity:
    def __init__(self, name, coords, sprites, hp= 100):
        self.coords = coords
        self.name = name
        self.hp = hp
        self.sprites = sprites

    def move(self, coords):
        self.coords = coords


class Hero(Entity):
    def __init__(self):
        super().__init__()
