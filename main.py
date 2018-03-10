#!/bin/env python3
import curses

from app import Application, log


def main(screen):

    app = Application(screen)
    app.run()

    #ser = serial.Serial('/dev/pts/0')
    #log.info('opened serial port "{}"'.format(ser.name))

if __name__ == '__main__':
    log.info("starting application")
    curses.wrapper(main)
