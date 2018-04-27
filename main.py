#!/bin/env python3
import curses
import signal
import traceback
import os

from app import Application, log

# ignore CTRL+V keybinding
#signal.signal(signal.SIGINT, signal.SIG_IGN)

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

    log.info("back in main")

    if ex is not None:
        log.info("clearing screen etc.")
        curses.endwin()
        # try to display it on screen

        # manually sending ANSI escape codes is not enough :(
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

        print("")
        print("")
        log.info("waiting for user to press a key...")
        input("Press [ENTER] to quit")
    else:
        log.info("exited cleanly")
