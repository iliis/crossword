import npyscreen
import curses
import logging

from helpers import *
log = logging.getLogger('puzzle')

class WidgetBase:

    def __init__(self, app, pos, size):
        self.app = app
        # create new screen for yourself
        self.screen = curses.newwin(int(size.y), int(size.x), int(pos.y), int(pos.x))
        self.visible = True

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
        # implement this in your derived class
        pass

    def render(self):
        if self.visible:
            self.draw()
            self.screen.noutrefresh() # only update internal framebuffer of curses, actual screen will be updated once after every widget has been rendered
