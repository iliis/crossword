#!/bin/env python3

import argparse
import socket
import netifaces
import logging
import selectors
import json
import traceback
import time

from management_interface import PacketParser


parser = argparse.ArgumentParser(description='Send a popup to the crossword server app')
parser.add_argument('-t', '--title', type=str, help='Title of the popup', required=True)
parser.add_argument('-m', '--message', type=str, help='Actual message content', required=True)
parser.add_argument('-b', '--buttons', type=str, default=['OK'], nargs='+', help='Buttons to show on popup')
parser.add_argument('-p', '--port', type=int, default=1234, help='Destination port')
parser.add_argument('-a', '--address', default='localhost', help='Destination address')
args = parser.parse_args()


def send_packet(connection, payload):
    data = json.dumps(payload)
    connection.send("{}\n{}\n".format(len(data), data).encode('ascii'))
    print("sent packet of length {} (encoded length: {})".format(len(data), len(data.encode('ascii'))))

print("buttons:", args.buttons)

print("opening connection to", args.address)
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect((args.address, args.port))

data_buffer = PacketParser()


payload = {
    'command': 'show_popup',
    'title':   args.title,
    'text':    args.message,
    'buttons': args.buttons
}
send_packet(conn, payload)


if False:
    # check if this is a problem
    data = json.dumps({'command': 'get_time'})

    # send packet in two parts
    conn.send("{}\n{}".format(len(data), data[:5]).encode('ascii'))
    time.sleep(0.3)
    conn.send("{}\n".format(data[5:]).encode('ascii'))



try:
    running = True
    while running:
        data = conn.recv(4096)
        for packet in data_buffer.receive(data):
            payload = json.loads(packet)
            print("got answer:", payload)
            if 'command' in payload and payload['command'] == 'popup_closed':
                running = False # exit

except ValueError:
    print("got invalid packet data: '{}'".format(data))
except ConnectionResetError:
    print("Connection to {} failed".format(conn))

conn.close()
