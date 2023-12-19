import os
import time
TIMER_DELAY = 10


class Tile:
    def __init__(self, sprite, is_top_solid=False, is_side_solid=False):
        self.data = is_top_solid, is_side_solid, sprite

    def get_top(self):
        return self.data[0]

    def get_side(self):
        return self.data[1]


    def get_sprite(self):
        return self.data[2]


class Air(Tile):
    def __init__(self, have_treasure=False):
        super().__init__(sprite)
        self.treasure = have_treasure

    def have_treasure(self):
        return self.treasure

    def take_treasure(self):
        self.treasure = False


class Ladder(Tile):
    def __init__(self):
        super().__init__(sprite, is_top_solid=True)


class Stone(Tile):
    def __init__(self, is_digable=True):
        super().__init__(sprite, is_top_solid=True, is_side_solid=True)
        self.digable = is_digable
        self.dig_data = 0

    def is_digable(self):
        self.digable and not self.dig_data

    def dig(self):
        if self.is_digable():
            self.dig_data = time.time() + TIMER_DELAY