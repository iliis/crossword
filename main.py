#!/bin/env python3
import curses

from app import Application, log


def main(screen):
    app = Application(screen)
    app.run()

if __name__ == '__main__':
    log.info("starting application")
    curses.wrapper(main)
