import curses
import logging

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

class FinalScreen(WidgetBase):

    def __init__(self, app):

        h, w = app.screen.getmaxyx()
        self.parent_size = Vector(w, h)


        # center in middle of parent
        #super(FinalScreen, self).__init__(app, parent_size/2-size/2, size)

        # make full screen
        super(FinalScreen, self).__init__(app, Vector(0,0), self.parent_size)

    def handle_input(self, key):
        if is_enter_key(key):
            self.app.show_static_crossword()
            return True

        return False

    def draw(self):
        self.screen.clear()

        size = Vector(16, 1)
        pos = self.parent_size/2 - size/2

        self.screen.addstr(int(pos.y), int(pos.x), "T H E   E N D", curses.A_BOLD)

        self.screen.addstr(self.parent_size.y-1, 0, "drücke ENTER um Kreuzworträtsel anzuzeigen")
