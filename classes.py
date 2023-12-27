import pygame
import os
import time
import sys
TIMER_DELAY = 10
size = width, height = 1000, 750


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def create_sprite(name, sprite_size=None):
    img = load_image(name)
    if sprite_size is None:
        sprite_size = img.get_width()
    img = pygame.transform.scale(img, (sprite_size, sprite_size))
    sprite = pygame.Surface((sprite_size, sprite_size), pygame.HWSURFACE)
    sprite.blit(img, (0, 0))
    return sprite


class Tile:
    def __init__(self, sprite, is_top_solid=False, is_side_solid=False):
        self.data = is_top_solid, is_side_solid, sprite

    def get_top(self) -> bool:
        return self.data[0]

    def get_side(self) -> bool:
        return self.data[1]

    def get_sprite(self) :
        return self.data[2]


class Air(Tile):
    sprite = create_sprite('air.png')

    def __init__(self, have_treasure=False, treasure=None):
        super().__init__(Air.sprite)
        self.treasure = have_treasure

    def have_treasure(self):
        return self.treasure

    def take_treasure(self):
        self.treasure = False


class Ladder(Tile):
    sprite = create_sprite('ladder.png')

    def __init__(self):
        super().__init__(Ladder.sprite, is_top_solid=True)


class Rope():
    pass


class Stone(Tile):
    sprite = create_sprite('stone.png')

    def __init__(self, is_digable=True):
        super().__init__(Stone.sprite, is_top_solid=True, is_side_solid=True)
        self.digable = is_digable
        self.dig_data = 0

    def is_digable(self):
        return self.digable and not self.dig_data

    def dig(self):
        if self.is_digable():
            self.dig_data = time.time() + TIMER_DELAY


class Item:
    def __init__(self, sprite):
        self.sprite = sprite

    def take(self):
        pass


class Board:
    def __init__(self, width, height, sprite, treasure_amount, board_data):
        self.sprite = sprite
        self.width = width
        self.height = height
        self.treasure_amount = treasure_amount
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
    def __init__(self, name, coords, sprites):
        self.coords = coords
        self.name = name
        self.sprites = sprites

    def move(self, coords):
        self.coords = coords


class Hero(Entity):
    sprite = create_sprite('hero.png')
    def __init__(self):
        super().__init__("Hero", (0, 0), (Hero.sprite,))