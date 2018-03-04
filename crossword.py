import npyscreen
import curses
import logging
import string

from grid_renderer import GridRenderer, LineType
log = logging.getLogger('puzzle')

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

def input_to_chr(_input):
    if type(_input) == int:
        return chr(_input)
    else:
        assert type(_input) == str
        return _input

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
            lambda _input: len(input_to_chr(_input)) == 1 and input_to_chr(_input) in string.ascii_letters + string.digits + 'äöüÄÖÜ',
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
        _input = input_to_chr(_input)
        log.info('handling input "{}"'.format(_input))
        #log.info("len: {}".formant(len(str(_input))))
        cur_word, cur_offset = self.puzzle_words[self.cursor.y]
        self.puzzle_input[self.cursor.y][self.cursor.x - cur_offset] = str(_input).upper()

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
                attr = curses.A_BOLD | self.parent.theme_manager.findPair(self, 'GOOD') #curses.color_pair(4)
                if self.cursor.x == (i+offset) and self.cursor.y == n:
                    # draw cursor
                    attr = curses.A_STANDOUT | curses.A_BLINK | curses.A_BOLD

                self.add_line(
                        self.rely + n*2 + 1,
                        self.relx + (i+offset)*4 + 2,
                        char,
                        [attr], 1)

