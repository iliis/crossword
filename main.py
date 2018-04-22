#!/bin/env python3
import curses
import signal

from app import Application, log

# ignore CTRL+V keybinding
signal.signal(signal.SIGINT, signal.SIG_IGN)

def main(screen):
    app = Application(screen)
    app.run()

if __name__ == '__main__':
    log.info("starting application")
    curses.wrapper(main)
