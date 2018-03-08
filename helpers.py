import math
from enum import Enum
import json

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
