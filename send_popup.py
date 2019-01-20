#!/bin/env python3

import argparse
import socket
import netifaces
import logging
import selectors
import json
import traceback

from management_interface import PacketParser


parser = argparse.ArgumentParser(description='Send a popup to the crossword server app')
parser.add_argument('-t', '--title', type=str, help='Title of the popup', required=True)
parser.add_argument('-m', '--message', type=str, help='Actual message content', required=True)
parser.add_argument('-b', '--buttons', type=str, default=['OK'], nargs='+', help='Buttons to show on popup')
parser.add_argument('-p', '--port', type=int, default=1234, help='Destination port')
parser.add_argument('-a', '--address', default='localhost', help='Destination address')
args = parser.parse_args()


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
data = json.dumps(payload)
conn.send("{}\n{}\n".format(len(data), data).encode('ascii'))

print("sent packet of length {} (encoded length: {})".format(len(data), len(data.encode('ascii'))))


try:
    while True:
        data = conn.recv(4096)

        if data:
            #print("received {} bytes: '{}'".format(len(data), data))
            p = data_buffer.parse(data)
            if p:
                payload = json.loads(p)
                print("got answer:")
                print(payload)
                if 'command' in payload and payload['command'] == 'popup_closed':
                    break
except ValueError:
    print("got invalid packet data: '{}'".format(data))
except ConnectionResetError:
    print("Connection to {} failed".format(conn))

conn.close()
