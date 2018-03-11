import npyscreen
import logging
import json
import curses
import selectors
import sys
import serial

from helpers import *
from crossword import Crossword
from progress_bar import ProgressBar
from management_interface import ManagementInterface
from widget_manager import WidgetManager

log = logging.getLogger('puzzle')
hdlr = logging.FileHandler('puzzle.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)



class Application:
    def __init__(self, screen):
        self.sel = selectors.DefaultSelector()
        self.screen = screen

        #curses.raw() # disable special keys and stuff (such as ctrl-c)
        self.screen.nodelay(True) # disable blocking on getch()
        curses.curs_set(False) # hide cursor
        curses.mousemask(curses.ALL_MOUSE_EVENTS) # enable mouse interaction
        curses.nonl() # don't translate KEY_RETURN into '\r\n'

        self.screen.clear()


        # create server for remote control
        self.mi = ManagementInterface(1234, self.sel)

        self.widget_mgr = WidgetManager(self)

        # register key handler
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.handle_input)

        with open('puzzle.cfg', 'r') as puzzle_cfg:
            cfg = json.load(puzzle_cfg)
            log.info("using configuration: {}".format(cfg))
            h, w = screen.getmaxyx()
            self.puzzle = Crossword(self, Vector(10,1), Vector(w-10, h-2), cfg)
            self.widget_mgr.add(self.puzzle)
            self.widget_mgr.focus = self.puzzle

        self.puzzle.resize_to_contents()

        # center in middle of screen (also take progress bar into account)
        ps = self.puzzle.size()
        self.puzzle.move(Vector(
                int((w-ps.x)/2),
                int((h-ps.y+4)/2)
                ))

        self.progress_bar = ProgressBar(
                self,
                self.puzzle.pos() - Vector(0,4),
                Vector(self.puzzle.size().x, 4),
                'Lösungsfortschritt:')
        self.puzzle.progress_bar = self.progress_bar

        """
        self.widget_mgr.show_popup('Dies ist der Titel',
                "asdfa sfasdfdsaf;dsa kfsa;dkfjdsa;if jsa;ifjsa dfijdsfoisdhaf " +'%'*40+ " uhsaif usahd end of first line\nsecond line here\nand a third " + "#"*250,
                lambda b: log.info('selected {}'.format(b)), ['foo', 'bar', 'baz'])
                """

    def handle_input(self, stdin):
        k = self.screen.getch()
        if k >= 0:
            if k == curses.KEY_F1 or k == curses.KEY_F2:
                self.widget_mgr.show_single_popup('Hilfe',
                        'TODO: Hier sollte wohl etwas Hilfe zum Puzzle (bzw. einfach zur Bedienung) hinkommen.')
            elif k == curses.KEY_F12:
                self.show_about()
            else:
                if not self.widget_mgr.handle_input(k):
                    log.info("unhandled key '{}'".format(k))

    def show_about(self):
        self.widget_mgr.show_single_popup('Kreuzworträtsel',
                """Geschrieben von Samuel Bryner

Diese Software ist frei verfügbar unter der GPL. Quellcode unter
https://github.com/iliis/crossword
""")

    def run(self):
        #ser.write(b'crossword running')

        while True:
            self.widget_mgr.render()
            events = self.sel.select()
            log.info("executing {} events after select".format(len(events)))
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
