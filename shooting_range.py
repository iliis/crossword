#!/bin/env python3

import curses
import logging
import math
from typing import List, Tuple

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

        self.target = ReddotTarget("/dev/ttyUSB2")
        self.target.start() # start asynchronous thread which polls the target

        self.screen.clear()

        self.target_rect_size  = Vector(70,33)
        self.target_point_diam = Vector(len(TARGET_CIRCLE[0]), len(TARGET_CIRCLE))

        self.MAX_POS = 4500 # min/max X/Y coordinate returned by reddot target
        self.CIRCLE_RAD = 1000

        curses.init_pair(50, curses.COLOR_BLACK, curses.COLOR_WHITE) # bg white
        curses.init_pair(51, curses.COLOR_BLACK, curses.COLOR_RED)   # bg red

        curses.init_pair(52, curses.COLOR_WHITE, curses.COLOR_BLACK) # point white
        curses.init_pair(53, curses.COLOR_BLACK, curses.COLOR_WHITE) # point red

        curses.init_pair(54, curses.COLOR_YELLOW, curses.COLOR_BLACK) # points total

        self.shots = [] # type: List[Tuple[Vector, float, float]]

        #for i in range(25):
            #self.shots.append(
                #(Vector(1,1), 10, 42)
            #)

    def handle_input(self, key):
        pass

    def handle_shot(self, shot):

        pos = Vector(int(shot[8]), -int(shot[9])) # y axis is inverted relative to screen
        dist = float(shot[7])
        points = float(shot[6])

        log.info("handling shot: Pos={}, Dist={}, points={}".format(pos, dist, points))

        self.shots.append( (pos, dist, points) )

    def draw(self) -> None:
        self.screen.clear()
        self.screen.border()

        # render target square
        for l in range(self.target_rect_size.y):
            self.screen.addstr(l+1, 2, " "*self.target_rect_size.x, curses.color_pair(50))
        # render target circle
        o = Vector(1,2)+self.target_rect_size/2-self.target_point_diam/2
        for line, text in enumerate(TARGET_CIRCLE):
            w = len([c for c in text if c != ' '])
            self.screen.addstr(int(line+o.y), int(o.x+self.target_point_diam.x/2-w/2), " "*w, curses.color_pair(51))

        self.screen.addstr(2, self.target_rect_size.x+4, "Treffer:", curses.A_BOLD)
        self.screen.addstr(3, self.target_rect_size.x+4, "Nr.:      Punkte.:", curses.A_BOLD)

        self.screen.addstr(self.target_rect_size.y-2, self.target_rect_size.x+4, "Total:", curses.A_BOLD)
        self.screen.addstr(self.target_rect_size.y-2, self.target_rect_size.x+10,
                "{:>13}".format(int(sum([p for _, _, p in self.shots]))),
                curses.A_BOLD + curses.color_pair(54))

        self.screen.addstr(self.target_rect_size.y-1, self.target_rect_size.x+4, "Bonuszeit:", curses.A_BOLD)
        self.screen.addstr(self.target_rect_size.y-1, self.target_rect_size.x+15,
                "{:>3}m {:>02}s".format(3, 4),
                curses.A_BOLD + curses.color_pair(54))

        list_offset = max(len(self.shots) - self.target_rect_size.y + 7, 0)
        for nr, (pos, dist, pts) in enumerate(self.shots):
            p = Vector(1,0) + self.target_rect_size/2 + pos/(self.MAX_POS*2)*self.target_rect_size
            #log.info("drawing shot {} to {}".format(pos, p))

            # highlight last shot
            if nr == len(self.shots)-1:
                tbl_flags = curses.A_STANDOUT
                if dist <= self.CIRCLE_RAD:
                    pt_flags  = curses.color_pair(53)
                else:
                    pt_flags = curses.color_pair(52)
            else:
                tbl_flags = curses.A_NORMAL
                if dist <= self.CIRCLE_RAD:
                    pt_flags  = curses.color_pair(51)
                else:
                    pt_flags = curses.color_pair(50)

            self.screen.addstr(int(p.y), int(p.x), 'X', pt_flags)

            # don't draw more shots into table than there is space
            if nr < list_offset:
                continue

            self.screen.addstr(nr+4-list_offset, self.target_rect_size.x+4, " {:>3}.  {:>12}  ".format(nr+1, pts), tbl_flags)

        self.screen.addstr(1,2, 'Schiessstand', curses.A_BOLD)
        self.screen.addstr(2,2, str(self.target.ser.port))


