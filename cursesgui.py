#!/bin/env python3

import npyscreen
import curses
import json
from enum import Enum

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
    '1010': '─',  '2020': '━',  '0000': '│',  '0000': '┃',
    '0011': '┌',  '0021': '┍',  '0000': '┎',  '0022': '┏',
    '1001': '┐',  '2001': '┑',  '0000': '┒',  '2002': '┓',  '0110': '└',  '0000': '┕',  '0000': '┖',  '0220': '┗',
    '1100': '┘',  '2100': '┙',  '0000': '┚',  '2200': '┛',  '0000': '├',  '0000': '┝',  '0000': '┞',  '0000': '┟',
    '0212': '┠',  '0221': '┡',  '0000': '┢',  '0000': '┣',  '0000': '┤',  '0000': '┥',  '0000': '┦',  '0000': '┧',
    '1202': '┨',  '2201': '┩',  '0000': '┪',  '0000': '┫',  '1011': '┬',  '0000': '┭',  '0000': '┮',  '0000': '┯',
    '1012': '┰',  '2012': '┱',  '0000': '┲',  '0000': '┳',  '1110': '┴',  '0000': '┵',  '0000': '┶',  '0000': '┷',
    '1210': '┸',  '2210': '┹',  '0000': '┺',  '0000': '┻',  '0000': '┼',  '0000': '┽',  '0000': '┾',  '0000': '┿',
    '1211': '╀',  '1112': '╁',  '0000': '╂',  '0000': '╃',  '0000': '╄',  '0000': '╅',  '0000': '╆',  '0000': '╇',
    '2122': '╈',  '2212': '╉',  '0000': '╊',  '0000': '╋',  '0000': '╌',  '0000': '╍',  '0000': '╎',  '0000': '╏',
    '3030': '═',  '0303': '║',  '0000': '╒',  '0000': '╓',  '0033': '╔',  '0000': '╕',  '0000': '╖',  '3003': '╗',
    '0130': '╘',  '0310': '╙',  '0330': '╚',  '0000': '╛',  '0000': '╜',  '3300': '╝',  '0000': '╞',  '0000': '╟',
    '0333': '╠',  '3101': '╡',  '0000': '╢',  '0000': '╣',  '0000': '╤',  '0000': '╥',  '0000': '╦',  '0000': '╧',
    '1310': '╨',  '3330': '╩',  '0000': '╪',  '0000': '╫',  '0000': '╬',  
    '1000': '╴',  '0100': '╵',  '0000': '╶',  '0000': '╷',  
    '2000': '╸',  '0200': '╹',  '0000': '╺',  '0000': '╻',  
    '1020': '╼',  '0102': '╽',  '0000': '╾',  '0000': '╿',  
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




class Crossword(npyscreen.widget.Widget):

    def __init__(self, screen, **kwargs):

        cfg = kwargs['cfg']
        self.puzzle_width  = cfg['width']
        self.puzzle_height = cfg['height']
        self.puzzle_words = cfg['words']
        self.puzzle_solution_col = cfg['solution_column']


        super(Crossword, self).__init__(screen, **kwargs)

        self.grid = GridRenderer(self.puzzle_width, self.puzzle_height)

        for n, (word, offset) in enumerate(self.puzzle_words):
            for i in range(len(word)):
                self.grid.set_cell_edge(offset+i, n, LineType.THICK)

        self.update()

    def calculate_area_needed(self):
        return self.puzzle_height*2+1, self.puzzle_width*4+1

    def set_up_handlers(self):
        super(Crossword, self).set_up_handlers()
        """
        self.handlers.update({
            curses.KEY_UP:    self.cursor_up,
            curses.KEY_DOWN:  self.cursor_down,
            curses.KEY_LEFT:  self.cursor_left,
            curses.KEY_RIGHT: self.cursor_right
        })
        """

    def cursor_up(self):
        pass

    def cursor_down(self):
        pass

    def cursor_left(self):
        pass

    def cursor_right(self):
        pass


    def update(self, clear=True):
        if clear:
            self.clear()

        if self.hidden:
            self.clear()
            return False

        for n, line in enumerate(self.grid.render(3,1)):
            self.add_line(self.rely + n, self.relx, line, self.make_attributes_list(line, curses.A_NORMAL), self.calculate_area_needed()[1])

        #for n, (word, offset) in enumerate(self.puzzle_words):
            #self.add_line(self.rely + n, self.relx + offset, word, self.make_attributes_list(word, curses.A_NORMAL), self.puzzle_width)
        """
        for row in range(self.puzzle_height):
            for col in range(self.puzzle_width):
                self.parent.curses_pad.addch(self.rely + row*2, self.relx + col*4 + 1, "╚")
                self.parent.curses_pad.addch(self.rely + row*2, self.relx + col*4 + 2, "+")
                self.parent.curses_pad.addch(self.rely + row*2, self.relx + col*4 + 3, curses.ACS_ULCORNER)
                #self.add_line(self.rely + row*3 + 2, self.relx + col*4 + 2, "+", 
                        #[curses.A_NORMAL],
                        #1)
        """


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
    with open('puzzle.cfg', 'r') as puzzle_cfg:
        cfg=json.load(puzzle_cfg)
        print("got words:", cfg['words'])
    TestApp = MyApplication().run()
