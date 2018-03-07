#!/bin/env python3
import npyscreen
import logging
import json
import curses
import selectors
import sys

from crossword import Crossword
from progress_bar import ProgressBar
from management_interface import ManagementInterface

log = logging.getLogger('puzzle')
hdlr = logging.FileHandler('puzzle.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)



sel = selectors.DefaultSelector()


def main(screen):
    #curses.raw() # disable special keys and stuff (such as ctrl-c)
    screen.nodelay(True) # disable blocking on getch()
    curses.curs_set(False) # hide cursor
    curses.mousemask(curses.ALL_MOUSE_EVENTS) # enable mouse interaction

    screen.clear()
    # create server for remote control
    with ManagementInterface(1234, sel) as mi:

        with open('puzzle.cfg', 'r') as puzzle_cfg:
            cfg = json.load(puzzle_cfg)
            log.info("using configuration: {}".format(cfg))
            h, w = screen.getmaxyx()
            puzzle_screen = curses.newwin(h-2, w-10, 1, 10)
            puzzle = Crossword(puzzle_screen, cfg, mi)

        puzzle.resize_to_contents()

        # center in middle of screen (also take progress bar into account)
        ph, pw = puzzle_screen.getmaxyx()
        puzzle_screen.mvwin(int((h-ph+4)/2), int((w-pw)/2))

        ph, pw = puzzle_screen.getmaxyx()
        py, px = puzzle_screen.getbegyx()
        progress_bar_win = curses.newwin(4, pw, py-4, px)
        progress_bar = ProgressBar(progress_bar_win, 'Lösungsfortschritt:')
        puzzle.progress_bar = progress_bar

        puzzle.draw()
        progress_bar.draw()

        screen.refresh()
        puzzle_screen.refresh()
        progress_bar_win.refresh()

        def read_stdin(stdin):
            k = screen.getch()
            if k >= 0:
                if puzzle.handle_input(k):
                    puzzle.draw()
                    puzzle_screen.refresh()
                    progress_bar.draw()
                    progress_bar_win.refresh()

        # register key handler
        sel.register(sys.stdin, selectors.EVENT_READ, read_stdin)


        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
                screen.refresh()

if __name__ == '__main__':

    log.info("starting application")

    #TestApp = MyApplication().run()
    curses.wrapper(main)
