import curses
import logging

from widget import WidgetBase
from helpers import *

log = logging.getLogger('puzzle')

class Door:
    def __init__(self, can_open=True, can_close=True, opened_title="Door was opened", opened_message="Door was opened", closed_title="Door was closed", closed_message="Door was closed"):
        self.can_open = can_open
        self.can_close = can_close
        self.opened_title   = opened_title
        self.opened_message = opened_message
        self.closed_title   = closed_title
        self.closed_message = closed_message

class DoorPanel(WidgetBase):

    def __init__(self, app):
        super(DoorPanel, self).__init__(app, Vector(0,0), Vector(59,14))

        curses.init_pair(40, curses.COLOR_RED,   curses.COLOR_BLACK)
        curses.init_pair(41, curses.COLOR_GREEN, curses.COLOR_BLACK)

        curses.init_pair(42, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(43, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.doors = [
            Door(can_open=False, can_close=False, opened_title='Tür 1 konnte nicht geöffnet werden', opened_message='Tür 1 konnte wegen unzureichender Berechtigung nicht geöffnet werden.'),
            Door(can_open=False, can_close=False, opened_title='Tür 2 konnte nicht geöffnet werden', opened_message='Tür 2 ist blockiert. Ein Techniker wurde informiert.'),
            Door(can_open=True, can_close=False, opened_title='Tür 3 wurde geöffnet', opened_message='Tür 3 ist nun offen und nicht mehr abgeschlossen.', closed_title='Tür 3 konnte nicht geschlossen werden', closed_message='Ein unerwarteter Ausnahmefehler ist aufgetreten. Die Tür konnte nicht geschlossen werden.'),
        ]

        self.reset()

    def reset(self):
        self.cursor = 0
        self.door_states = [False] * len(self.doors)

    def handle_input(self, key):
        if   key == curses.KEY_LEFT:  self.cursor -= 1
        elif key == curses.KEY_UP:    self.cursor -= 1
        elif key == curses.KEY_BTAB:  self.cursor -= 1 # shift-tab
        elif key == curses.KEY_RIGHT: self.cursor += 1
        elif key == curses.KEY_DOWN:  self.cursor += 1
        elif key == ord('\t'):        self.cursor += 1 # tab
        elif key == curses.KEY_ENTER or key == ' ' or key == '\n' or key == '\r':
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
        if self.door_states[self.cursor]:
            self.app.widget_mgr.show_single_popup(
                    self.doors[self.cursor].closed_title,
                    self.doors[self.cursor].closed_message)
        else:
            self.app.widget_mgr.show_single_popup(
                    self.doors[self.cursor].opened_title,
                    self.doors[self.cursor].opened_message)

        # only toggle a change if the door was not locked
        if (self.door_states[self.cursor] and self.doors[self.cursor].can_close) \
            or (not self.door_states[self.cursor] and self.doors[self.cursor].can_open):
            self.door_states[self.cursor] = not self.door_states[self.cursor]

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
