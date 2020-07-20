from pygame import Rect, image
from math import pi, e, sqrt


def normalize(values, scale=1):
    """
    Normalize a list of values by deviding by total and scaling it inbetween 0
    and scale

    :param values: a list of number values
    :param scale: a number
    :return: the same list of values but substituted with the normalized values
    """
    total = sum(values)
    for index, val in enumerate(values):
        values[index] = val / total * scale
    return values

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def rect_from_block_matrix(block_matrix):
    """
    Create a pygame rect object from a matrix of block classes.

    :param block_matrix: a list of lists of block objects
    :return: pygame Rect object

    The rectangle is the size between the first and last position in the matrix
    """
    start_pos = block_matrix[0][0].rect.topleft
    end_pos = block_matrix[-1][-1].rect.bottomright
    size = (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
    return Rect((*start_pos, *size))

class Size:
    """
    Class that defines a size, basically a rectangle without coordinates
    """
    def __init__(self, width, height):
        self.height = height
        self.width = width

    @property
    def size(self):
        return [self.width, self.height]

    @property
    def centerx(self):
        return int(self.width / 2)

    @property
    def centery(self):
        return int(self.height / 2)

    @property
    def center(self):
        return (self.centerx, self.centery)

    def __add__(self, other):
        if len(other) == 1:
            return self.width + other[0], self.height + other[0]
        if len(other) == 2:
            return self.width + other[0], self.height + other[1]
        else:
            raise ValueError("Invalid lenght for multiplication should be 1 or {}.".format(len(self)))

    def __sub__(self, *other):
        if len(other) == 1:
            return self.width - other[0], self.height - other[0]
        if len(other) == 2:
            return self.width - other[0], self.height - other[1]
        else:
            raise ValueError("Invalid lenght for division should be 1 or {}.".format(len(self)))

    def __mul__(self, other):
        if len(other) == 1:
            return self.width * other[0], self.height * other[0]
        if len(other) == 2:
            return self.width * other[0], self.height * other[1]
        else:
            raise ValueError("Invalid lenght for multiplication should be 1 or {}.".format(len(self)))

    def __truediv__(self, other):
        if len(other) == 1:
            return self.width / other[0], self.height / other[0]
        if len(other) == 2:
            return self.width / other[0], self.height / other[1]
        else:
            raise ValueError("Invalid lenght for division should be 1 or {}.".format(len(self)))

    def __getitem__(self, item):
        return self.size[item]

    def __len__(self):
        return len(self.size)

    def __str__(self):
        return str(self.size)

    def copy(self):
        return Size(self.width, self.height)

class Gaussian:
    def __init__(self, mean, sd):
        self.mean = mean
        self.sd = sd

    def probability_density(self, x):
        """
        Calculate the probability of encountering x given self.mean and
        self.sd

        :param x: a real number
        :return: a probability between 0 and 1
        """
        #The probability density for a Gaussian distribution
        probability = (1 / sqrt(2 * pi * self.sd ** 2)) * (e ** (- 0.5 * (x - self.mean) ** 2 / self.sd ** 2))
        return probability