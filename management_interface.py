import socket
import netifaces
import logging
import selectors
import json
import traceback

from waitable_timer import WaitableTimer
from helpers import *

log = logging.getLogger('puzzle')

NETWORK_DELAY = 1 # in seconds

class PacketParser:
    def __init__(self, timer=None):
        self.timer = timer
        if timer is not None:
            self.timer.callback = self.on_timeout
        self.reset()

    def delete(self):
        log.debug("deleting PacketParser")
        if self.timer:
            self.timer.delete()
            del self.timer

    def reset(self):
        self.length = None
        self.buffer = bytearray()
        if self.timer is not None:
            self.timer.reset()

    def on_timeout(self):
        log.warning("timeout while receiving network data")
        if len(self.buffer) > 0:
            log.warning("got {} bytes of {}: '{}'".format(len(self.buffer), self.length, self.buffer))
        self.reset()

    def receive(self, data):
        """Parses data and returns a list of zero or more packets.
        Packets are bytearrays!"""

        if not data:
            return []

        self.buffer.extend(data)

        #log.debug("adding '{}' to buffer".format(data))
        #log.debug("buffer now contains '{}' = {} bytes".format(self.buffer, len(self.buffer)))

        packets = []

        while True:
            more, packet = self.parse()
            if packet:
                packets.append(packet)
            if not more:
                break

        return packets


    def parse(self):
        """
        Parses internal buffer and returns any packet it can find, which can be none, one or multiple!

        returns: Tuple[bool, Optional[packet]]

        bool: if True, then there is more data to process and parse() should be called again
        packet: parsed packet, might be None

        """

        #log.debug("start parsing: {} bytes in buffer".format(len(self.buffer)))

        if self.length is None:
            # no length information yet
            while b'\n' in self.buffer:
                # got complete length info
                payload_length, self.buffer = self.buffer.split(b'\n', 1)
                if self.timer is not None:
                    # got more data, reset timer (this allows for a full message to take quite long, as long as no single delay is above the timeout, but wayne)
                    self.timer.reset()

                # strip any additional newline characters
                payload_length = payload_length.replace(b'\r', b'')
                payload_length = payload_length.replace(b'\n', b'')

                if len(payload_length) == 0:
                    #log.debug("payload len is 0, {} bytes remaining in buffer".format(len(self.buffer)))
                    continue # try again by splitting at next newline

                self.length = int(payload_length)

                #log.debug("got packet header: length = {}".format(self.length))

                if self.timer is not None:
                    # only start timer if we have a valid payload_length
                    self.timer.start()

                break

        # no elseif, might fall trough:
        if self.length is not None:
            if len(self.buffer) >= self.length:
                # packet is complete
                packet = self.buffer[:self.length]

                # get ready for next packet
                self.buffer = self.buffer[self.length:] # put rest of data (if any) in buffer for next packet

                #log.debug("got complete packet (length = {}, remaining in buffer: {} bytes)".format(self.length, len(self.buffer)))

                self.length = None
                if self.timer is not None:
                    self.timer.reset()

                return len(self.buffer) > 0, packet

        # if we fall through to here, there might still be data in the buffer but not a complete packet
        return False, None



