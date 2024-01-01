from classes import *


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


def wait_for_press():
    for event in pg.event.get():
        if event.type in [pg.MOUSEBUTTONDOWN, pg.KEYDOWN]:
            return False
    return True


def start_screen():
    background = pg.transform.scale(load_image('fon.jpg'), SIZE)
    screen.blit(background, (0, 0))


def wait_screen():
    while wait_for_press():
        start_screen()
        pg.display.flip()


wait_screen()
#lvl = LevelScreen('map', screen)
main_menu = MainMenu(screen)
main_menu.run()
#lvl.run(screen)