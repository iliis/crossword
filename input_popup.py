import string
import curses
import logging
from enum import Enum

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

class InputPopup(WidgetBase):

    def __init__(self, app, parent, title, text):

        h, w = parent.getmaxyx()
        parent_size = Vector(w, h)

        self.layout_text = layout_text(text, 80) # max width: 100
        self.height = len(self.layout_text) + 1 # title, text

        self.width = 90

        size = Vector(self.width+4, self.height+4)

        # center in middle of parent
        super(InputPopup, self).__init__(app, parent_size/2-size/2, size)

        self.title = title
        self.app = app
        self.user_input = ""
        self.is_password_input = False

        self.callback = None

    def handle_input(self, key):
        #if   key == curses.KEY_LEFT  or key == curses.KEY_BTAB: self.selected_button -= 1
        #elif key == curses.KEY_RIGHT or key == '\t':       self.selected_button += 1
        if type(key) == str and key in string.ascii_letters + string.digits + 'äöüÄÖÜ ':
            if len(self.user_input) < self.width-1-len(self.layout_text[-1]):
                self.user_input += key
        elif key == curses.KEY_BACKSPACE:
            if len(self.user_input) > 0:
                self.user_input = self.user_input[:-1]
        elif key == curses.KEY_ENTER or key == '\n' or key == '\r':
            self.app.mi.send_packet({
                'command':  'input_popup_closed',
                'user_input': self.user_input,
                'title':    self.title
            })
            if self.callback:
                log.info('Input Popup: calling callback')
                self.callback(self.user_input)
            else:
                log.warn('Popup: no callback defined!')
        else:
            return False

        return True


    def draw(self):
        self.screen.clear()
        self.screen.border()

        # title
        self.screen.addstr(1,2, self.title, curses.A_BOLD)

        # text
        for y, line in enumerate(self.layout_text):
            self.screen.addstr(3+y, 2, line)

        # input
        if self.is_password_input:
            i = "*" * len(self.user_input)
        else:
            i = self.user_input

        self.screen.addstr(2+len(self.layout_text), 2+len(self.layout_text[-1])+1, i)
