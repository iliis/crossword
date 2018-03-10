import npyscreen
import curses
import logging

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

BAR_FULL  = '█'
BAR_EMPTY = '░' # ▒ ▓

class ProgressBar(WidgetBase):

    def __init__(self, app, pos, size, label):
        super(ProgressBar, self).__init__(app, pos, size)
        self.progress = 0 # 0 - 1
        self.label = label

    def set_progress(self, fraction):
        self.progress = fraction

    def draw(self):
        #self.screen.clear()
        self.screen.border()

        ph, pw = self.screen.getmaxyx()

        # label
        self.screen.addstr(1,2, self.label, curses.A_BOLD)

        # percentage text
        p_text = "{:3.0f}%".format(self.progress*100)
        self.screen.addstr(1, pw-len(p_text)-2, p_text, curses.A_BOLD)

        # progress bar
        bar_width = pw - 4
        s = round(self.progress * bar_width)
        bar = BAR_FULL * s + BAR_EMPTY * (bar_width-s)
        self.screen.addstr(2, 2, bar)
