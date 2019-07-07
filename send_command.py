#!/bin/env python3
import json
import socket
import sys
import argparse

from management_interface import PacketParser

parser = argparse.ArgumentParser(description='Send a generic command to the crossword server app')
#parser.add_argument('-c', '--command', type=str, help='command', required=True)
parser.add_argument('-p', '--port', type=int, default=1234, help='Destination port')
parser.add_argument('-a', '--address', default='localhost', help='Destination address')
args = parser.parse_args()




# set up connection
con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
con.connect( (args.address, args.port) )

print("connected to", con.getpeername())

parser = PacketParser()


def send(pkt):
    data = json.dumps(pkt)
    pkt = "{}\n{}\n".format(len(data), data).encode('ascii')
    print("sending raw command: '{}'".format(pkt))
    con.sendall(pkt)

    print("sent command")


def receive():
    data = con.recv(4096)
    for packet in parser.receive(data):
        print("got reply:")
        print(json.loads(packet))


def send_popup():
    print("send popup")

    pkt = {'command': 'show_popup'}
    pkt['title'] = input('Titel:')
    pkt['text']  = input('Text:')

    buttons = input('Buttons (leave empty for "OK"):').strip()
    if len(buttons) > 0:
        pkt['buttons'] = buttons.split(',')

    send(pkt)

    receive()



def quit():
    print("sending quit command")
    send({'command': 'quit'})


def ping():
    send({'command': 'ping'})

def reset():
    send({'command': 'reset'})

def restore_backup():
    send({'command': 'restore_saved_state'})

def just_listen():
    print("waiting for packets...")
    while True:
        receive()


fns = [
        just_listen,
        send_popup,
        quit,
        reset,
        ping,
        restore_backup,
    ]


print("choose a command:")
for i, fn in enumerate(fns):
    print(i, fn.__name__)

n = int(input("?"))
if n < len(fns):
    fns[n]()
