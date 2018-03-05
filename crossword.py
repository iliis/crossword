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

class Crossword:

    def __init__(self, cfg, management_interface): #, screen, **kwargs):

        self.relx = 0
        self.rely = 0

        self.mi = management_interface

        self.width  = cfg['width']
        self.height = cfg['height']
        self.words  = cfg['words']
        self.solution_col = cfg['solution_column']

        self.cursor = Vector(self.words[0][1], 0) # initialize cursor on first character of first word

        self.grid = GridRenderer(self.width, self.height)

        for n, (word, offset) in enumerate(self.words):
            for i in range(len(word)):
                self.grid.set_cell_edge(offset+i, n, LineType.THICK)
                if i > 0:
                    self.grid.set_cell_edge_left(offset+i, n, LineType.THIN_DASHED3)

        #for i in range(len(self.words)):
            #self.grid.set_cell_edge_left (self.solution_col, i, LineType.DOUBLE)
            #self.grid.set_cell_edge_right(self.solution_col, i, LineType.DOUBLE)


        # user input is stored here
        self.puzzle_input = [ [' '] * len(word) for word, _ in self.words ]

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
        else:
            log.info("ignored key '{}'".format(key))
            return False # did not handle key, no need to update screen
        return True

    def cursor_is_in_field(self):
        if self.cursor.x < 0 or self.cursor.y < 0 or self.cursor.x >= self.width or self.cursor.y >= self.height:
            return False

        word, offset = self.words[self.cursor.y]
        return offset <= self.cursor.x < offset+len(word)

    def cursor_move(self, dx, dy):
        assert dx != 0 or dy != 0

        while True:
            self.cursor = (self.cursor + Vector(dx, dy)) % Vector(self.width, self.height)
            if self.cursor_is_in_field():
                break


    def cursor_to_next_word(self, direction=1):
        self.cursor.y = (self.cursor.y + direction) % self.height
        self.cursor.x = self.words[self.cursor.y][1]

    def cursor_to_next_char(self, direction=1):
        word, offset = self.words[self.cursor.y]
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
        word, offset = self.words[self.cursor.y]
        self.cursor.x = offset + len(word) - 1

    def handle_generic_input(self, _input, direction=1):
        _input = input_to_chr(_input)
        log.info('handling input "{}"'.format(_input))
        #log.info("len: {}".formant(len(str(_input))))
        cur_word, cur_offset = self.words[self.cursor.y]
        self.puzzle_input[self.cursor.y][self.cursor.x - cur_offset] = str(_input).upper()

        # move cursor to next character (or word if this was the last character)
        self.cursor_to_next_char(direction)

        self.notify_state_update('edited')

    def notify_state_update(self, kind):
        self.mi.send_packet({
            'command':  'puzzle_state_update',
            'kind':     str(kind),
            'state':    {
                'cursor': {
                    'x': self.cursor.x,
                    'y': self.cursor.y,
                },
                'input': [''.join(line) for line in self.puzzle_input],
            }
        })

    def draw(self, screen):
        screen.clear()

        for n, line in enumerate(self.grid.render(3,1)):
            screen.addstr(self.rely + n, self.relx, line, curses.A_NORMAL)

        # draw user input
        for n, ((word, offset), user_input) in enumerate(zip(self.words, self.puzzle_input)):
            for i, char in enumerate(user_input):
                attr = curses.A_BOLD #| self.parent.theme_manager.findPair(self, 'GOOD') #curses.color_pair(4)
                if self.cursor.x == (i+offset) and self.cursor.y == n:
                    # draw cursor
                    attr = curses.A_STANDOUT | curses.A_BLINK | curses.A_BOLD

                screen.addstr(
                        self.rely + n*2 + 1,
                        self.relx + (i+offset)*4 + 2,
                        char,
                        attr)


    def while_waiting(self):
        log.info("waiting in widget...")
