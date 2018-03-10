import npyscreen
import curses
import logging
import string
import math
from enum import Enum

from widget import WidgetBase
from helpers import *
from grid_renderer import GridRenderer, LineType
log = logging.getLogger('puzzle')

class Crossword(WidgetBase):

    class SolutionState(Enum):
        UNSOLVED = 1
        WRONG = 2
        PARTIALLY_CORRECT = 3
        CORRECT = 4

    def __init__(self, app, pos, size, cfg): #, screen, **kwargs):
        super(Crossword, self).__init__(app, pos, size)

        self.margin_x = 3
        self.margin_y = 1

        # inside size, without border
        self.cell_w = 3
        self.cell_h = 1

        self.app = app

        self.width  = cfg['width']
        self.height = cfg['height']
        self.words  = cfg['words']
        self.solution_col = cfg['solution_column']

        self.cursor = Vector(self.words[0][1], 0) # initialize cursor on first character of first word

        self.grid = GridRenderer(self.width, self.height)

        for n, (word, offset, desc) in enumerate(self.words):
            for i in range(len(word)):
                self.grid.set_cell_edge(offset+i, n, LineType.THICK)
                if i > 0:
                    self.grid.set_cell_edge_left(offset+i, n, LineType.THIN_DASHED3)

        #for i in range(len(self.words)):
            #self.grid.set_cell_edge_left (self.solution_col, i, LineType.DOUBLE)
            #self.grid.set_cell_edge_right(self.solution_col, i, LineType.DOUBLE)


        # user input is stored here
        self.puzzle_input = [ [' '] * len(word) for word, _, _ in self.words ]

        # COLORS
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(13, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(14, curses.COLOR_RED, curses.COLOR_BLACK)

        self.colors = {
                'highlight':            curses.color_pair(10),
                'solution_highlight':   curses.color_pair(11),
                'text_normal':          curses.color_pair(12),
                'text_correct':         curses.color_pair(13),
                'text_wrong':           curses.color_pair(14),
            }

        self.progress_bar = None

        log.info("created crossworld")

    def calculate_area_needed(self):
        return self.height*2+1, self.width*4+1

    def handle_input(self, key):
        if   key == curses.KEY_LEFT:  self.cursor_move(-1, 0)
        elif key == curses.KEY_UP:    self.cursor_move(0, -1)
        elif key == curses.KEY_RIGHT: self.cursor_move(1, 0)
        elif key == curses.KEY_DOWN:  self.cursor_move(0, 1)
        elif key == curses.KEY_DC:    self.handle_generic_input(' ') # delete
        elif key == curses.KEY_BACKSPACE:
            self.cursor_to_next_char(-1)
            self.handle_generic_input(' ', 0) # backspace
        elif key == ord('\t'):        self.cursor_to_next_word(1) # tab
        elif key == curses.KEY_BTAB:  self.cursor_to_next_word(-1) # shift-tab
        elif key == curses.KEY_HOME:  self.cursor_home()
        elif key == curses.KEY_END:   self.cursor_end()
        elif len(input_to_chr(key)) == 1 and input_to_chr(key) in string.ascii_letters + string.digits + 'äöüÄÖÜ ':
            self.handle_generic_input(key)
        elif key == curses.KEY_MOUSE:
            _id, x, y, z, bstate = curses.getmouse()
            self.handle_mouse_input(x,y,bstate)
        else:
            log.info("ignored key '{}'".format(key))
            return False # did not handle key, no need to update screen
        return True

    def cursor_is_in_field(self, cur):
        if cur.x < 0 or cur.y < 0 or cur.x >= self.width or cur.y >= self.height:
            return False

        word, offset, _ = self.words[cur.y]
        return offset <= cur.x < offset+len(word)

    def cursor_move(self, dx, dy):
        assert dx != 0 or dy != 0

        while True:
            self.cursor = (self.cursor + Vector(dx, dy)) % Vector(self.width, self.height)
            if self.cursor_is_in_field(self.cursor):
                break


    def cursor_to_next_word(self, direction=1):
        self.cursor.y = (self.cursor.y + direction) % self.height
        self.cursor.x = self.words[self.cursor.y][1]

    def cursor_to_next_char(self, direction=1):
        word, offset, _ = self.words[self.cursor.y]
        if direction == 1:
            if self.cursor.x-offset >= len(word) - 1:
                # move to beginning of next word
                self.cursor.y = (self.cursor.y + 1) % self.height
                self.cursor.x = self.words[self.cursor.y][1]
            else:
                # move to next character
                self.cursor.x += 1
        elif direction == -1:
            if self.cursor.x-offset <= 0:
                # move to end of prev. word
                self.cursor.y = (self.cursor.y - 1) % self.height
                word, offset = self.words[self.cursor.y]
                self.cursor.x = offset + len(word) - 1
            else:
                # move to prev character
                self.cursor.x -= 1

    def cursor_home(self):
        self.cursor.x = self.words[self.cursor.y][1]

    def cursor_end(self):
        word, offset, _ = self.words[self.cursor.y]
        self.cursor.x = offset + len(word) - 1

    def handle_generic_input(self, _input, direction=1):
        _input = input_to_chr(_input)
        log.info('handling input "{}"'.format(_input))
        #log.info("len: {}".formant(len(str(_input))))
        _, offset, _ = self.words[self.cursor.y]
        self.puzzle_input[self.cursor.y][self.cursor.x - offset] = str(_input).upper()

        # move cursor to next character (or word if this was the last character)
        self.cursor_to_next_char(direction)

        self.notify_state_update('edited')

    def handle_mouse_input(self, x, y, bstate):

        py, px = self.screen.getbegyx() # window position

        # convert absolute into relative mouse coordinates
        mouse_pos = Vector(x - px, y - py)


        # find closest valid field
        closest_dist = float('inf')
        closest_field = None

        for y, (word, offset, _) in enumerate(self.words):
            for i in range(len(word)):
                cell = Vector(offset+i, y)
                d = (mouse_pos - (self.cell_to_screen_coord(cell) + Vector(self.cell_w+1, self.cell_h+1)/2)).len()
                if d < closest_dist:
                    closest_dist = d
                    closest_field = cell

        #log.info("clicked, closest dist: {}, pos: {}".format(closest_dist, closest_field))

        assert self.cursor_is_in_field(closest_field)

        # ignore mouse clicks that are too far out
        if closest_dist <= 8:
            self.cursor = closest_field



    def notify_state_update(self, kind):
        sol_state = self.validate_input()

        sol_percent = 0
        for (word, offset, desc), (word_state, char_states) in zip(self.words, sol_state):
            # only count (almost) fully solved words
            if word_state == Crossword.SolutionState.PARTIALLY_CORRECT or word_state == Crossword.SolutionState.CORRECT:
                sol_percent += sum(char_states) / len(word) / len(self.words)

        if self.progress_bar:
            self.progress_bar.set_progress(sol_percent)

        self.app.mi.send_packet({
            'command':  'puzzle_state_update',
            'kind':     str(kind),
            'state':    {
                'cursor': {
                    'x': self.cursor.x,
                    'y': self.cursor.y,
                },
                'input': [''.join(line) for line in self.puzzle_input],
                'solved_fraction': sol_percent,
                'solutionstate': sol_state
            }
        })

    def resize_to_contents(self):
        self.screen.resize(
                self.height*(self.cell_h+2) + self.margin_y*2 + 2,
                self.width *(self.cell_w+1) + self.margin_x*2 + 5
                )

    # get top-left corner ON GRID of cell
    def cell_to_screen_coord(self, cell):
        return Vector(
                self.margin_x + cell.x*(self.cell_w+1) + 4,
                self.margin_y + cell.y*(self.cell_h+1))

    def set_attr(self, pos, attr):
        self.screen.chgat(pos.y, pos.x, 1, attr)

    def set_cell_attr(self, cell, attr, border=True, fill=False):
        p = self.cell_to_screen_coord(cell)
        for y in range(self.cell_h+2):
            for x in range(self.cell_w+2):
                is_border_char = (x == 0 or x == self.cell_w+1) or (y == 0 or y == self.cell_h+1)
                if (border and is_border_char) or (fill and not is_border_char):
                    self.set_attr(p + Vector(x,y), attr)

    # return [(word solution state, [char_correct])]
    def validate_input(self):
        state = []
        for current_input, (word, offset, desc) in zip(self.puzzle_input, self.words):
            # check every char
            char_state = [c_in == c_sol for c_in, c_sol in zip(current_input, word)]
            num_input = sum([c_in != ' ' and c_in != '' for c_in in current_input])

            total_wrong = len(word) - sum(char_state)

            if total_wrong == 0:
                word_state = Crossword.SolutionState.CORRECT
            elif total_wrong == 1:
                word_state = Crossword.SolutionState.PARTIALLY_CORRECT
            elif num_input == len(word):
                word_state = Crossword.SolutionState.WRONG
            else:
                word_state = Crossword.SolutionState.UNSOLVED

            state.append( (word_state, char_state) )

        return state


    def draw(self):
        #self.screen.clear()

        self.screen.border()

        #for k, v in inspect.getmembers(self.screen):
            #log.info("{}: {}".format(k,v))

        # grid
        for n, line in enumerate(self.grid.render(self.cell_w,self.cell_h)):
            self.screen.addstr(self.margin_y+n, self.margin_x+4, line)

        """
        # highlight current cell
        for y in range(3):
            self.screen.chgat(
                    self.margin_y + self.cursor.y*2 + y,
                    self.margin_x + self.cursor.x*4 + 4,
                    5,
                    curses.color_pair(10))
        """


        # highlight solution colum
        for row in range(len(self.words)):
            self.set_cell_attr(Vector(self.solution_col, row), curses.color_pair(11) | curses.A_BOLD)

        # descriptions and numbers
        for n, (word, offset, desc) in enumerate(self.words):
            if n == self.cursor.y:
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            self.screen.addstr(self.margin_y + n*(self.cell_h+1) + 1,               self.margin_x, "{}.".format(n+1), attr)
            self.screen.addstr(self.margin_y + self.height*(self.cell_h+1) + 2 + n, self.margin_x, "{}. {}".format(n+1, desc), attr)

        # draw user input
        for n, ((word, offset, desc), user_input, (word_state, char_state)) in enumerate(zip(self.words, self.puzzle_input, self.validate_input())):
            for i, (char, char_correct) in enumerate(zip(user_input, char_state)):
                attr = curses.A_BOLD #| self.parent.theme_manager.findPair(self, 'GOOD') #curses.color_pair(4)
                if self.cursor.x == (i+offset) and self.cursor.y == n:
                    # draw cursor
                    attr = curses.A_STANDOUT | curses.A_BLINK | curses.A_BOLD
                    #attr = curses.color_pair(10)

                if word_state == Crossword.SolutionState.UNSOLVED:
                    if i + offset == self.solution_col:
                        attr |= self.colors['solution_highlight']
                    else:
                        attr |= self.colors['text_normal']
                elif word_state == Crossword.SolutionState.WRONG:
                    attr |= self.colors['text_wrong']
                else: # [PARTIALLY_]CORRECT
                    if char_correct:
                        attr |= self.colors['text_correct']
                    else:
                        attr |= self.colors['text_wrong']

                self.screen.addstr(
                        self.margin_y + n*(self.cell_h+1) + 1,
                        self.margin_x + (i+offset)*(self.cell_w+1) + 2 + 4,
                        char,
                        attr)

        if self.progress_bar:
            self.progress_bar.render()
