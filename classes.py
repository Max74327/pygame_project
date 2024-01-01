import pygame as pg
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

    def can_move_left(self, level):
        if self.coords[0] == 0:
            return False
        return type(level[self.coords[1]][self.coords[0] - 1]) in [Air, Ladder, Rope]

    def move_left(self, level):
        if self.can_move_left(level):
            self.coords = self.coords[0] - 1, self.coords[1]
            self.refresh()

    def can_move_right(self, level):
        if self.coords[0] == len(level) - 1:
            return False
        return type(level[self.coords[1]][self.coords[0] + 1]) in [Air, Ladder, Rope]

    def move_right(self, level):
        if self.can_move_right(level):
            self.coords = self.coords[0] + 1, self.coords[1]
            self.refresh()

    def refresh(self):
        self.rect.x, self.rect.y = self.coords[0] * TILE_WIDTH, self.coords[1] * TILE_WIDTH


class Level:
    tile_codes = {'1': Air, '2': Ladder, '3': Stone}

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
    def __init__(self, level, screen):
        self.level = Level(load_level(f'{level}.txt'))
        self.r = True
        self.screen = screen

    def run(self):
        self.r = True
        background = pg.sprite.Sprite()
        background.image = load_image('background.jpg')
        background.rect = background.image.get_rect()
        all_sprites.add(background)
        camera = Camera()
        clock = pg.time.Clock()
        while self.r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.r = False
                if event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_a]:
                        self.level.player.move_left(self.level.map)
                    if keys[pg.K_d]:
                        self.level.player.move_right(self.level.map)
                    if keys[pg.K_ESCAPE]:
                        self.r = False
            screen.fill((0, 0, 0))
            self.level.update_player()
            camera.update(self.level.player)
            for sprite in all_sprites:
                camera.apply(sprite)
            all_sprites.draw(self.screen)
            self.level.draw(self.screen)
            self.level.player_group.draw(self.screen)
            for sprite in all_sprites:
                camera.undo(sprite)
            pg.display.flip()
            clock.tick(165)


class Button:
    def __init__(self, pos, size, screen, font, text='Button', text_color=(0, 255, 0), border_color=(0, 255, 0), back_color=(0, 0, 0)):
        self.size = size
        self.pos = pos
        self.text = text
        self.screen = screen
        self.font = font
        self.text_size = self.text_width, self.text_height = self.font.size(self.text)
        self.text_color = self.d_t_c = text_color
        self.border_color = self.d_b_c = border_color
        self.back_color = self.d_bg_c = back_color

    def draw(self):
        pg.draw.rect(self.screen, self.back_color, (*self.pos, *self.size))
        text = self.font.render(self.text, False, self.text_color, self.back_color)
        self.screen.blit(text, (self.pos[0] + self.text_width / 4, self.pos[1] + self.text_height / 4))
        pg.draw.rect(self.screen, self.border_color, (*self.pos, *self.size), 5)

    def click(self, pos):
        if self.in_box(pos):
            self.on_click()

    def on_click(self):
        if self.border_color == (0, 255, 0):
            self.border_color = (255, 0, 0)
        else:
            self.border_color = (0, 255, 0)

    def in_box(self, pos):
        return self.pos[0] <= pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= pos[1] <= self.pos[1] + self.size[1]

    def mouse_move(self, pos):
        if self.in_box(pos):
            self.active()
        else:
            self.inactive()

    def active(self):
        self.back_color = self.d_t_c
        self.text_color = self.d_bg_c

    def inactive(self):
        self.text_color = self.d_t_c
        #self.border_color = self.d_b_c
        self.back_color = self.d_bg_c


class PlayButton(Button):
    def __init__(self, pos, size, screen, font, text, text_color, border_color, back_color, win):
        super().__init__(pos, size, screen, font, text, text_color, border_color, back_color)
        self.win = win

    def on_click(self):
        lvl_window = LevelSelectionWindow(self.win.screen)
        lvl_window.run()
        #self.win.r = False
        #lvl = LevelScreen('map', self.win.screen)
        #lvl.run()


