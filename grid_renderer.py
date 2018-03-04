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
