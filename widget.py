import npyscreen
import curses
import logging

from helpers import *
log = logging.getLogger('puzzle')

class WidgetBase:

    def __init__(self, pos, size):
        # create new screen for yourself
        self.screen = curses.newwin(size.y, size.x, pos.y, pos.x)

    def size(self):
        h, w = self.screen.getmaxyx()
        return Vector(w, h)

    def pos(self):
        py, px = self.screen.getbegyx()
        return Vector(px, py)

    def resize(self, new_size):
        self.screen.resize(new_size.y, new_size.x)

    def move(self, new_pos):
        self.screen.mvwin(new_pos.y, new_pos.x)

    def draw(self):
        pass

    def render(self):
        self.draw()
        self.screen.noutrefresh() # only update internal framebuffer of curses, actual screen will be updated once after every widget has been rendered
