#!/bin/env python3
import json
import socket


HOST = 'localhost'


# set up connection
con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
con.connect( (HOST, 1234) )

print("connected to", con.getpeername())


def send(pkt):
    data = json.dumps(pkt)
    pkt = "{}\n{}\n".format(len(data), data).encode('ascii')
    print("sending raw command: '{}'".format(pkt))
    con.sendall(pkt)

    print("sent command")

    data = con.recv(4096)

    print("got reply:")
    l, payload = data.decode('utf8').split('\n', 1)
    l = int(l)
    payload = payload.strip()
    if len(payload) != l:
        print("WARNING: malformed packet: invalid length! Got", len(payload), "bytes instead of", l)
    
    print(json.loads(payload))


def send_popup():
    print("send popup")

    pkt = {'command': 'show_popup'}
    pkt['title'] = input('Titel:')
    pkt['text']  = input('Text:')

    buttons = input('Buttons (leave empty for "OK"):').strip()
    if len(buttons) > 0:
        pkt['buttons'] = buttons.split(',')

    send(pkt)



def quit():
    print("sending quit command")
    send({'command': 'quit'})


def ping():
    send({'command': 'ping'})



fns = [
        send_popup,
        quit,
        ping,
    ]


print("choose a command:")
for i, fn in enumerate(fns):
    print(i, fn.__name__)

n = int(input("?"))
if n < len(fns):
    fns[n]()
