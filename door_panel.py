import npyscreen
import curses
import logging

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

DOOR_CNT = 3

class DoorPanel(WidgetBase):

    def __init__(self, app):
        super(DoorPanel, self).__init__(app, Vector(0,0), Vector(59,14))

        curses.init_pair(40, curses.COLOR_RED,   curses.COLOR_BLACK)
        curses.init_pair(41, curses.COLOR_GREEN, curses.COLOR_BLACK)

        curses.init_pair(42, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(43, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.reset()

    def reset(self):
        self.cursor = 0
        self.door_states = [False] * DOOR_CNT

    def handle_input(self, key):
        if   key == curses.KEY_LEFT:  self.cursor -= 1
        elif key == curses.KEY_UP:    self.cursor -= 1
        elif key == curses.KEY_BTAB:  self.cursor -= 1 # shift-tab
        elif key == curses.KEY_RIGHT: self.cursor += 1
        elif key == curses.KEY_DOWN:  self.cursor += 1
        elif key == ord('\t'):        self.cursor += 1 # tab
        elif key == curses.KEY_ENTER or key == ord(' ') or key == ord('\n') or key == ord('\r'):
            self.toggle_door()
        else:
            return False # did not handle key, no need to update screen
        self.cursor %= len(self.door_states)
        return True

    def toggle_door(self):
        state = self.door_states[self.cursor]

        if not state:
            # only confirm if user wants to unlock door
            self.app.widget_mgr.show_single_popup(
                    'Tür {} öffnen?'.format(self.cursor+1),
                    'Wollen Sie Tür {} wirklich öffnen?'.format(self.cursor+1),
                    self.toggle_door_cb,
                    ['JA', 'NEIN'])
        else:
            self.actually_toggle_door()

    def toggle_door_cb(self, answer):
        if answer == 'JA':
            self.actually_toggle_door()

    def actually_toggle_door(self):
        self.door_states[self.cursor] = not self.door_states[self.cursor]

        if self.door_states[self.cursor]:
            self.app.widget_mgr.show_single_popup(
                    'Tür {} wurde geöffnet'.format(self.cursor+1),
                    'Tür {} ist nun offen und nicht mehr abgeschlossen.'.format(self.cursor+1))
        else:
            self.app.widget_mgr.show_single_popup(
                    'Tür {} wurde geschlossen'.format(self.cursor+1),
                    'Tür {} ist erfolgreich abgeschlossen worden.'.format(self.cursor+1))

        self.app.mi.send_packet({
            'event': 'door_changed',
            'doors': self.door_states
        })


    def draw(self):
        #self.screen.clear()
        self.screen.border()

        self.screen.addstr(3, 8,
                'Stadtwache Ankh-Morpork: Türkontrollsystem',
                curses.A_BOLD)

        for i, state in enumerate(self.door_states):
            y = 6 + i*2

            self.screen.addstr(y, 8, 'Tür {}:'.format(i+1))
            self.screen.addstr(y, 16,
                    'offen      ' if state else 'geschlossen',
                    curses.color_pair(41 if state else 40))

            self.screen.addstr(y, 30,
                    '   schliessen   ' if state else '     öffnen     ',
                    curses.A_BOLD | curses.color_pair(43)
                        if i == self.cursor else curses.color_pair(42))
