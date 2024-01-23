import pygame as pg
import os
import sys
import time
import queue
TIMER_DELAY = 10
ENEMY_DELAY = 4

# from teste_classes_maintenance import tile_group, entity_group
# from test1 import SIZE, WIDTH, HEIGHT
all_sprites = pg.sprite.Group()
tiles_group = pg.sprite.Group()
player_group = pg.sprite.Group()
entity_group = pg.sprite.Group()
TILE_WIDTH = 30
MIN_TILE_SIZE = 30
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


def load_level(name, camera=None):
    global TILE_WIDTH
    path = 'data/' + name
    with open(path, 'r') as f:
        level_map = [line.strip() for line in f]
    max_width = max(map(len, level_map))
    width, height = max_width, len(level_map)
    TILE_WIDTH = max(MIN_TILE_SIZE, min(WIDTH // width, HEIGHT // height))
    if camera is not None:
        if TILE_WIDTH * width <= WIDTH:
            camera.mode = 1
            if TILE_WIDTH * height <= HEIGHT:
                camera.mode = -1
        elif TILE_WIDTH * height <= HEIGHT:
            camera.mode = 0
        else:
            camera.mode = None
        #print(camera.mode)
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
        if self.mode is not None and self.mode == 0 or self.mode == -1:
            self.dy = 0
        if self.mode is not None and self.mode == 1 or self.mode == -1:
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

    def stepped_on(self, level):
        pass

    # def get_sprite(self) :
    #    return self.data[2]


class Air(Tile):
    # sprite = create_sprite('air.png')
    def __init__(self, coords):
        super().__init__(coords)
        self.image = load_image('air.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)


class Exit(Tile):

    def __init__(self, coords):
        super().__init__(coords)
        self.image = load_image('mar.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)

    def stepped_on(self, level):
        if level.exit_active:
            level.end(True)


class Ladder(Tile):
    # sprite = create_sprite('ladder.png')

    def __init__(self, coords):
        super().__init__(coords, is_top_solid=True)
        self.image = load_image('ladder.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)


class Rope(Tile):
    # sprite = create_sprite('rope.png')

    def __init__(self, coords):
        super().__init__(coords)
        self.image = load_image('grass.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)


class Stone(Tile):
    # sprite = create_sprite('stone.png')

    def __init__(self, coords):
        super().__init__(coords, is_top_solid=True, is_side_solid=True)
        self.image = load_image('stone.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)
        self.dig_data = 0


class Treasure(Tile):
    # sprite = create_sprite('treasure.png')

    def __init__(self, coords):
        super().__init__(coords)
        self.image = load_image('treasure.png', -1)
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)

    def stepped_on(self, level):
        level.treasure -= 1
        level.map[self.coords[1]][self.coords[0]] = Air(self.coords)
        self.image = load_image('air.png', -1)


class Entity(pg.sprite.Sprite):
    def __init__(self, name, coords):
        super().__init__(all_sprites, entity_group)
        self.coords = coords
        self.name = name

    def move(self, coords):
        self.coords = coords

    def fall(self, level):
        if type(level.map[self.coords[1]][self.coords[0]]) in [Ladder, Rope]:
            return
        if len(level.map) > self.coords[1] + 1 and not level.map[self.coords[1] + 1][self.coords[0]].get_top():
            self.coords = self.coords[0], self.coords[1] + 1
            self.fall(level)

    def can_move_left(self, level):
        if self.coords[0] == 0:
            return False
        return not level.map[self.coords[1]][self.coords[0] - 1].get_side()

    def can_move_up(self, level):
        if self.coords[1] == 0:
            return False
        return type(level.map[self.coords[1]][self.coords[0]]) == Ladder and type(level.map[self.coords[1] - 1][self.coords[0]]) != Stone

    def move_up(self, level):
        if self.can_move_up(level):
            self.coords = self.coords[0], self.coords[1] - 1
            self.refresh(level)

    def move_left(self, level):
        if self.can_move_left(level):
            self.coords = self.coords[0] - 1, self.coords[1]
            self.refresh(level)

    def can_move_right(self, level):
        if self.coords[0] == len(level.map[0]) - 1:
            return False
        return not level.map[self.coords[1]][self.coords[0] + 1].get_side()

    def move_right(self, level):
        if self.can_move_right(level):
            self.coords = self.coords[0] + 1, self.coords[1]
            self.refresh(level)

    def can_move_down(self, level):
        if self.coords[1] == len(level.map) - 1:
            return False
        return not level.map[self.coords[1] + 1][self.coords[0]].get_top() or type(level.map[self.coords[1] + 1][self.coords[0]]) is Ladder

    def move_down(self, level):
        if self.can_move_down(level):
            self.coords = self.coords[0], self.coords[1] + 1
            self.refresh(level)

    def mouse_motion(self, coords, level, camera=None):
        if camera is not None:
            coords = coords[0] - camera.dx, coords[1] - camera.dy
        if coords[1] > self.rect.bottom:
            self.move_down(level)
        elif coords[1] < self.rect.top:
            self.move_up(level)
        if coords[0] > self.rect.right:
            self.move_right(level)
        elif coords[0] < self.rect.left:
            self.move_left(level)

    def refresh(self, level=None):
        if level is not None:
            self.fall(level)
        self.rect.x, self.rect.y = self.coords[0] * TILE_WIDTH, self.coords[1] * TILE_WIDTH


class Hero(Entity):
    # sprite = create_sprite('hero.png')
    def __init__(self, coords):
        super().__init__("Hero", coords)  # , (Hero.sprite,))
        self.image = load_image('hero.png')
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.refresh()

    def fall(self, level):
        if type(level.map[self.coords[1]][self.coords[0]]) in [Ladder, Rope]:
            return
        if len(level.map) > self.coords[1] + 1 and not level.map[self.coords[1] + 1][self.coords[0]].get_top():
            self.coords = self.coords[0], self.coords[1] + 1
            level.map[self.coords[1]][self.coords[0]].stepped_on(level)
            self.fall(level)

    def refresh(self, level=None):
        if level is not None:
            level.map[self.coords[1]][self.coords[0]].stepped_on(level)
            self.fall(level)
        self.rect.x, self.rect.y = self.coords[0] * TILE_WIDTH, self.coords[1] * TILE_WIDTH


class Enemy(Entity):
    def __init__(self, coords):
        super().__init__("Enemy", coords)
        self.image = load_image('Enemy.png')
        self.image = pg.transform.scale(self.image, (TILE_WIDTH, TILE_WIDTH))
        self.rect = self.image.get_rect()
        self.rect.move_ip(coords[0] * TILE_WIDTH, coords[1] * TILE_WIDTH)
        self.q = queue.Queue()
        for _ in range(ENEMY_DELAY):
            self.q.put(coords)

    def en_move(self, coords, level):
        self.q.put(coords)
        self.mouse_motion(self.q.get(), level)
        if self.coords == level.player.coords:
            level.end(False)


class Level:
    tile_codes = {'1': Air, '2': Ladder, '3': Stone, '4': Rope, '5': Treasure, 'e': Exit}

    def __init__(self, sender, level):
        self.sender = sender
        self.enemys = []
        self.size = self.width, self.height = len(level[0]), len(level)
        self.level = level
        self.exit_active = False
        self.treasure = 0
        self.map = [[0 for j in range(len(level[0]))] for i in range(len(level))]
        self.draw_group = pg.sprite.Group()
        self.player = Hero((0, 0))
        self.player_group = pg.sprite.Group()
        self.player_group.add(self.player)
        self.enemy_group = pg.sprite.Group()
        self.generate_level()

    def generate_level(self):
        for y in range(len(self.level)):
            for x in range(len(self.level[y])):
                if self.level[y][x] == '@':
                    self.map[y][x] = Air((x, y))
                    self.player.move((x, y))
                    self.player.refresh()
                elif self.level[y][x] == 'e':
                    self.map[y][x] = Exit((x, y))
                elif self.level[y][x] == 'E':
                    self.map[y][x] = Air((x, y))
                    self.enemys.append(Enemy((x, y)))
                    self.enemy_group.add(self.enemys[-1])
                elif self.level[y][x] == '5':
                    self.treasure += 1
                    self.map[y][x] = Treasure((x, y))
                else:
                    self.map[y][x] = self.tile_codes[self.level[y][x]]((x, y))
                self.draw_group.add(self.map[y][x])

    def draw(self, surface):
        self.draw_group.draw(surface)

    def draw_player(self, surface):
        surface.blit(self.player.image, (self.player.coords[0] * TILE_WIDTH, self.player.coords[1] * TILE_WIDTH))

    def update_player(self):
        self.player.refresh()

    def end(self, is_won:bool):
        self.sender.end(is_won)


def wait_screen():
    while wait_for_press():
        start_screen()
        pg.display.flip()


class LevelScreen:
    def __init__(self, level, screen):
        self.camera = Camera()
        self.level = Level(self, load_level(f'{level}.txt', camera=self.camera))
        self.r = True
        self.screen = screen
        self.level.player.refresh(level=self.level)
        self.controls = None
        with open('data/settings.txt', 'r') as f:
            self.controls = [eval(i) for i in f.readlines()]
        print(self.controls)

    def end(self, is_won:bool):
        self.r = False

    def run(self):
        self.r = True
        background = pg.sprite.Sprite()
        background.image = load_image('background.jpg')
        background.rect = background.image.get_rect()
        all_sprites.add(background)
        clock = pg.time.Clock()
        while self.r:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.r = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    if pg.mouse.get_pressed()[0]:
                        self.level.player.mouse_motion(event.pos, self.level, self.camera)
                        for enemy in self.level.enemys:
                            enemy.en_move(self.level.player.coords, self.level)
                elif event.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if any(keys[i] for i in self.controls[2]):  # keys[pg.K_a] or keys[pg.K_LEFT]:
                        self.level.player.move_left(self.level)
                    if any(keys[i] for i in self.controls[3]):  # keys[pg.K_d] or keys[pg.K_RIGHT]:
                        self.level.player.move_right(self.level)
                    if any(keys[i] for i in self.controls[0]):  # keys[pg.K_w] or keys[pg.K_UP]:
                        self.level.player.move_up(self.level)
                    if any(keys[i] for i in self.controls[1]):  # keys[pg.K_s] or keys[pg.K_DOWN]:
                        self.level.player.move_down(self.level)
                    if keys[pg.K_ESCAPE]:
                        self.r = False
                    else:
                        continue
                    for enemy in self.level.enemys:
                        enemy.en_move(self.level)
            screen.fill((0, 0, 0))
            if self.level.treasure == 0:
                self.level.exit_active = True
            self.level.update_player()
            self.camera.update(self.level.player)
            for sprite in all_sprites:
                self.camera.apply(sprite)
            self.camera.undo(background)
            all_sprites.draw(self.screen)
            self.level.draw(self.screen)
            self.level.player_group.draw(self.screen)
            self.level.enemy_group.draw(self.screen)
            for sprite in all_sprites:
                self.camera.undo(sprite)
            self.camera.apply(background)
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
    def __init__(self, pos, size, screen, font, text, text_color, border_color, back_color, win, level):
        super().__init__(pos, size, screen, font, text, text_color, border_color, back_color)
        self.win = win
        self.level = level

    def on_click(self):
        #self.win.r = False
        lvl = LevelScreen(self.level, self.win.screen)
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
                row.append(LevelButton((x_of + x * (x_of + sz), y_of + y * (y_of + sz)), (sz, sz), self.screen, pg.font.Font(None,  sz), str(y * self.level_columns + x + 1), (175, 220, 55), (77, 100, 17), (75, 75, 75), self, str(y * self.level_columns + x + 1)))
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
        self.button_up_change = None
        print(pg.key.name(1073741906))

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
