#!/bin/env python3

import curses
import logging
import math

from widget import WidgetBase
from reddot_target import ReddotTarget

from helpers import *
log = logging.getLogger('puzzle')


TARGET_CIRCLE = [
    "       #########      ",
    "    ###############   ",
    "  ################### ",
    "  ################### ",
    " #####################",
    " #####################",
    " #####################",
    "  ################### ",
    "  ################### ",
    "    ###############   ",
    "       #########      ",
]

class ShootingRange(WidgetBase):
    def __init__(self, app) -> None:
        super(ShootingRange, self).__init__(app, Vector(0,0), Vector(100,35))
        self.center_in(app.screen)

        self.screen.border()
        self.screen.addstr(1,2,"searching for serial port...")
        self.screen.refresh()

        self.target = ReddotTarget("/dev/ttyUSB1")
        self.target.start() # start asynchronous thread which polls the target

        self.screen.clear()

        self.target_rect_size  = Vector(70,33)
        self.target_point_diam = Vector(len(TARGET_CIRCLE[0]), len(TARGET_CIRCLE))

        self.MAX_POS = 4200 # min/max X/Y coordinate returned by reddot target

        curses.init_pair(50, curses.COLOR_RED,   curses.COLOR_WHITE)
        curses.init_pair(51, curses.COLOR_BLACK, curses.COLOR_RED)

        self.shots = []

    def handle_input(self, key):
        pass

    def handle_shot(self, shot):

        pos = Vector(int(shot[8]), -int(shot[9])) # y axis is inverted relative to screen
        dist = float(shot[7])
        points = float(shot[6])

        log.info("handling shot: Pos={}, Dist={}, points={}".format(pos, dist, points))

        self.shots.append( (pos, dist, points) )

    def draw(self) -> None:
        self.screen.border()

        # render target square
        for l in range(self.target_rect_size.y):
            self.screen.addstr(l+1, 2, " "*self.target_rect_size.x, curses.color_pair(50))
        # render target circle
        o = Vector(1,2)+self.target_rect_size/2-self.target_point_diam/2
        for line, text in enumerate(TARGET_CIRCLE):
            w = len([c for c in text if c != ' '])
            self.screen.addstr(int(line+o.y), int(o.x+self.target_point_diam.x/2-w/2), " "*w, curses.color_pair(51))

        for pos, dist, pts in self.shots:
            p = Vector(1,0) + self.target_rect_size/2 + pos/(self.MAX_POS*2)*self.target_rect_size
            #log.info("drawing shot {} to {}".format(pos, p))
            self.screen.addstr(int(p.y), int(p.x), 'X')

        self.screen.addstr(1,2, 'Schiessstand', curses.A_BOLD)
        self.screen.addstr(2,2, str(self.target.ser.port))


