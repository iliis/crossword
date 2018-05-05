import math
from enum import Enum
import json
import logging

log = logging.getLogger('puzzle')

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name #{"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return "Vec[{}, {}]".format(self.x, self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector(self.x * other.x, self.y * other.y)

    def __mod__(self, other):
        return Vector(self.x % other.x, self.y % other.y)

    def __truediv__(self, num):
        return Vector(self.x / num, self.y / num)

    def len(self):
        return math.sqrt(self.x**2 + self.y**2)

def input_to_chr(_input):
    if type(_input) == int:
        return chr(_input)
    else:
        assert type(_input) == str
        return _input


# split text into lines (either at \n or ' ') so that it fits into max_cols
def layout_text(text, max_width):
    lls = [layout_line(l.strip(), max_width) for l in text.split('\n')]
    return [l for ls in lls for l in ls] # flatten

def layout_line(line, max_width):
    if len(line) <= max_width:
        return [line]
    else:
        # find optimal break-points
        #log.info('fitting line "{}" into {} characters'.format(line, max_width))
        lines = []
        cur_line = ""


        words = line.split(' ')
        while True:

            if len(cur_line) >= max_width:
                #log.info(' --> appending very long cur_line = "{}"'.format(cur_line))
                lines.append(cur_line)
                cur_line = ""
            elif len(cur_line) > 0:
                cur_line += ' ' # space between words

            if len(words) == 0:
                if len(cur_line) > 0:
                    lines.append(cur_line)
                break

            #log.info(' --> trying to append word "{}"'.format(words[0]))
            if len(cur_line) + len(words[0]) > max_width:
                if len(words[0]) > max_width:
                    # break very long words into multiple lines if necessary
                    #log.info('splitting very long word "{}"'.format(words[0]))
                    l = max_width - len(cur_line)
                    cur_line += words[0][:l]
                    words[0]  = words[0][l:]

                lines.append(cur_line)
                #log.info('     --> too long for current line, waiting for next one')
                #log.info('     --> appending prev cur_line = "{}"'.format(cur_line))
                cur_line = ""
            else:
                cur_line += words[0]
                del words[0]
                #log.info('     --> appending... cur_line = "{}"'.format(cur_line))

        return lines


def time_format(s):
    hours = int(s / 3600)
    mins = int(s / 60 - hours * 60)
    secs = int(s - mins * 60 - hours * 3600)
    if hours > 0:
        return "{:>2}h {:02}m {:>02}s".format(hours, mins, secs)
    else:
        return "{:>2}m {:>02}s".format(mins, secs)
