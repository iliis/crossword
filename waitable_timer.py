import threading
import selectors
import logging

from waitable_event import WaitableEvent

log = logging.getLogger('puzzle')

class WaitableTimer(WaitableEvent):

    def __init__(self, selector, delay_sec, callback, periodic=False):
        super(WaitableTimer, self).__init__()
        self.sel = selector
        self.delay = delay_sec
        self.callback = callback
        self.periodic = periodic
        self.timer = None
        self.reset()

        self.sel.register(self, selectors.EVENT_READ, self._sel_callback)

    def _sel_callback(self, _):
        # we're back in the main thread here
        #log.info("_sel_callback: thread = {}".format(threading.currentThread()))
        self.clear() # don't trigger callback again
        if self.periodic:
            self.reset()
            # TODO: we *could* implement a non-drifting periodic timer here
            self.timer.start()

        # call actual callback
        self.callback()

    def reset(self, new_delay=None):
        #log.info("WaitableTimer: reset in thread {}".format(threading.currentThread()))
        if self.timer:
            self.timer.cancel()

        if new_delay is not None:
            assert new_delay > 0
            self.delay = new_delay

        self.clear()

        # each threading.Timer can only be used once :(
        self.timer = threading.Timer(self.delay, self._timer_callback)
        self.timer.daemon = True # stop thread when main thread exits

    def _timer_callback(self):
        # don't do anything non-threadsafe in here!
        #log.info("_timer_callback: thread = {}".format(threading.currentThread()))
        self.set()

    def cancel(self):
        self.timer.cancel()

    def start(self):
        self.timer.start()

