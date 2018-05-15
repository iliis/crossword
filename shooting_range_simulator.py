#!/usr/bin/python3

import os
import pty
import serial
import serial.tools.list_ports
import time
import subprocess
import re
import random
import sys
import select
import signal

MAX_POS = 4500

def send_shot(ser):
    pts = random.randint(0,100)/10
    dist = random.randint(0,1000)
    px = random.randint(-MAX_POS, MAX_POS)
    py = random.randint(-MAX_POS, MAX_POS)
    msg = '\r'.join(str(n) for n in [0,0,0,0,0,0,pts,dist,px,py]) + '\r$'

    ser.write(msg.encode())


with subprocess.Popen(['/usr/bin/socat', '-d', '-d', 'pty,raw,echo=0,link=./RedDotSimulator', 'pty,raw,echo=0,link=./RedDotSimulatorBackend'],
        stdin=subprocess.DEVNULL,
        ) as socat:

    sending_shots = False

    try:
        time.sleep(0.5) # wait for socat to actually start
        print ("simulator is running...")
        print ("press ENTER to start generating shots")

        ser = serial.Serial('./RedDotSimulatorBackend', baudrate=9600, timeout=0.1)

        while True:
            try:
                c = ser.read(1)
                if len(c) == 0:
                    raise serial.serialutil.SerialException("no data")
                else:
                    if c == b'\x05':
                        if sending_shots:
                            send_shot(ser)
                        else:
                            ser.write([0x15])
            except serial.serialutil.SerialException:
                pass # read timeout

            #time.sleep(0.1)
            in_ready, out_ready, err_ready = select.select([sys.stdin], [], [], 0.1)
            if in_ready:
                sys.stdin.read(1) # clear input
                sending_shots = not sending_shots
                if sending_shots:
                    print("sending shots")
                else:
                    print("stopped")


    except Exception as e:
        print("got exception:")
        print(e)
