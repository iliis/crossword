#!/bin/env python3

import serial
import serial.tools.list_ports
import time
import logging
import threading
import queue

from waitable_event import WaitableEvent

log = logging.getLogger('puzzle')

class ReddotTarget(threading.Thread):
    class AutodetectFailedException(Exception):
        pass

    def __init__(self, port=None):
        if port == None:
            # try to autodetect port
            log.info("autodetecting serial port...")
            all_ports = serial.tools.list_ports.comports()
            for p in all_ports:
                log.info("trying port {}".format(p))
                with serial.Serial(port=p.device, baudrate=9600, timeout=0.1) as s:
                    s.write([5])
                    try:
                        c = s.read(1)
                        if len(c) == 0:
                            raise serial.serialutil.SerialException("no data")
                    except serial.serialutil.SerialException:
                        log.info('no answer, trying next device')
                        continue

                    log.info("found port {}".format(p))
                    port = p.device
                    break
            else:
                raise ReddotTarget.AutodetectFailedException("Serialport autodetection failed! Is the reddot-target connected?")

        self.ser = serial.Serial(port=port, baudrate=9600, timeout=0.3)

        super(ReddotTarget, self).__init__()

        self.shots_queue = queue.Queue(maxsize=100)
        self.shots_queue_available = WaitableEvent() # we cannot use select() with a queue :(

        self.is_running = True
        self.daemon = True # auto-kill when main thread exits

    def poll(self):
        self.ser.write([5])
        try:
            c = self.ser.read(1)
            if len(c) != 1:
                raise serial.serialutil.SerialException("no data read")
        except serial.serialutil.SerialException:
            log.error('serial read failed')
            return None


        if c[0] == 0x15:
            # no data
            return None
        else:
            # got something
            buf = bytearray(c)
            while c[0] != ord('$'):
                c = self.ser.read(1)
                buf.extend(c)

            data = buf.decode('ascii').split('\r')

            self.ser.write([6]) # clear

            return data

        #time.sleep(0.2)

    def run(self):
        log.info("starting thread for target...")
        while self.is_running:
            data = self.poll()
            if data is not None:
                self.shots_queue.put(data)
                self.shots_queue_available.set()

            time.sleep(0.2)
