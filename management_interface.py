import socket
import logging
import selectors
import json

from helpers import *

log = logging.getLogger('puzzle')

class PacketParser:
    def __init__(self):
        self.reset()

    def reset(self):
        self.length = None
        self.buffer = bytearray()

    def parse(self, data):
        self.buffer.extend(data)
        if self.length is None:
            # no length information yet
            while b'\n' in self.buffer:
                # got complete length info
                payload_length, self.buffer = self.buffer.split(b'\n', 1)

                # strip any additional newline characters
                payload_length = payload_length.replace(b'\r', b'')
                payload_length = payload_length.replace(b'\n', b'')

                if len(payload_length) == 0:
                    continue # try again by splitting at next newline

                self.length = int(payload_length)

                #log.info("got packet header: length = {}".format(int(payload_length)))
                break

        # no elseif, might fall trough:
        if self.length is not None:
            if len(self.buffer) >= self.length:
                # packet is complete
                packet = self.buffer[:self.length].decode('ascii')

                # get ready for next packet
                self.buffer = self.buffer[self.length:] # put rest of data (if any) in buffer for next packet
                self.length = None

                return packet



class ManagementInterface:
    def __init__(self, port, selector):
        self.selector = selector

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # could set SO_REUSEADDR so we can restart a program immediately
        # but this could theoretically lead to some errorenous behaviour in edge cases
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_sock.bind(('', port)) # bind to all available interfaces
        self.server_sock.listen()
        self.server_sock.setblocking(False)
        self.selector.register(self.server_sock, selectors.EVENT_READ, self.accept)
        log.info('started server on TODO:my ip')
        # TODO: write it to screen!

        self.data_buffer = {}
        self.connections = []

        self.handlers = {}

    def register_handler(self, command, handler):
        self.handlers[command] = handler

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        log.info('closing server connection')
        self.server_sock.shutdown(socket.SHUT_RDWR)
        self.server_sock.close()
        for conn in self.connections:
            log.info('closing connection {}'.format(conn))
            conn.close()


    def accept(self, sock):
        conn, addr = sock.accept()  # Should be ready
        log.info("accepted connection from {}\n".format(addr))
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

        self.data_buffer[conn] = PacketParser()
        self.connections.append(conn)

    def read(self, conn):
        data = conn.recv(4096)

        if data:
            #log.info("received {} bytes: '{}'".format(len(data), data))
            p = self.data_buffer[conn].parse(data)
            if p:
                self.handle_packet(p)
        else:
            log.info("closing connection {}\n".format(conn))
            self.selector.unregister(conn)
            conn.close()
            self.connections.remove(conn)

    def handle_packet(self, packet):
        log.info("got packet: '{}'".format(repr(packet)))

        payload = json.loads(packet)

        if payload['command'] in self.handlers:
            self.handlers[payload['command']](payload)
        else:
            log.warn("No handler specifiec for command '{}'.".format(payload_length['command']))

    def send_packet(self, payload):
        data = json.dumps(payload, cls=EnumEncoder)
        pkt = "{}\n{}\n".format(len(data), data).encode('ascii')
        for conn in self.connections:
            conn.sendall(pkt)