class LevelButton(Button):
    def __init__(self, pos, size, screen, font, text, text_color, border_color, back_color, win):
        super().__init__(pos, size, screen, font, text, text_color, border_color, back_color)
        self.win = win

    def on_click(self):
        #self.win.r = False
        lvl = LevelScreen('map', self.win.screen)
        lvl.run()


class SettingsButton(Button):
    def __init__(self, pos, size, screen, font, text, text_color, border_color, back_color, win):
        super().__init__(pos, size, screen, font, text, text_color, border_color, back_color)
        self.win = win

    def on_click(self):
        #self.win.r = False
        settings_menu = SettingsMenu(self.win.screen)
        settings_menu.run()


class LevelSelectionWindow:
    def __init__(self, screen):
        self.screen = screen
        self.level_buttons = list()
        self.current_page = 0
        self.level_count = 20
        self.levels_on_page = 20
        self.level_rows = 4
        self.level_columns = self.levels_on_page // self.level_rows
        self.r = True
        self.load_level_buttons()

    def load_level_buttons(self):
        for y in range(self.level_rows):
            row = list()
            for x in range(self.level_columns):
                y_of = int(0.05 * HEIGHT)
                sz = int((HEIGHT * (0.95 - 0.05 * self.level_rows)) // self.level_rows)
                x_of = int((WIDTH - sz * self.level_columns) // (self.level_columns + 1))
                row.append(LevelButton((x_of + x * (x_of + sz), y_of + y * (y_of + sz)), (sz, sz), self.screen, pg.font.Font(None,  sz), str(y * self.level_columns + x + 1), (175, 220, 55), (77, 100, 17), (75, 75, 75), self))
            self.level_buttons.append(row)

    def run(self):
        self.r = True
        while self.r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.r = False
                if event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_ESCAPE]:
                        self.r = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    if pg.mouse.get_pressed()[0]:
                        for lst in self.level_buttons:
                            for button in lst:
                                button.click(event.pos)
                if event.type == pg.MOUSEMOTION:
                    for lst in self.level_buttons:
                        for button in lst:
                            button.mouse_move(event.pos)
            screen.fill((0, 0, 0))
            for lst in self.level_buttons:
                for button in lst:
                    button.draw()
            pg.display.flip()
            clock.tick(165)


class SettingsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.r = True

    def run(self):
        self.r = True
        while self.r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.r = False
                if event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_ESCAPE]:
                        self.r = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    pass
                if event.type == pg.MOUSEMOTION:
                    pass
            screen.fill((0, 0, 0))
            pg.display.flip()
            clock.tick(165)


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.play_button = PlayButton((WIDTH / 2 - 150, HEIGHT / 2 - 200), (300, 100), self.screen, pg.font.Font(None, 100), 'Play', (0, 255, 0), (0, 255, 0), (0, 0, 0), self)
        self.settings_button = SettingsButton((WIDTH / 2 - 200, HEIGHT / 2), (400, 100), self.screen, pg.font.Font(None, 100), 'Settings', (0, 175, 175), (75, 75, 0), (40, 40, 40), self)
        self.r = True

    def run(self):
        self.r = True
        while self.r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.r = False
                if event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_ESCAPE]:
                        self.r = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    if pg.mouse.get_pressed()[0]:
                        self.play_button.click(event.pos)
                        self.settings_button.click(event.pos)
                if event.type == pg.MOUSEMOTION:
                    self.play_button.mouse_move(event.pos)
                    self.settings_button.mouse_move(event.pos)
            screen.fill((0, 0, 0))
            self.play_button.draw()
            self.settings_button.draw()
            pg.display.flip()
            clock.tick(165)

# level = load_level('map.txt')
# player, level_x, level_y = generate_level(level)
# camera = Camera()
