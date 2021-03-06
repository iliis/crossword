import datetime
import curses
import json
import logging
import os
import selectors
import subprocess
import sys
import time
import traceback
import signal

import gc
import pickle

# make sure logfile doesn't grow unboundedly
if os.path.exists("puzzle.log") and os.path.getsize("puzzle.log") > 1024*1024*10: # limit: 10MB
    print("[{}] deleting huge logfile".format(datetime.datetime.now()))
    os.remove("puzzle.log")


log = logging.getLogger('puzzle')
hdlr = logging.FileHandler('puzzle.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)



from helpers import *
from crossword import Crossword
from progress_bar import ProgressBar
from door_panel import DoorPanel
from management_interface import ManagementInterface
from widget_manager import WidgetManager
from shooting_range import ShootingRange, ShootingRangeState
from waitable_timer import WaitableTimer
from final_screen import FinalScreen


def git_cmd(params):
    log.debug("Executing git command: {}".format(params))
    try:
        log.debug("executing git command: {}".format(params))
        label = subprocess.check_output(
                    params,
                    cwd=os.path.dirname(os.path.realpath(__file__))).decode('utf8').strip()

        if len(label) == 0:
            return "UNKNOWN"
        else:
            return label
    except Exception as e:
        log.error("Unhandled Exception: {}".format(e))
        log.debug(traceback.format_exc())
        return "UNKNOWN (err)"

def get_version():
    return git_cmd(["git", "describe", "--always", "--tags"])

def get_version_date():
    return git_cmd(["git", "log", "-1", "--format=%cd"])




class Application:
    def __init__(self, screen):
        self.sel = selectors.DefaultSelector()
        self.screen = screen

        self.is_running = False

        # optionally pass different configuration file (useful for debugging)
        if len(sys.argv) > 1:
            app_cfg_path = sys.argv[1]
        else:
            app_cfg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app.cfg')

        with open(app_cfg_path, 'r') as app_cfg:
            self.cfg = json.load(app_cfg)
            log.info("using application configuration: {}".format(self.cfg))

            if not self.cfg['cheats']:
                # ignore CTRL+Z/V keybinding
                log.info("disabling SIGINT")
                signal.signal(signal.SIGINT, signal.SIG_IGN)


        #curses.raw() # disable special keys and stuff (such as ctrl-c)
        self.screen.nodelay(True) # disable blocking on getch()
        curses.curs_set(False) # hide cursor
        curses.mousemask(curses.ALL_MOUSE_EVENTS) # enable mouse interaction
        curses.nonl() # don't translate KEY_RETURN into '\r\n'

        self.screen.clear()

        # make sure display is big enough
        H, W = self.screen.getmaxyx()
        log.info("Screen Size: {} cols by {} rows".format(W,H))

        if W < 102 or H < 39:
            raise Exception("Screen is too small: {} rows by {} columns, but we need at least 39 by 102.\n".format(H, W) +
                "Try a smaller font size or increasing the resolution of your terminal emulator.")

        # create server for remote control
        self.mi = ManagementInterface(1234, self.sel)
        log.info("local address: {}".format(self.mi.get_local_addresses()))

        self.mi.register_handler('quit', self.exit_app_by_packet)
        self.mi.register_handler('shutdown', self.shutdown)
        self.mi.register_handler('reset', lambda _: self.reset())
        self.mi.register_handler('show_popup', self.show_popup_from_packet)
        self.mi.register_handler('ping', lambda _: None) # dummy command
        self.mi.register_handler('set_time', lambda p: self.set_timeout(p['timeout']))
        self.mi.register_handler('show_shooting_range', lambda _: self.show_shooting_range())
        self.mi.register_handler('get_time', lambda p: self.mi.reply_success(p, self.remaining_time()))
        self.mi.register_handler('restore_saved_state', self.restore_backup_by_packet);
        self.mi.register_handler('memory_dump', lambda p: self.memory_dump());
        self.mi.register_handler('wakeup', lambda p: self.wakeup_screen());

        self.mi.new_connection_handler = self.new_connection_handler

        self.widget_mgr = WidgetManager(self)

        self.TIMEOUT = self.cfg["game_timeout"] #60*60
        self.timeout_timer = WaitableTimer(self.sel, self.TIMEOUT, self.on_timeout)
        self.set_timeout(self.TIMEOUT)

        # register key handler
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.handle_input)

        puzzle_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'puzzle.cfg')
        with open(puzzle_filename, 'r', encoding="utf-8") as puzzle_cfg:
            pcfg = json.load(puzzle_cfg)
            log.info("using puzzle configuration: {}".format(pcfg))
            h, w = screen.getmaxyx()
            self.puzzle = Crossword(self, Vector(10,1), Vector(w-10, h-2), pcfg)
            self.widget_mgr.show(self.puzzle)

        self.puzzle.resize_to_contents()
        H, W = self.puzzle.screen.getmaxyx()
        log.info("Puzzle Size: {} x {}".format(W,H))

        # center in middle of screen (also take progress bar into account)
        ps = self.puzzle.size()
        try:
            self.puzzle.move(Vector(
                    int((w-ps.x)/2),
                    int((h-ps.y+6)/2)
            ))
        except Exception as e:
            raise Exception("Failed to move curses window. This can happen if your screen is too small!\nMaybe you forgot to switch to fullscreen?")

        self.progress_bar = ProgressBar(
                self,
                self.puzzle.pos() - Vector(0,5),
                Vector(self.puzzle.size().x, 5),
                'Lösungsfortschritt:')
        self.puzzle.progress_bar = self.progress_bar
        self.puzzle.solved_callback = self.on_crossword_solved

        self.door_panel = DoorPanel(self)
        self.door_panel.center_in(self.screen)
        self.door_panel.visible = False
        #self.widget_mgr.add(self.door_panel)

        self.shooting_range = ShootingRange(self)
        self.shooting_range.first_shot_callback = self.show_shooting_range
        self.shooting_range.closed_callback = self.on_shooting_range_closed

        if self.shooting_range.target is None:
            self.widget_mgr.show_popup("Hallo", "Konnte keine Verbindung zum Reddot-Target aufbauen. "
                    "Schiessstand ist deaktiviert.") 
        else:
            self.sel.register(self.shooting_range.target.shots_queue_available, selectors.EVENT_READ, self.handle_shot)
            self.sel.register(self.shooting_range.target.has_raised_exception, selectors.EVENT_READ, self.handle_exception_in_reddot_target)

        self.final_screen = FinalScreen(self)

        self.check_for_backup()

        self.periodic_backup_timer = WaitableTimer(self.sel, 10, self.on_periodic_backup)
        self.periodic_backup_timer.start()

    def __del__(self): # TODO: this should be implemented using a context manager ('with')
        self.mi.delete()
        del self.mi
        self.exit()

    def set_timeout(self, seconds):
        if seconds <= 0:
            log.warn("set timeout called with invalid timeout '{}', setting timeout to one second.".format(seconds))
            seconds = 1 # netagive or zero timeouts are not allowed
        self.TIMEOUT = seconds
        self.time_ends = time.time() + self.TIMEOUT
        self.timeout_timer.reset(self.TIMEOUT) # stop any running timer (if any) and set new timeout
        self.timeout_timer.start()

    def on_timeout(self):
        log.info("main application timeout!")
        self.mi.send_packet({
            'event': 'main_timeout',
        })

        self.widget_mgr.remove(self.puzzle)
        self.widget_mgr.remove(self.shooting_range)
        self.widget_mgr.remove(self.door_panel)
        self.widget_mgr.show(self.final_screen)

        self.screen.clear()
        self.screen.refresh()
        self.widget_mgr.show_popup("Zeit Abgelaufen", "Ihre Zeit ist leider rum. Bitte begeben Sie sich zum Ausgang.\nFreundlichst, Ihre Spielleitung")
        self.widget_mgr.render()

        self.clear_backup()

    def show_static_crossword(self):
        log.info("showing crossword again")
        self.widget_mgr.remove_all()
        self.widget_mgr.show(self.puzzle)

    def handle_input(self, stdin):
        k = self.screen.get_wch()
        if k == curses.KEY_F1:
            self.show_help()
        elif k == curses.KEY_F12:
            self.show_about()
        elif k == curses.KEY_F9:
            if self.cfg["cheats"]:
                self.show_admin_screen()
            else:
                self.widget_mgr.show_input("Management", "Passwort:", self.show_admin_screen, True)
        else:
            if not self.widget_mgr.handle_input(k):
                log.info("unhandled key '{}'".format(k))

    def handle_shot(self, _):
        self.shooting_range.target.shots_queue_available.clear()
        while not self.shooting_range.target.shots_queue.empty():
            self.shooting_range.handle_shot(self.shooting_range.target.shots_queue.get())

    def show_about(self):
        self.widget_mgr.show_popup('Kreuzworträtsel',
                """Geschrieben von Samuel Bryner:

Diese Software ist frei verfügbar unter der GPL. Quellcode unter
https://github.com/iliis/crossword
""")

    def show_admin_screen(self, pw=None):
        if pw == self.cfg["admin_pw"] or self.cfg["cheats"]:

            ser_port = "not connected"
            if self.shooting_range.target is not None:
                ser_port = self.shooting_range.target.ser.name

            self.widget_mgr.show_popup('Admin',
                    'Version {}\nLast Update: {}\n\n'.format(get_version(), get_version_date())
                    +'Serial Port: {}\n\n'.format(ser_port)
                    +'Local Address:\n{}\n'.format('\n'.join(' - {}'.format(a) for a in self.mi.get_local_addresses()))
                    +'Local Port: {}\n\n'.format(self.mi.port)
                    +'Remote Control Connections:\n{}\n'.format('\n'.join(' - {}'.format(c.getpeername()) for c in self.mi.connections)),
                    callback=self._admin_screen_cb,
                    buttons=['CLOSE', 'LOAD BACKUP', 'AUTOFILL', 'SHOW SRANGE', 'RESET ALL', 'EXIT APP'])
        else:
            self.widget_mgr.show_popup('Passwort Falsch', 'Die Management-Konsole ist nur für die Spielleitung gedacht, sorry.')

    def _admin_screen_cb(self, button):
        if button == 'EXIT APP':
            log.info("Exiting application through admin panel.")
            self.exit()
        elif button == 'RESET ALL':
            self.reset()
        elif button == 'AUTOFILL':
            self.puzzle.autofill()
        elif button == 'SHOW SRANGE':
            self.show_shooting_range()
        elif button == 'LOAD BACKUP':
            if not self.restore_backup():
                self.widget_mgr.show_popup('Backup wiederhestellen fehlgeschlagen', 'Konnte kein Backup laden. Kontrollier das log für weitere Fehler. Gibt es überhaupt ein Backup?')
        elif button == 'CLOSE':
            pass # just ignore
        else:
            raise ValueError("Unknown button pressed in admin panel: '" + str(button) + "'.")

    def exit_app_by_packet(self, packet):
        log.info("Exiting application trough remote command.")
        self.exit()

    def exit(self):
        self.is_running = False
        # if something fails, shooting_range is not yet created, thus we
        # trigger another exception when trying to set this variable. To
        # protect against this, let's check if the member variable exists
        # before accessing it
        if hasattr(self, 'shooting_range') and self.shooting_range.target is not None:
            self.shooting_range.target.is_running = False

        self.backup_state()
        self.mi.close()
        self.mi = None

    def show_popup_from_packet(self, packet):
        if not 'title' in packet or not 'text' in packet:
            raise ValueError("Invalid command: missing 'title' or 'text' field.")

        if 'buttons' in packet:
            buttons = packet['buttons']
        else:
            buttons = ['OK']

        self.widget_mgr.show_popup(
                packet['title'],
                packet['text'],
                buttons=buttons)

    def on_crossword_solved(self, _):
        self.widget_mgr.remove(self.puzzle)
        self.widget_mgr.show(self.door_panel)
        self.backup_state()

    def show_shooting_range(self):
        if self.shooting_range.target is not None:
            if self.shooting_range.state == ShootingRangeState.NOT_WORKING:
                raise Exception("Cannot start shooting range: Target is not working.")
            else:
                self.widget_mgr.show(self.shooting_range)

    def on_shooting_range_closed(self, _):
        self.widget_mgr.remove(self.shooting_range)

        # convert bonus point to time
        self.set_timeout(self.remaining_time_in_seconds() + self.shooting_range.points_to_bonus_time())

        self.mi.send_packet({
            'event': 'shooting_range_timeout',
            'bonus_time': self.shooting_range.points_to_bonus_time(),
            'total_points': self.shooting_range.total_points(),
            'remaining_time': self.remaining_time_in_seconds()
        })
        self.backup_state()


    def handle_exception_in_reddot_target(self, _):
        self.shooting_range.target.has_raised_exception.clear()
        exc, info = self.shooting_range.target.cached_exception
        raise exc from None

    def remaining_time_in_seconds(self):
        return max(math.ceil(self.time_ends - time.time()), 0)

    def remaining_time(self):
        return time_format(self.remaining_time_in_seconds())

    def shutdown(self, packet):
        log.info("Shutting down PC!!")
        subprocess.call(["sudo", "halt"])

    def show_help(self):
        self.widget_mgr.show_popup('Hilfe',
                'Für jeden Verbrecher gibt es ein Rätsel. Löse die Rätsel und trage die Lösungsworte hier im Kreuzworträtsel ein um auszubrechen. '
                'Pfeiltasten auf der Tastatur benutzen zum navigieren. Sobald alles korrekt ausgefüllt ist erscheint die Türsteuerung. '
                'Bei Fragen oder wenn Ihr einen Tipp braucht einfach mit dem Telefon anrufen: Kurbeln und Höhrer ans Ohr halten.')

    def reset(self):
        log.info("Resetting application!")
        self.screen.clear()

        self.puzzle.reset()
        self.door_panel.reset()
        self.shooting_range.reset()

        self.widget_mgr.remove_all()
        self.TIMEOUT=self.cfg["game_timeout"]
        self.set_timeout(self.TIMEOUT)

        self.widget_mgr.show(self.puzzle)

    def run(self):
        #ser.write(b'crossword running')
        self.is_running = True

        while self.is_running:
            self.widget_mgr.render()
            events = self.sel.select()

            for key, mask in events:
                callback = key.data
                callback(key.fileobj)

    def on_periodic_backup(self):
        self.backup_state()
        self.periodic_backup_timer.reset()
        self.periodic_backup_timer.start()

    def backup_state(self):
        state = {
            # Q: store this as an absolute timestamp, so time continues?
            # A: No, don't count time it took to restart app, that's not the players fault
            'time_remaining': self.remaining_time_in_seconds(),
            # TODO: puzzle state backup/restore should be handled in Crossword class itself
            'puzzle_input': [''.join(line) for line in self.puzzle.puzzle_input],
            'puzzle_solved': self.door_panel.visible
        }

        with open('state_backup.cfg', 'w') as state_file:
            json.dump(state, state_file)
            log.info("wrote state to backup file: {}".format(state))

    def clear_backup(self):
        if os.path.exists("state_backup.cfg"):
            log.info("deleting state backup")
            os.remove("state_backup.cfg")

    def load_backup(self):
        if not os.path.isfile('state_backup.cfg'):
            log.error("cannot restore state from backup: file does not exist")
            return None

        try:
            with open('state_backup.cfg', 'r') as state_file:
                return json.load(state_file)
        except:
            return None

    def restore_backup_by_packet(self, packet):
        if self.restore_backup():
            return self.mi.reply_success(packet)
        else:
            return self.mi.reply_failure(packet, "Could not restore state. Maybe there is no backup?")

    def restore_backup(self):
        state = self.load_backup()
        if state is None:
            return False

        # don't restore a completed game
        if state["time_remaining"] <= 0:
            return False

        self.set_timeout(state["time_remaining"])

        if state["puzzle_solved"]:
            self.widget_mgr.remove(self.puzzle)
            self.widget_mgr.show(self.door_panel)
            self.widget_mgr.render(clear=True)
        else:
            # TODO: puzzle state backup/restore should be handled in Crossword class itself
            self.puzzle.puzzle_input = [[c for c in line] for line in state["puzzle_input"]]
            self.puzzle.notify_state_update('restore')

        log.warning("Restored state from backup. Remaining time: {}".format(self.remaining_time_in_seconds()))
        self.mi.send_packet({
            'event': 'backup_restored',
            'remaining_time': self.remaining_time_in_seconds(),
        })
        return True

    def is_backup_different(self):
        """
        Check if there is anything in the backup to be interesting.
        """
        if not os.path.exists('state_backup.cfg'):
            return False # no backup -> nothing interesting

        backup = self.load_backup()
        if not backup:
            log.error("Failed to load backup even though file exists?! This should not happen.")
            return False

        if backup["time_remaining"] <= 0:
            return False

        if backup["puzzle_solved"]:
            return True

        # check crossword puzzle
        for line_backup, line_puzzle in zip(backup["puzzle_input"], self.puzzle.puzzle_input):
            if [c for c in line_backup] != line_puzzle:
                return True

        # nothing to restore from backup
        return False

    def check_for_backup(self):
        # check if backup contains anything interesting
        if self.is_backup_different():
            # if so, ask if you want to restore it
            self.widget_mgr.show_popup('Wiederherstellen?',
                                       'Offenbar wurde das Spiel unterbrochen und nicht korrekt zu Ende gespielt.\n'
                                       'Dies sollte nicht passieren, bitte melden Sie diesen Vorfall der Spielleitung.\n\n'
                                       'Möchten Sie Ihren den vorherigen Zustand wieder rekonstruieren? Andernfalls müssen Sie mit dem Kreuzworträtsel von vorne beginnen.',
                                       callback=self._check_backup_popup_cb,
                                       buttons=['WIEDERHERSTELLEN', 'NEUES SPIEL'])

    def _check_backup_popup_cb(self, button):
        if button == 'WIEDERHERSTELLEN':
            self.restore_backup()

    def new_connection_handler(self, connection):
        # notify newly connected clients about the current state of things
        # (these will notify *all* clients, but that shouldn't be a problem)
        self.widget_mgr.send_stack_update(force=True)
        self.puzzle.notify_state_update("new_connection")

    def get_screen_width(self):
        H, W = self.screen.getmaxyx()
        return W

    # from https://stackoverflow.com/a/9567831
    def memory_dump(self):
        log.info("collecting garbage...")
        gc.collect()
        log.info("dumping memory to 'memory_dump.pickle'...")
        xs = []
        for obj in gc.get_objects():
            i = id(obj)
            size = sys.getsizeof(obj, 0)
            #    referrers = [id(o) for o in gc.get_referrers(obj) if hasattr(o, '__class__')]
            referents = [id(o) for o in gc.get_referents(obj) if hasattr(o, '__class__')]

            cls = None
            if hasattr(obj, '__class__'):
                cls = str(obj.__class__)
            xs.append({'id': i, 'class': cls, 'str': str(obj), 'size': size, 'referents': referents})

        with open('memory_dump.pickle', 'wb') as dump:
            pickle.dump(xs, dump, pickle.HIGHEST_PROTOCOL)
        log.info("memory dump complete")

    def wakeup_screen(self):
        log.info("sending key to wakeup screen")
        subprocess.check_call(["xdotool", "key", "Up"])


