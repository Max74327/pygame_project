import pygame as pg
from pprint import pprint
import os
import sys
import time

TIMER_DELAY = 10

# from teste_classes_maintenance import tile_group, entity_group
# from test1 import SIZE, WIDTH, HEIGHT
all_sprites = pg.sprite.Group()
tiles_group = pg.sprite.Group()
player_group = pg.sprite.Group()
entity_group = pg.sprite.Group()
TILE_WIDTH = 30
SIZE = WIDTH, HEIGHT = 1600, 900  # 1920, 1080
FPS = 60  # 165
pg.init()
screen = pg.display.set_mode(SIZE)
run = True
clock = pg.time.Clock()
player = None


def load_image(name, colorkey=None):
    path = os.path.join('data', name)
    if not os.path.isfile(path):
        sys.exit()
    image = pg.image.load(path)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pg.quit()
    sys.exit()


def start_screen():
    background = pg.transform.scale(load_image('fon.jpg'), SIZE)
    screen.blit(background, (0, 0))


def load_level(name):
    path = 'data/' + name
    with open(path, 'r') as f:
        level_map = [line.strip() for line in f]
    max_width = max(map(len, level_map))
    pprint(list(map(lambda x: x.ljust(max_width, '.'), level_map)))

    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def wait_for_press():
    for event in pg.event.get():
        if event.type in [pg.MOUSEBUTTONDOWN, pg.KEYDOWN]:
            return False
    return True


class Camera:
    def __init__(self, mode=None):
        self.dx = 0
        self.dy = 0
        self.mode = mode

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def undo(self, obj):
        obj.rect.x -= self.dx
        obj.rect.y -= self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)
        if self.mode is not None and self.mode == 0:
            self.dy = 0
        elif self.mode is not None and self.mode == 1:
            self.dx = 0


class Tile(pg.sprite.Sprite):
    def __init__(self, coords, is_top_solid=False, is_side_solid=False):
        super().__init__(all_sprites, tiles_group)
        self.data = is_top_solid, is_side_solid
        self.width = TILE_WIDTH
        self.coords = coords

    def get_top(self) -> bool:
        return self.data[0]

    def get_side(self) -> bool:
        return self.data[1]

    # def get_sprite(self) :
    #    return self.data[2]


