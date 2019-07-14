import curses
import logging
from enum import Enum

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

DEFAULT_BUTTON_WIDTH = 20

class Popup(WidgetBase):

    def __init__(self, app, parent, title, text, buttons=['OK']):
        assert len(buttons) > 0

        self.button_w = DEFAULT_BUTTON_WIDTH

        desired_width = min(100, app.get_screen_width()) # max 100 cols wide, but not bigger than screen can handle

        self.text = text
        self.layout_text = layout_text(text, desired_width-4)
        self.height = len(self.layout_text) + 2 # title, buttons

        # set size according to contents of popup
        self.width = max(max(len(l) for l in self.layout_text), len(buttons)*(self.button_w+1))

        if self.width+4 > app.get_screen_width():
            log.warning("Popup is too wide, trying to reduce button size so it fits.")

            # don't make buttons arbitrarily small
            self.button_w = max(8, int((app.get_screen_width()-4)/len(buttons))-1)
            self.width = max(max(len(l) for l in self.layout_text), len(buttons)*(self.button_w+1))

            log.debug("New button width: {}. Total popup width: {}.".format(self.button_w, self.width+4))

            if self.width+4 > app.get_screen_width():
                raise Exception("Failed to reduce popup size to acceptable width. Too many/big buttons?")

        size = Vector(self.width+4, self.height+4)

        """
        log.info("creating popup with title '{}'".format(title))
        log.info("layouted text: '{}'".format(self.layout_text))
        log.info("parent size: {}".format(parent_size))
        log.info("own size: {}".format(size))
        log.info("pos: {}".format(parent_size/2-size/2))
        log.info("button len: {} {}".format(len(buttons), button_w))
        log.info("max line len: {}".format(max(len(l)for l in self.layout_text)))
        """

        super(Popup, self).__init__(app, Vector(0,0), size)
        self.center_in(parent)

        self.title = title
        self.app = app
        self.buttons = buttons
        self.selected_button = 0

        curses.init_pair(30, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(31, curses.COLOR_WHITE, curses.COLOR_RED)
        self.col_unselected = 30
        self.col_selected   = 31

        self.callback = None

    def handle_input(self, key):
        if   key == curses.KEY_LEFT  or key == curses.KEY_BTAB: self.selected_button -= 1
        elif key == curses.KEY_RIGHT or key == '\t':       self.selected_button += 1
        elif key == curses.KEY_ENTER or key == ' ' or key == '\n' or key == '\r':
            self.app.mi.send_packet({
                'event':  'popup_closed',
                'button': str(self.buttons[self.selected_button]),
                'title':  self.title
            })
            if self.callback:
                log.info('Popup: calling callback')
                self.callback(self.buttons[self.selected_button])
                return True
            else:
                log.warn('Popup: no callback defined!')
        else:
            return False

        self.selected_button %= len(self.buttons)
        return True


    def draw(self):
        #self.screen.clear() # everything gets painted over anyways
        self.screen.border()

        # title
        self.screen.addstr(1,2, self.title, curses.A_BOLD)

        # text
        for y, line in enumerate(self.layout_text):
            self.screen.addstr(3+y, 2, line)

        # buttons
        for i, button in enumerate(self.buttons):
            attr = curses.A_BOLD | curses.color_pair(self.col_selected if i == self.selected_button else self.col_unselected)
            self.screen.addstr(self.height+2,
                    self.width+3 - (self.button_w+1)*(len(self.buttons) - i),
                    "{text:^{width}}".format(text=button, width=self.button_w), attr)
