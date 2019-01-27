import curses
import logging
import time
import threading

from helpers import *
from popup import Popup
from input_popup import InputPopup
from waitable_timer import WaitableTimer

log = logging.getLogger('puzzle')

class WidgetManager:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen

        self.widgets = []

        # although 1 would be ideal, this will drift and thus we will have some
        # values twice which does not look good.
        # TODO: only re-render widgets which need periodic refreshing
        self.periodic_refresh_timer = WaitableTimer(self.app.sel, 0.25, self.render, True)
        self.periodic_refresh_timer.start()

        self.last_update = None

    def add(self, widget):
        log.debug("adding new widget: {}".format(widget))
        self.widgets.append(widget)
        self.send_stack_update()

    def show(self, widget):
        log.debug("showing widget: {}".format(widget))
        if not widget in self.widgets:
            self.add(widget)

        self.raise_to_fg(widget)
        widget.visible = True

    def remove(self, widget):
        if widget in self.widgets:
            log.debug("removing widget: {}".format(widget))
            self.widgets.remove(widget)
        else:
            log.debug("not removing widget: {}, is already removed".format(widget))
        widget.visible = False
        self.send_stack_update()

    def remove_all(self):
        log.debug("removing all widgets")
        self.widgets = []
        self.send_stack_update()

    def raise_to_fg(self, widget):
        # move widget to end of list
        log.debug("raising widget to foreground: {}".format(widget))
        idx = self.widgets.index(widget)
        self.widgets.append(self.widgets.pop(idx))
        self.send_stack_update()


    def send_stack_update(self):
        if not self.widgets:
            top = None
        else:
            top = self.widgets[-1]

        if self.last_update == top:
            return # don't send an update when nothing has changed
        self.last_update = top

        event = {
            "event": "window_stack_update",
            "top_window": {
                "type": str(type(top).__name__).lower(),
            }
        }

        if isinstance(top, Popup):
            event['top_window']['title'] = top.title
            event['top_window']['text']  = top.text

        self.app.mi.send_packet(event)

    def handle_input(self, key):
        if len(self.widgets) > 0:
            return self.widgets[-1].handle_input(key)
        else:
            return False

    def show_popup(self, title, text, callback=None, buttons=['OK']):
        return self.show_popup_obj(Popup(self.app, self.screen, title, text, buttons), title, text, callback)

    def show_input(self, title, text, callback=None, is_password_input=False):
        p = self.show_popup_obj(InputPopup(self.app, self.screen, title, text), title, text, callback)
        p.is_password_input = is_password_input
        return p

    def show_popup_obj(self, popup, title, text, callback=None):
        self.add(popup)

        def wrapped_callback(btn):
            nonlocal popup # otherwise assignment to this variable will mark it as local

            popup.visible = False
            #popup.screen.clear()
            self.remove(popup)

            log.info('popup wrapped_callback, restoring focus to {}'.format(self.widgets[-1])) # this fails if there is NO widget, but that should never happen

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
