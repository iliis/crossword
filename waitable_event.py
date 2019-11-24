# source: https://lat.sk/2015/02/multiple-event-waiting-python-3/

import os
import select
import logging

log = logging.getLogger('puzzle')

class WaitableEvent:
    """
    Provides an abstract object that can be used to resume select() loops with
    indefinite waits from another thread or process. This mimics the standard
    threading.Event interface.
    """

    def __init__(self):
        self._read_fd, self._write_fd = os.pipe()
        log.debug("opening pipe: read fd: {}, write fd: {}".format(self._read_fd, self._write_fd))

    def wait(self, timeout=None):
        rfds, wfds, efds = select.select([self._read_fd], [], [], timeout)
        return self._read_fd in rfds

    def isSet(self):
        return self.wait(0)

    def clear(self):
        if self.isSet():
            os.read(self._read_fd, 1)

    def set(self):
        if not self.isSet():
            os.write(self._write_fd, b'1')

    def fileno(self):
        """
        Return the FD number of the read side of the pipe, allows this object
        to be used with select.select().
        """
        return self._read_fd

    def delete(self):
        log.debug("closing pipe: read fd: {}, write fd: {}".format(self._read_fd, self._write_fd))
        os.close(self._read_fd)
        os.close(self._write_fd)
        self._read_fd = None
        self._write_fd = None