class ManagementInterface:
    def __init__(self, port, selector):
        self.port = port
        self.selector = selector

        # TODO: add IPv6 support
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # could set SO_REUSEADDR so we can restart a program immediately
        # but this could theoretically lead to some errorenous behaviour in edge cases
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_sock.bind(('', port)) # bind to all available interfaces
        self.server_sock.listen()
        self.server_sock.setblocking(False)
        self.selector.register(self.server_sock, selectors.EVENT_READ, self.accept)
        log.info('started server on port {}'.format(port))

        self.data_buffer = {}
        self.connections = []

        self.handlers = {}

        self.new_connection_handler = None

    # handler should take one parameter: the packet
    # handler can return a full response-packet (use reply_success/_failure()
    # helpers) or raise an exception upon error
    def register_handler(self, command, handler):
        self.handlers[command] = handler

    def __del__(self):
        self.close()

    def close(self):
        log.info('closing server connection')
        self.selector.unregister(self.server_sock)
        self.server_sock.shutdown(socket.SHUT_RDWR)
        self.server_sock.close()
        for conn in self.connections:
            #log.info('closing connection {}'.format(conn))
            conn.close()


    def accept(self, sock):
        conn, addr = sock.accept()  # Should be ready
        log.info("accepted connection from {}\n".format(addr))
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

        self.data_buffer[conn] = PacketParser(WaitableTimer(self.selector, NETWORK_DELAY, None))
        self.connections.append(conn)

        if self.new_connection_handler:
            self.new_connection_handler(conn)

    def close_connection(self, conn):
        log.info("closing connection {}\n".format(conn))
        self.selector.unregister(conn)
        conn.close()
        if conn in self.connections:
            self.connections.remove(conn)
        if conn in self.data_buffer:
            self.data_buffer[conn].delete()
            del self.data_buffer[conn]
        else:
            log.warn("not deleting data buffer")


    def get_local_addresses(self):
        addrs = []
        for iface in netifaces.interfaces():
            all_addr = netifaces.ifaddresses(iface)

            for proto in [netifaces.AF_INET, netifaces.AF_INET6]:
                if proto in all_addr:
                    addrs.extend( a['addr'] for a in all_addr[proto] )

        return addrs

    def read(self, conn):
        try:
            data = conn.recv(4096)
            packets = self.data_buffer[conn].receive(data)

            for packet in packets:
                self.handle_packet(packet, conn)

            if packets:
                return # keep connection open
        except ValueError:
            log.error("got invalid packet data: '{}'".format(data))
        except ConnectionResetError:
            log.error("Connection to {} failed".format(conn))
        except Exception as e: # handle other exceptions, like OSError (e.g. "No route to host")
            log.error("Connection to {} failed; got Exception:\n{}\n{}".format(conn, e, traceback.format_exc()))

        # close connection if no data or parse error
        self.close_connection(conn)

    def encode_packet(self, payload):
        data = json.dumps(payload, cls=EnumEncoder)
        return "{}\n{}\n".format(len(data), data).encode('ascii') # json.dumps already encodes utf8, but it still returns a str and we need bytes

    def reply_success(self, orig_pkt, data=None):
        return {
                'command':  'reply',
                'retval':   'success',
                'data':     data,
                'reply_to': orig_pkt,
                }

    def reply_failure(self, orig_pkt, error, retval='failure'):
        return {
                'command':  'reply',
                'retval':   retval,
                'error':    error,
                'reply_to': orig_pkt,
                }

    def handle_packet(self, packet, conn):

        # the json library can only handle strings up to version 3.5
        if type(packet) == bytearray:
            packet = packet.decode('utf-8')

        log.info("got packet: {}".format(repr(packet)))

        payload = json.loads(packet)

        if 'command' in payload:
            cmd = payload['command'].lower()
            if cmd in self.handlers:
                try:
                    reply = self.handlers[cmd](payload)
                except Exception as e:
                    log.error("failed to execute packet handler: Got Exception:\n{}\n{}".format(e, traceback.format_exc()))
                    reply = self.reply_failure(payload, "Exception: {}".format(e), retval='exception')
                    reply['exception'] = str(e)
                    reply['exception_type'] = str(e.__class__.__name__)
                    reply['traceback'] = traceback.format_exc()

                # assume handler executed successfully if it doesn't return any response
                if not reply:
                    reply = self.reply_success(payload)

            else:
                err = "No handler specified for command '{}'.".format(cmd)
                log.warn(err)
                reply = self.reply_failure(payload, err)
        else:
            err = "Got invalid packet without 'command' field: '{}'".format(payload)
            log.err(err)
            reply = self.reply_failure(payload, err)

        log.info("sending reply: '{}'".format(repr(reply)))
        try:
            conn.sendall(self.encode_packet(reply))
        except Exception as e:
            log.error("sendall() failed; got Exception:\n{}\n{}".format(e, traceback.format_exc()))
            self.close_connection(conn)

    def send_packet(self, payload):
        pkt = self.encode_packet(payload)
        for conn in self.connections[:]:
            try:
                conn.sendall(pkt)
            except Exception as e:
                log.error("sendall() failed; got Exception:\n{}\n{}".format(e, traceback.format_exc()))
                self.close_connection(conn)
