import curses
import logging

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

class FinalScreen(WidgetBase):

    def __init__(self, app):

        h, w = app.screen.getmaxyx()
        parent_size = Vector(w, h)

        size = Vector(16, 1)

        # center in middle of parent
        super(FinalScreen, self).__init__(app, parent_size/2-size/2, size)

    def draw(self):
        self.screen.addstr(0,0, "T H E   E N D", curses.A_BOLD)
