#!/bin/env python3
import npyscreen
import logging
import json
import curses
import selectors
import sys

from crossword import Crossword
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

    screen.clear()
    # create server for remote control
    with ManagementInterface(1234, sel) as mi:

        with open('puzzle.cfg', 'r') as puzzle_cfg:
            cfg = json.load(puzzle_cfg)
            log.info("using configuration: {}".format(cfg))
            puzzle = Crossword(cfg, mi)

        puzzle.draw(screen)

        screen.refresh()

        def read_stdin(stdin, screen):
            k = screen.getch()
            if k >= 0:
                if puzzle.handle_input(k):
                    puzzle.draw(screen)
                    screen.refresh()

        # register key handler
        sel.register(sys.stdin, selectors.EVENT_READ, read_stdin)


        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, screen)
                screen.refresh()

if __name__ == '__main__':

    log.info("starting application")

    #TestApp = MyApplication().run()
    curses.wrapper(main)
