import curses
import logging
import time
import threading

from helpers import *
from popup import Popup
from input_popup import InputPopup

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
        return self.show_popup_obj(Popup(self.app, self.screen, title, text, buttons), title, text, callback)

    def show_input(self, title, text, callback=None, is_password_input=False):
        p = self.show_popup_obj(InputPopup(self.app, self.screen, title, text), title, text, callback)
        p.is_password_input = is_password_input
        return p

    def show_popup_obj(self, popup, title, text, callback=None):
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
        return popup

    def render(self):
        for widget in self.widgets:
            widget.render()

        curses.doupdate()


    def periodic_refresh(self):
        # although 1 would be ideal, this will drift and thus we will have some
        # values twice which does not look good.
        # TODO: In which context does this call our function? This might introduce multithreading-issues!
        t = threading.Timer(0.25, self.periodic_refresh)
        t.daemon = True # kill when main thread exits
        t.start()

        self.render()
