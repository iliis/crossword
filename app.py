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

        self.is_running = False

        #curses.raw() # disable special keys and stuff (such as ctrl-c)
        self.screen.nodelay(True) # disable blocking on getch()
        curses.curs_set(False) # hide cursor
        curses.mousemask(curses.ALL_MOUSE_EVENTS) # enable mouse interaction
        curses.nonl() # don't translate KEY_RETURN into '\r\n'

        self.screen.clear()

        # create server for remote control
        self.mi = ManagementInterface(1234, self.sel)
        log.info("local address: {}".format(self.mi.get_local_addresses()))

        self.mi.register_handler('quit', self.exit_app_by_packet)
        self.mi.register_handler('show_popup', self.show_popup_from_packet)
        self.mi.register_handler('ping', lambda _: None) # dummy command

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


        self.ser = serial.Serial('/dev/pts/5')
        log.info('opened serial port "{}"'.format(self.ser.name))


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
            elif k == curses.KEY_F11 or k == curses.KEY_F9:
                self.show_admin_screen()
            else:
                if not self.widget_mgr.handle_input(k):
                    log.info("unhandled key '{}'".format(k))

    def show_about(self):
        self.widget_mgr.show_single_popup('Kreuzworträtsel',
                """Geschrieben von Samuel Bryner

Diese Software ist frei verfügbar unter der GPL. Quellcode unter
https://github.com/iliis/crossword
""")

    def show_admin_screen(self):
        self.widget_mgr.show_single_popup('Admin',
                'Serial Port: {}\n\n'.format(self.ser.name)
                +'Local Address:\n{}\n'.format('\n'.join(' - {}'.format(a) for a in self.mi.get_local_addresses()))
                +'Local Port: {}\n'.format(self.mi.port)
                +'Remote Control Connections:\n{}\n'.format('\n'.join(' - {}'.format(c.getpeername()) for c in self.mi.connections)),
                callback=self._admin_screen_cb,
                buttons=['CLOSE', 'RESET ALL', 'EXIT APP'])

    def _admin_screen_cb(self, button):
        if button == 'EXIT APP':
            self.is_running = False
            log.info("Exiting application through admin panel.")

    def exit_app_by_packet(self, packet):
        self.is_running = False
        log.info("Exiting application trough remote command.")

    def show_popup_from_packet(self, packet):
        if not 'title' in packet or not 'text' in packet:
            raise ValueError("Invalid command: missing 'title' or 'text' field.")

        if 'buttons' in packet:
            buttons = packet['buttons']
        else:
            buttons = ['OK']

        self.widget_mgr.show_single_popup(
                packet['title'],
                packet['text'],
                buttons=buttons)

    def run(self):
        #ser.write(b'crossword running')
        self.is_running = True

        while self.is_running:
            self.widget_mgr.render()
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
