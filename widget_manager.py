import curses
import logging
import time
import threading

from helpers import *
from popup import Popup

log = logging.getLogger('puzzle')

class WidgetManager:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen

        self.widgets = []
        self.focus = None

        self.periodic_refresh()

    def add(self, widget):
        self.widgets.append(widget)

    def handle_input(self, key):
        if self.focus is not None:
            return self.focus.handle_input(key)
        else:
            return False

    def show_single_popup(self, *args, **kwargs):
        if not isinstance(self.focus, Popup):
            self.show_popup(*args, **kwargs)

    def show_popup(self, title, text, callback=None, buttons=['OK']):
        popup = Popup(self.app, self.screen, title, text, buttons)
        self.add(popup)

        old_focus = self.focus # save focus at time of popup call
        self.focus = popup

        def wrapped_callback(btn):
            nonlocal popup # otherwise assignment to this variable will mark it as local

            log.info('popup wrapped_callback, restoring focus to {}'.format(old_focus))
            self.focus = old_focus # restore focus
            popup.visible = False
            #popup.screen.clear()
            self.widgets.remove(popup)

            self.screen.clear()
            self.screen.refresh()

            del popup
            popup = None

            if callback:
                callback(btn)

            self.screen.clear()

        popup.callback = wrapped_callback

    def render(self):
        for widget in self.widgets:
            widget.render()

        curses.doupdate()


    def periodic_refresh(self):
        # although 1 would be ideal, this will drift and thus we will have some
        # values twice which does not look good.
        threading.Timer(0.25, self.periodic_refresh).start()
        self.render()
