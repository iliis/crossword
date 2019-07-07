#!/bin/env python3
import threading
import curses
import traceback
import os
import sys

from app import Application, log

def main(screen):
    try:
        app = Application(screen)
        app.run()
        return None, None
    except Exception as e:
        log.error("Unhandled Exception: {}".format(e))
        log.error(traceback.format_exc())
        return e, traceback.format_exc()



if __name__ == '__main__':
    log.info("starting application")
    ex, bt = curses.wrapper(main)

    if ex is not None:
        # try to display exception on screen

        curses.endwin() # this doesn't really work somehow :(
        # and manually sending ANSI escape codes is not enough :(
        os.system("clear")
        os.system("reset")
        os.system("stty sane")
        os.system("tput rs1")

        print("\033[4m\033[1mUnhandled Exception\033[0m") # bold, underlined
        print("\033[31m\033[1m") # red, bold
        print(ex)

        print("\033[0m") # reset
        print("Backtrace:")
        print(bt)

        log.info("exiting after exception")

        #for t in threading.enumerate():
            #print("thread", t.name, ": ", t, "daemon?", t.daemon)
        sys.exit(-1)
    else:
        log.info("exited cleanly")
        sys.exit(0)
