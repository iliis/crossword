#!/bin/env python3
import npyscreen
import logging
import json
import curses
import selectors
import sys

from helpers import *
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
            puzzle = Crossword(Vector(10,1), Vector(w-10, h-2), cfg, mi)

        puzzle.resize_to_contents()

        # center in middle of screen (also take progress bar into account)
        ps = puzzle.size()
        puzzle.move(Vector(
                int((w-ps.x)/2),
                int((h-ps.y+4)/2)
                ))

        progress_bar = ProgressBar(
                puzzle.pos() - Vector(0,4),
                Vector(puzzle.size().x, 4),
                'Lösungsfortschritt:')
        puzzle.progress_bar = progress_bar

        puzzle.render()
        progress_bar.render()

        curses.doupdate()

        def read_stdin(stdin):
            k = screen.getch()
            if k >= 0:
                if puzzle.handle_input(k):
                    puzzle.render()
                    progress_bar.render()

        # register key handler
        sel.register(sys.stdin, selectors.EVENT_READ, read_stdin)


        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
                curses.doupdate()

if __name__ == '__main__':
    log.info("starting application")
    curses.wrapper(main)