class Air(Tile):
    # sprite = create_sprite('air.png')
    def __init__(self, coords, have_treasure=False, treasure=None):
        super().__init__(coords)
        self.treasure = have_treasure
        self.image = load_image('air.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)

    def have_treasure(self):
        return self.treasure

    def take_treasure(self):
        self.treasure = False


class Ladder(Tile):
    # sprite = create_sprite('ladder.png')

    def __init__(self, coords):
        super().__init__(coords, is_top_solid=True)
        self.image = load_image('ladder.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)


class Rope():
    pass


class Stone(Tile):
    # sprite = create_sprite('stone.png')

    def __init__(self, coords, is_digable=True):
        super().__init__(coords, is_top_solid=True, is_side_solid=True)
        self.image = load_image('stone.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)
        self.digable = is_digable
        self.dig_data = 0

    def is_digable(self):
        return self.digable and not self.dig_data

    def dig(self):
        if self.is_digable():
            self.dig_data = time.time() + TIMER_DELAY


class Item(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

    def take(self):
        pass


class Entity(pg.sprite.Sprite):
    def __init__(self, name, coords):
        super().__init__(all_sprites, entity_group)
        self.coords = coords
        self.name = name

    def move(self, coords):
        self.coords = coords


class Hero(Entity):
    # sprite = create_sprite('hero.png')
    def __init__(self, coords):
        super().__init__("Hero", coords)  # , (Hero.sprite,))
        self.image = load_image('hero.png')
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.refresh()

    def fall(self, level):
        if type(level[self.coords[1]][self.coords[0]]) in [Ladder, Rope]:
            return
        if len(level) > self.coords[1] + 1 and type(level[self.coords[1] + 1][self.coords[0]]) in [Air, Rope]:
            self.coords = self.coords[0], self.coords[1] + 1
            self.fall(level)

    def can_move_left(self, level):
        if self.coords[0] == 0:
            return False
        return type(level[self.coords[1]][self.coords[0] - 1]) in [Air, Ladder, Rope]

    def can_move_up(self, level):
        if self.coords[1] == 0:
            return False
        return type(level[self.coords[1]][self.coords[0]]) == Ladder

    def move_up(self, level):
        if self.can_move_up(level):
            self.coords = self.coords[0], self.coords[1] - 1
            self.refresh(level)

    def move_left(self, level):
        if self.can_move_left(level):
            self.coords = self.coords[0] - 1, self.coords[1]
            self.refresh(level)

    def can_move_right(self, level):
        if self.coords[0] == len(level) - 1:
            return False
        return type(level[self.coords[1]][self.coords[0] + 1]) in [Air, Ladder, Rope]

    def move_right(self, level):
        if self.can_move_right(level):
            self.coords = self.coords[0] + 1, self.coords[1]
            self.refresh(level)

    def can_move_down(self, level):
        if self.coords[1] == len(level) - 1:
            return False
        return type(level[self.coords[1] + 1][self.coords[0]]) in [Ladder, Rope, Air] and type(
            level[self.coords[1]][self.coords[0]]) in [Air, Ladder, Rope]

    def move_down(self, level):
        if self.can_move_down(level):
            self.coords = self.coords[0], self.coords[1] + 1
            self.refresh(level)

    def refresh(self, level=None):
        if level is not None:
            self.fall(level)
        self.rect.x, self.rect.y = self.coords[0] * TILE_WIDTH, self.coords[1] * TILE_WIDTH


class Level:
    tile_codes = {'1': Air, '2': Ladder, '3': Stone, '4': Rope}

    def __init__(self, level):
        self.size = self.width, self.height = len(level[0]), len(level)
        self.level = level
        self.map = [[0 for j in range(len(level))] for i in range(len(level[0]))]
        self.draw_group = pg.sprite.Group()
        self.player = Hero((0, 0))
        self.player_group = pg.sprite.Group()
        self.player_group.add(self.player)
        self.generate_level()

    def generate_level(self):
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.level[y][x] == '@':
                    self.map[y][x] = Air((x, y))
                    self.player.move((x, y))
                    self.player.refresh()
                else:
                    self.map[y][x] = self.tile_codes[self.level[y][x]]((x, y))
                self.draw_group.add(self.map[y][x])

    def draw(self, surface):
        self.draw_group.draw(surface)

    def draw_player(self, surface):
        surface.blit(self.player.image, (self.player.coords[0] * TILE_WIDTH, self.player.coords[1] * TILE_WIDTH))

    def update_player(self):
        self.player.refresh()


def wait_screen():
    while wait_for_press():
        start_screen()
        pg.display.flip()


class LevelScreen:
    def __init__(self, level):
        self.level = Level(load_level(f'{level}.txt'))

    def run(self, screen):
        r = True
        background = pg.sprite.Sprite()
        background.image = load_image('background.jpg')
        background.rect = background.image.get_rect()
        all_sprites.add(background)
        camera = Camera()
        clock = pg.time.Clock()
        while r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    r = False
                if event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_a] or keys[pg.K_LEFT]:
                        self.level.player.move_left(self.level.map)
                    if keys[pg.K_d] or keys[pg.K_RIGHT]:
                        self.level.player.move_right(self.level.map)
                    if keys[pg.K_w] or keys[pg.K_UP]:
                        self.level.player.move_up(self.level.map)
                    if keys[pg.K_s] or keys[pg.K_DOWN]:
                        self.level.player.move_down(self.level.map)
                    if keys[pg.K_ESCAPE]:
                        r = False
            screen.fill((0, 0, 0))
            self.level.update_player()
            camera.update(self.level.player)
            for sprite in all_sprites:
                camera.apply(sprite)
            all_sprites.draw(screen)
            self.level.draw(screen)
            self.level.player_group.draw(screen)
            for sprite in all_sprites:
                camera.undo(sprite)
            pg.display.flip()
            clock.tick(165)

# level = load_level('map.txt')
# player, level_x, level_y = generate_level(level)
# camera = Camera()
