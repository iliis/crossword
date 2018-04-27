#!/bin/env python3

import curses
import logging
import math
import threading
import time
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


class ShootingRangeState(Enum):
    READY = 0
    ACTIVE = 1
    DISABLED = 2
    NOT_WORKING = 3


class ShootingRange(WidgetBase):
    def __init__(self, app) -> None:
        super(ShootingRange, self).__init__(app, Vector(0,0), Vector(102,37))
        self.center_in(app.screen)
        self.state = ShootingRangeState.READY

        try:
            self.target = ReddotTarget() #("/dev/ttyUSB2")
            self.target.start() # start asynchronous thread which polls the target
        except ReddotTarget.AutodetectFailedException as e:
            log.error(str(e))
            self.target = None
            self.state = ShootingRangeState.NOT_WORKING

        self.target_rect_size  = Vector(70,33)
        self.target_point_diam = Vector(len(TARGET_CIRCLE[0]), len(TARGET_CIRCLE))

        self.MAX_POS = 4500 # min/max X/Y coordinate returned by reddot target
        self.CIRCLE_RAD = 1500
        self.TIMEOUT = 3 * 60
        self.MAX_BONUS_TIME = 10 * 60
        self.MAX_POINTS_FOR_BONUS = 200

        curses.init_pair(50, curses.COLOR_BLACK, curses.COLOR_WHITE) # bg white
        curses.init_pair(51, curses.COLOR_WHITE, curses.COLOR_RED)   # bg red

        curses.init_pair(52, curses.COLOR_WHITE, curses.COLOR_BLACK) # point white
        curses.init_pair(53, curses.COLOR_BLACK, curses.COLOR_GREEN)   # point red

        curses.init_pair(54, curses.COLOR_YELLOW, curses.COLOR_BLACK) # points total

        self.closed_callback = None
        self.first_shot_callback = None
        self.time_started = 0

        self.shots = [] # type: List[Tuple[Vector, float, float]]

        #for i in range(25):
            #self.shots.append(
                #(Vector(1,1), 10, 42)
            #)
        ## all the following shots are within the red dot
        #self.shots.extend([
        #    (Vector(452, -1400), 1306.6, 5.7),
        #    (Vector(452, -1260), 1306.6, 5.7),
        #    (Vector(411, -1424), 1482.1, 5.0),
        #    (Vector(-720, -926), 1172.9, 6.3),
        #    (Vector(-786, 648), 1018.6, 6.9),
        #    (Vector(976, 601), 1146.2, 6.4),
        #    (Vector(937, 922), 1314.5, 5.7),
        #    (Vector(-1005, 799), 1283.9, 5.8),
        #    (Vector(-36, 1031), 1031.6, 6.8),
        #    (Vector(1168, 152), 1177.8, 6.2),
        #    (Vector(-1333, 129), 1339.2, 5.6),
        #    (Vector(0, 0), 0, 0),
        #])

    def handle_input(self, key):
        pass

    def handle_shot(self, shot):
        if self.state == ShootingRangeState.READY:
            t = threading.Timer(self.TIMEOUT, self.shooting_range_timeout)
            t.daemon = True # kill when main thread exits
            t.start()
            self.state = ShootingRangeState.ACTIVE
            self.time_started = time.time()
            self.first_shot_callback()
        elif self.state == ShootingRangeState.DISABLED:
            # we are disabled and thus we discard all future shots
            return

        pos = Vector(int(shot[8]), -int(shot[9])) # y axis is inverted relative to screen
        dist = float(shot[7])
        points = float(shot[6])

        log.info("handling shot: Pos={}, Dist={}, points={}".format(pos, dist, points))

        self.shots.append( (pos, dist, points) )

    def draw(self) -> None:
        self.screen.erase()
        self.screen.border()

        # render target square
        for l in range(self.target_rect_size.y):
            self.screen.addstr(l+2, 2, " "*self.target_rect_size.x, curses.color_pair(50))
        # render target circle
        o = Vector(2,0)+self.target_rect_size/2-self.target_point_diam/2
        for line, text in enumerate(TARGET_CIRCLE):
            w = len([c for c in text if c != ' '])
            self.screen.addstr(int(line+o.y), int(o.x+self.target_point_diam.x/2-w/2), " "*w, curses.color_pair(51))

        self.screen.addstr(2, self.target_rect_size.x+4, "Verbleibende Zeit: {}".format(self.remaining_time()), curses.A_NORMAL)

        self.screen.addstr(4, self.target_rect_size.x+4, "Treffer:", curses.A_BOLD)
        self.screen.addstr(5, self.target_rect_size.x+4, "Nr.:      Punkte.:", curses.A_BOLD)

        self.screen.addstr(self.target_rect_size.y-2, self.target_rect_size.x+4, "Total:", curses.A_BOLD)
        self.screen.addstr(self.target_rect_size.y-2, self.target_rect_size.x+9,
                "{:>13}".format(self.total_points()),
                curses.A_BOLD + curses.color_pair(54))

        self.screen.addstr(self.target_rect_size.y-1, self.target_rect_size.x+4, "Bonuszeit:", curses.A_BOLD)
        self.screen.addstr(self.target_rect_size.y-1, self.target_rect_size.x+15,
                time_format(self.points_to_bonus_time()),
                curses.A_BOLD + curses.color_pair(54))

        list_offset = max(len(self.shots) - self.target_rect_size.y + 7, 0)
        for nr, (pos, dist, pts) in enumerate(self.shots):
            p = (pos/(self.MAX_POS*2) + Vector(0.5, 0.5))*self.target_rect_size
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

            self.screen.addstr(nr+6-list_offset, self.target_rect_size.x+4, " {:>3}.  {:>12}  ".format(nr+1, pts), tbl_flags)

        self.screen.addstr(1,2, 'Schiessstand', curses.A_BOLD)
        #self.screen.addstr(2,2, str(self.target.ser.port))

    def shooting_range_timeout(self):
        log.info("shooting range timeout")
        self.shooting_range_state = ShootingRangeState.DISABLED
        self.app.widget_mgr.show_single_popup(
                'Schiessstand beendet',
                'Sie haben {} Bonuszeit erhalten'.format(self.points_to_bonus_time()),
                self.closed_callback,
                ['OK'])
        # force render as we did not receive a regular input
        self.app.widget_mgr.render()

    def total_points(self):
        return int(sum([p for _, _, p in self.shots]))

    def points_to_bonus_time(self):
        total = min(self.total_points(), self.MAX_POINTS_FOR_BONUS)
        return total / self.MAX_POINTS_FOR_BONUS * self.MAX_BONUS_TIME

    def remaining_time(self):
        diff = max(math.ceil(self.time_started + self.TIMEOUT - time.time()), 0)
        return time_format(diff)
