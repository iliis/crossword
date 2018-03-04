#!/bin/env python3

import npyscreen
import curses
import json
import logging
from enum import Enum

log = logging.getLogger(__file__)
hdlr = logging.FileHandler(__file__ + ".log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)

# U+250x 	─ 	━ 	│ 	┃ 	┄ 	┅ 	┆ 	┇ 	┈ 	┉ 	┊ 	┋ 	┌ 	┍ 	┎ 	┏
# U+251x 	┐ 	┑ 	┒ 	┓ 	└ 	┕ 	┖ 	┗ 	┘ 	┙ 	┚ 	┛ 	├ 	┝ 	┞ 	┟
# U+252x 	┠ 	┡ 	┢ 	┣ 	┤ 	┥ 	┦ 	┧ 	┨ 	┩ 	┪ 	┫ 	┬ 	┭ 	┮ 	┯
# U+253x 	┰ 	┱ 	┲ 	┳ 	┴ 	┵ 	┶ 	┷ 	┸ 	┹ 	┺ 	┻ 	┼ 	┽ 	┾ 	┿
# U+254x 	╀ 	╁ 	╂ 	╃ 	╄ 	╅ 	╆ 	╇ 	╈ 	╉ 	╊ 	╋ 	╌ 	╍ 	╎ 	╏
# U+255x 	═ 	║ 	╒ 	╓ 	╔ 	╕ 	╖ 	╗ 	╘ 	╙ 	╚ 	╛ 	╜ 	╝ 	╞ 	╟
# U+256x 	╠ 	╡ 	╢ 	╣ 	╤ 	╥ 	╦ 	╧ 	╨ 	╩ 	╪ 	╫ 	╬ 	╭ 	╮ 	╯
# U+257x 	╰ 	╱ 	╲ 	╳ 	╴ 	╵ 	╶ 	╷ 	╸ 	╹ 	╺ 	╻ 	╼ 	╽ 	╾ 	╿

"""
┏━━━┓
┃ A ┃
┗━━━┛
┏━━━┯━━━┯━━━
┃ A │ B │
┗━━━┷━━━┷━━━
┌───┐
│ B │
└───┘
┌───┐
│ B ┊
└───┘

"""

# 0: none
# 1: thin
# 2: thick
# 3: double
FULL_CHAR_DICT = {
   # ltrb
    '0000': ' ',
    '1010': '─',  '2020': '━',  '0101': '│',  '0000': '┃',
    '0011': '┌',  '0021': '┍',  '0012': '┎',  '0022': '┏',
    '1001': '┐',  '2001': '┑',  '1002': '┒',  '2002': '┓',  '0110': '└',  '0120': '┕',  '0210': '┖',  '0220': '┗',
    '1100': '┘',  '2100': '┙',  '1200': '┚',  '2200': '┛',  '0111': '├',  '0121': '┝',  '0211': '┞',  '0112': '┟',
    '0212': '┠',  '0221': '┡',  '0122': '┢',  '0222': '┣',  '1101': '┤',  '2101': '┥',  '1201': '┦',  '1102': '┧',
    '1202': '┨',  '2201': '┩',  '2102': '┪',  '2202': '┫',  '1011': '┬',  '2011': '┭',  '1021': '┮',  '2021': '┯',
    '1012': '┰',  '2012': '┱',  '1022': '┲',  '2022': '┳',  '1110': '┴',  '2110': '┵',  '1120': '┶',  '2120': '┷',
    '1210': '┸',  '2210': '┹',  '1220': '┺',  '2220': '┻',  '1111': '┼',  '2111': '┽',  '1121': '┾',  '2121': '┿',
    '1211': '╀',  '1112': '╁',  '1212': '╂',  '2211': '╃',  '1221': '╄',  '2112': '╅',  '1122': '╆',  '2221': '╇',
    '2122': '╈',  '2212': '╉',  '1222': '╊',  '2222': '╋',
    '3030': '═',  '0303': '║',  '0031': '╒',  '0013': '╓',  '0033': '╔',  '3001': '╕',  '1003': '╖',  '3003': '╗',
    '0130': '╘',  '0310': '╙',  '0330': '╚',  '3100': '╛',  '1300': '╜',  '3300': '╝',  '0131': '╞',  '0313': '╟',
    '0333': '╠',  '3101': '╡',  '1303': '╢',  '3303': '╣',  '3031': '╤',  '1013': '╥',  '3033': '╦',  '3130': '╧',
    '1310': '╨',  '3330': '╩',  '3131': '╪',  '1313': '╫',  '3333': '╬',  
    '1000': '╴',  '0100': '╵',  '0010': '╶',  '0001': '╷',  
    '2000': '╸',  '0200': '╹',  '0020': '╺',  '0002': '╻',  
    '1020': '╼',  '0102': '╽',  '2010': '╾',  '0201': '╿',  
}

FULL_CHAR_DICT['0000'] = ' '

class LineType(Enum):
    NONE = 0          #
    THIN = 1          # │
    THIN_DASHED2 = 4  # ╎
    THIN_DASHED3 = 5  # ┆
    THIN_DASHED4 = 6  # ┊
    THICK = 2         # ┃
    THICK_DASHED2 = 8 # ╏
    THICK_DASHED3 = 9 # ┇
    THICK_DASHED4 =10 # ┋
    DOUBLE = 3        # ║

    def horiz_line_char(self):
        return {
            LineType.NONE:          ' ',
            LineType.THIN:          '─',
            LineType.THIN_DASHED2:  '╌',
            LineType.THIN_DASHED3:  '┄',
            LineType.THIN_DASHED4:  '┈',
            LineType.THICK:         '━',
            LineType.THICK_DASHED2: '╍',
            LineType.THICK_DASHED3: '┅',
            LineType.THICK_DASHED4: '┉',
            LineType.DOUBLE:        '═',
        }[self]

    def vert_line_char(self):
        return {
            LineType.NONE:          ' ',
            LineType.THIN:          '│',
            LineType.THIN_DASHED2:  '╎',
            LineType.THIN_DASHED3:  '┆',
            LineType.THIN_DASHED4:  '┊',
            LineType.THICK:         '┃',
            LineType.THICK_DASHED2: '╏',
            LineType.THICK_DASHED3: '┇',
            LineType.THICK_DASHED4: '┋',
            LineType.DOUBLE:        '║',
        }[self]

    def normalize(self):
        if self in [
                LineType.THIN_DASHED2,
                LineType.THIN_DASHED3,
                LineType.THIN_DASHED4
            ]:
            return LineType.THIN

        if self in [
                LineType.THICK_DASHED2,
                LineType.THICK_DASHED3,
                LineType.THICK_DASHED4,
            ]:
            return LineType.THICK

        return self


    @staticmethod
    def corner_char(l, t, r, b):
        # normalize (there aren't any dashed corner chars)
        l = l.normalize().value
        t = t.normalize().value
        r = r.normalize().value
        b = b.normalize().value

        # build 'code' for LUT
        c = '{}{}{}{}'.format(l, t, r, b)

        if c in FULL_CHAR_DICT:
            return FULL_CHAR_DICT[c]
        else:
            return ' ' # char not found :(

        """
        nonempty = len(t for t in [l, r, t, b] if t != LineType.NONE)

        if nonempty == 0:
            return ' '

        if nonempty == 1:
            if l == LineType.THIN: return '╴'
            if r == LineType.THIN: return '╵'
            if t == LineType.THIN: return '╶'
            if b == LineType.THIN: return '╷'

            if l == LineType.THICK: return '╸'
            if r == LineType.THICK: return '╹'
            if t == LineType.THICK: return '╺'
            if b == LineType.THICK: return '╻'

            return ' ' # no fitting char :(

        if nonempty == 2:
            if 


        return '?'
        """


class GridRenderer:

    def __init__(self, width, height):
        self.width  = width
        self.height = height

        """
        width = 6
        height = 3

        edge indexes:
        ┌──0─0──┬──0─1──┬──0─2──┬──0─3──┬──0─4──┬──0─5──┐
        │       │       │       │       │       │       │
       1│0     1│1     1│2     1│3     1│4     1│5     1│6
        │       │       │       │       │       │       │
        ├──2─0──┼──2─1──┼──2─2──┼──2─3──┼──2─4──┼──2─5──┤
        │       │       │       │       │       │       │
       3│0     3│1     3│2     3│3     3│4     3│5     3│6
        │       │       │       │       │       │       │
        ├──4─0──┼──4─1──┼──4─2──┼──4─3──┼──4─4──┼──4─5──┤
        │       │       │       │       │       │       │
       5│0     5│1     5│2     5│3     5│4     5│5     5│6
        │       │       │       │       │       │       │
        └──6─0──┴──6─1──┴──6─2──┴──6─3──┴──6─4──┴──6─5──┘
        """
        self.edge_types = [[LineType.NONE]*(self.width+1) for _ in range(self.height*2+1)]

    def set_cell_edge(self, x, y, edge_type):
        assert 0 <= x < self.width
        assert 0 <= y < self.height

        self.set_cell_edge_left(x, y, edge_type)
        self.set_cell_edge_right(x, y, edge_type)
        self.set_cell_edge_top(x, y, edge_type)
        self.set_cell_edge_bottom(x, y, edge_type)

    def set_cell_edge_top(self, x, y, edge_type):
        self.edge_types[y*2  ][x]   = edge_type # top

    def set_cell_edge_left(self, x, y, edge_type):
        self.edge_types[y*2+1][x]   = edge_type # left

    def set_cell_edge_right(self, x, y, edge_type):
        self.edge_types[y*2+1][x+1] = edge_type # right

    def set_cell_edge_bottom(self, x, y, edge_type):
        self.edge_types[y*2+2][x]   = edge_type # bottom

    def get_cell_edge_top(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return LineType.NONE
        else:
            return self.edge_types[y*2][x]

    def get_cell_edge_left(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return LineType.NONE
        else:
            return self.edge_types[y*2+1][x]

    def get_cell_edge_right(self, x, y):
        if x < -1 or y < 0 or x >= self.width or y >= self.height:
            return LineType.NONE
        else:
            return self.edge_types[y*2+1][x+1]

    def get_cell_edge_bottom(self, x, y):
        if x < 0 or y < -1 or x >= self.width or y >= self.height:
            return LineType.NONE
        else:
            return self.edge_types[y*2+2][x]


    def render(self, cell_width, cell_height):
        # width, height: size of cell interior in chars

        grid_rows = [[' ']*(self.width*(cell_width+1)+1) for _ in range(self.height*(cell_height+1)+1)]

        # render horizontal and vertical lines
        for y in range(-1, self.height):
            for x in range(-1, self.width):
                # right edge
                if y >= 0:
                    for i in range(cell_height):
                        grid_rows[ y*(cell_height+1)+i+1 ][ (x+1)*(cell_width+1) ] = self.edge_types[y*2+1][x+1].vert_line_char()

                # bottom edge
                if x >= 0:
                    for i in range(cell_width):
                        grid_rows[ (y+1)*(cell_height+1) ][ x*(cell_width+1)+i+1 ] = self.edge_types[y*2+2][x].horiz_line_char()

                # bottom-right corner
                grid_rows[ (y+1)*(cell_height+1) ][ (x+1)*(cell_width+1) ] = \
                        LineType.corner_char(
                                self.get_cell_edge_bottom(x,y), # left
                                self.get_cell_edge_right(x,y), # top
                                self.get_cell_edge_bottom(x+1,y), # right
                                self.get_cell_edge_right(x,y+1), # bottom
                        )


        #return "\n".join(grid_rows)
        return [''.join(row) for row in grid_rows]

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return "Vec[{}, {}]".format(self.x, self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __mod__(self, other):
        return Vector(self.x % other.x, self.y % other.y)


class Crossword(npyscreen.widget.Widget):

    def __init__(self, screen, **kwargs):

        cfg = kwargs['cfg']
        self.puzzle_width  = cfg['width']
        self.puzzle_height = cfg['height']
        self.puzzle_words = cfg['words']
        self.puzzle_solution_col = cfg['solution_column']

        super(Crossword, self).__init__(screen, **kwargs)

        self.cursor = Vector(self.puzzle_words[0][1], 0) # initialize cursor on first character of first word

        self.grid = GridRenderer(self.puzzle_width, self.puzzle_height)

        for n, (word, offset) in enumerate(self.puzzle_words):
            for i in range(len(word)):
                self.grid.set_cell_edge(offset+i, n, LineType.THICK)
                if i > 0:
                    self.grid.set_cell_edge_left(offset+i, n, LineType.THIN_DASHED3)

        #for i in range(len(self.puzzle_words)):
            #self.grid.set_cell_edge_left (self.puzzle_solution_col, i, LineType.DOUBLE)
            #self.grid.set_cell_edge_right(self.puzzle_solution_col, i, LineType.DOUBLE)


        # user input is stored here
        self.puzzle_input = [ [' '] * len(word) for word, _ in self.puzzle_words ]

        self.update()
        log.info("created crossworld")

    def calculate_area_needed(self):
        return self.puzzle_height*2+1, self.puzzle_width*4+1

    def set_up_handlers(self):
        super(Crossword, self).set_up_handlers()
        self.handlers = { # overwrite existing handlers!
            curses.KEY_UP:    self.cursor_up,
            curses.KEY_DOWN:  self.cursor_down,
            curses.KEY_LEFT:  self.cursor_left,
            curses.KEY_RIGHT: self.cursor_right
        }

        self.complex_handlers.append([
            lambda _input: chr(_input).isalnum(),
            self.handle_generic_input
        ])

    def cursor_is_in_field(self):
        if self.cursor.x < 0 or self.cursor.y < 0 or self.cursor.x >= self.puzzle_width or self.cursor.y >= self.puzzle_height:
            return False

        word, offset = self.puzzle_words[self.cursor.y]
        return offset <= self.cursor.x < offset+len(word)

    def cursor_move(self, x, y):
        assert x != 0 or y != 0

        while True:
            self.cursor = (self.cursor + Vector(x, y)) % Vector(self.puzzle_width, self.puzzle_height)
            if self.cursor_is_in_field():
                break


    def cursor_up(self, _input):
        self.cursor_move(0, -1)

    def cursor_down(self, _input):
        self.cursor_move(0, 1)

    def cursor_left(self, _input):
        self.cursor_move(-1, 0)

    def cursor_right(self, _input):
        self.cursor_move(1, 0)

    def cursor_home(self, _input):
        pass # TODO

    def cursor_end(self, _input):
        pass # TODO

    def handle_generic_input(self, _input):
        cur_word, cur_offset = self.puzzle_words[self.cursor.y]
        self.puzzle_input[self.cursor.y][self.cursor.x - cur_offset] = chr(_input).upper()

        # move cursor to next character (or word if this was the last character)
        if self.cursor.x-cur_offset >= len(cur_word) - 1:
            # move to next word
            self.cursor.y = (self.cursor.y + 1) % self.puzzle_height
            self.cursor.x = self.puzzle_words[self.cursor.y][1]
        else:
            # move to next character
            self.cursor.x += 1

    def update(self, clear=True):
        if clear:
            self.clear()

        if self.hidden:
            self.clear()
            return False

        for n, line in enumerate(self.grid.render(3,1)):
            self.add_line(self.rely + n, self.relx, line, self.make_attributes_list(line, curses.A_NORMAL), self.calculate_area_needed()[1])

        # draw user input
        for n, ((word, offset), user_input) in enumerate(zip(self.puzzle_words, self.puzzle_input)):
            for i, char in enumerate(user_input):
                attr = curses.A_NORMAL
                if self.cursor.x == (i+offset) and self.cursor.y == n:
                    # draw cursor
                    attr = curses.A_STANDOUT | curses.A_BLINK

                self.add_line(
                        self.rely + n*2 + 1,
                        self.relx + (i+offset)*4 + 2,
                        char,
                        [attr], 1)


class CrosswordForm(npyscreen.Form):
    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):
       #self.myName        = self.add(npyscreen.TitleText, name='Name')
       #self.myDepartment = self.add(npyscreen.TitleSelectOne, scroll_exit=True, max_height=3, name='Department', values = ['Department 1', 'Department 2', 'Department 3'])
       #self.myDate        = self.add(npyscreen.TitleDateCombo, name='Date Employed')
       with open('puzzle.cfg', 'r') as puzzle_cfg:
           self.crossword = self.add(Crossword, cfg=json.load(puzzle_cfg))

class MyApplication(npyscreen.NPSAppManaged):
   def onStart(self):
       self.addForm('MAIN', CrosswordForm, name='Stadtwache Ankh Morpork Management Console Login')
       # A real application might define more forms here.......

if __name__ == '__main__':

    log.info("starting application")
    with open('puzzle.cfg', 'r') as puzzle_cfg:
        cfg=json.load(puzzle_cfg)
        log.info("using configuration: {}".format(cfg))

    TestApp = MyApplication().run()
