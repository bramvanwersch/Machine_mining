from pygame import Rect, image
from math import pi, e, sqrt

GROUP = 0

def unique_group():
    global GROUP
    group_id = "u{}".format(GROUP)
    GROUP += 1
    return group_id


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

def side_by_side(rect1, rect2):
    """
    Check if two rectangles are side by side and are touching.

    :param rect1: pygame rect 1
    :param rect2:  pygame rect 2
    :return: a number giving a direction index that coresponds to the list
    [N, E, S, W]
    """

    if rect1.bottom == rect2.top:
        if (rect1.left <= rect2.left and rect1.right > rect2.left) or\
            (rect1.left < rect2.right and rect1.right >= rect2.right):
            return 2
        elif (rect2.left <= rect1.left and rect2.right > rect1.left) or \
            (rect2.left < rect1.right and rect2.right >= rect1.right):
            return 2
    elif rect1.top == rect2.bottom:
        if (rect1.left <= rect2.left and rect1.right > rect2.left) or\
            (rect1.left < rect2.right and rect1.right >= rect2.right):
            return 0
        elif (rect2.left <= rect1.left and rect2.right > rect1.left) or \
            (rect2.left < rect1.right and rect2.right >= rect1.right):
            return 0
    elif rect1.right == rect2.left:
        if (rect1.top <= rect2.top and rect1.bottom > rect2.top) or \
            (rect1.top < rect2.bottom and rect1.bottom >= rect2.bottom):
            return 1
        elif (rect2.top <= rect1.top and rect2.bottom > rect1.top) or \
            (rect2.top < rect1.bottom and rect2.bottom >= rect1.bottom):
            return 1
    elif rect1.left == rect2.right:
        if (rect1.top <= rect2.top and rect1.bottom > rect2.top) or \
            (rect1.top < rect2.bottom and rect1.bottom >= rect2.bottom):
            return 3
        elif (rect2.top <= rect1.top and rect2.bottom > rect1.top) or \
            (rect2.top < rect1.bottom and rect2.bottom >= rect1.bottom):
            return 3
    else:
        return None


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

#calculating using iterable objects of len 2
    def __add__(self, other):
        try:
            if len(other) == 2:
                return Size(self.width + other[0], self.height + other[1])
        except TypeError as e:
            print(e)
        raise ValueError("Expected value of lenght 2. Got {}".format(type(other)))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        try:
            if len(other) == 2:
                return Size(self.width - other[0], self.height - other[1])
        except TypeError as e:
            print(e)
        raise ValueError("Expected value of lenght 2. Got {}".format(type(other)))

    def __rsub__(self, other):
        try:
            if len(other) == 2:
                return Size(other[0] - self.width, other[1] - self.height)
        except TypeError as e:
            print(e)
        raise ValueError("Expected value of lenght 2. Got {}".format(type(other)))

    def __mul__(self, other):
        try:
            if len(other) == 2:
                return Size(self.width * other[0], self.height * other[1])
        except TypeError as e:
            print(e)
        raise ValueError("Invalid lenght for multiplication should be 1 or {}.".format(len(self)))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        try:
            if len(other) == 2:
                return Size(self.width / other[0], self.height / other[1])
        except TypeError as e:
            print(e)
        raise ValueError("Invalid lenght for division should be 1 or {}.".format(len(self)))

    def __rtruediv__(self, other):
        try:
            if len(other) == 2:
                return Size(other[0] / self.width, other[1] / self.height)
        except TypeError as e:
            print(e)
        raise ValueError("Invalid lenght for division should be 1 or {}.".format(len(self)))

    def __getitem__(self, item):
        return self.size[item]

#general
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