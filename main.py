#!/bin/env python3
import npyscreen
import logging
import json
import curses
import selectors
import sys

from crossword import Crossword

log = logging.getLogger('puzzle')
hdlr = logging.FileHandler('puzzle.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)


"""
class CrosswordForm(npyscreen.Form):
    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):

        #self.myName        = self.add(npyscreen.TitleText, name='Name')
        #self.myDepartment = self.add(npyscreen.TitleSelectOne, scroll_exit=True, max_height=3, name='Department', values = ['Department 1', 'Department 2', 'Department 3'])
        #self.myDate        = self.add(npyscreen.TitleDateCombo, name='Date Employed')
        with open('puzzle.cfg', 'r') as puzzle_cfg:
            self.crossword = self.add(Crossword, cfg=json.load(puzzle_cfg))

        self.keypress_timeout = 0
        self.curses_pad.nodelay(True) # non-blocking getch()

    def while_waiting(self):
        log.info("waiting in form...")

class MyApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.ElegantTheme)
        self.addForm('MAIN', CrosswordForm, name='Stadtwache Ankh Morpork Management Console Login')
        # A real application might define more forms here.......


        log.info("curses has color? {}".format(curses.has_colors()))
        log.info("colors disabled? {}".format(npyscreen.npysGlobalOptions.DISABLE_ALL_COLORS))

"""

sel = selectors.DefaultSelector()


def main(screen):
    #curses.raw() # disable special keys and stuff (such as ctrl-c)
    screen.nodelay(True) # disable blocking on getch()
    curses.curs_set(False) # hide cursor

    screen.clear()

    with open('puzzle.cfg', 'r') as puzzle_cfg:
        cfg = json.load(puzzle_cfg)
        log.info("using configuration: {}".format(cfg))
        puzzle = Crossword(cfg)

    puzzle.draw(screen)

    screen.refresh()

    def read_stdin(stdin, mask, screen):
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
            callback(key.fileobj, mask, screen)
            screen.refresh()

if __name__ == '__main__':

    log.info("starting application")

    #TestApp = MyApplication().run()
    curses.wrapper(main)
