from pygame import Rect
from typing import Set, TYPE_CHECKING
import types
from math import pi, e, sqrt, erfc
from abc import ABC
from time import time_ns
from numpy import array, linalg, exp
import inspect
import uuid


if TYPE_CHECKING:
    from block_classes.blocks import Block


def unique_id():
    """Create a unique ID based using the time module"""
    return str(uuid.uuid4())


class BlockPointer:
    """Super simple wrapper around a block class that allows to return a pointer to a block. In this way methods that
    want to retrieve blocks from the original matrix and not repeadatly do that is now possible"""
    __slots__ = "block"

    block: "Block"

    def __init__(self, block: "Block"):
        if isinstance(block, BlockPointer):
            block = block.block
        super().__setattr__("block", block)

    def __getattr__(self, item: str):
        try:
            return getattr(self.block, item)
        except AttributeError:
            raise(AttributeError(f"{type(self.block)} has no attribute {item}"))

    def __setattr__(self, key, value):
        try:
            setattr(self.block, key, value)
        except AttributeError:
            raise(AttributeError(f"{type(self.block)} has no attribute {key}"))

    def __hash__(self):
        return hash(self.block)

    def __eq__(self, other):
        return self.block.__eq__(other)

    def set_block(self, block: "Block"):
        super().__setattr__("block", block)


class GameException(Exception):
    pass


class NotImplementedWarning(UserWarning):
    pass


class ConsoleReadable(ABC):
    """Methods that a class that is usable for certain console commands has"""

    def printables(self) -> Set[str]:
        """Return a list of variable names that are allowed printable, default is all public varaible names"""
        return {name for name, method in inspect.getmembers(self) if not name.startswith("_")
                and not isinstance(method, types.MethodType)}

    def setables(self) -> Set[str]:
        """Return a list of varaible names that are allowed to be changed trough the console. The default is all the
        printable values"""
        return self.printables()


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
        try:
            values[index] = val / total * scale
        except ZeroDivisionError:
            values[index] = 0
    return values


def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def eucledian_distance(p1, p2):
    return sqrt(abs(p1[1] - p2[1]) ** 2 + abs(p1[0] - p2[0]) ** 2)


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
    return Rect((start_pos[0], start_pos[1], size[0], size[1]))


def line_from_points(point1, point2):
    a = (point2[1] - point1[1]) / (point2[0] - point1[0])
    b = point1[1] - a * point1[0]
    return a, b


def side_by_side(rect1, rect2):
    """
    Check if two rectangles are side by side and are touching.

    :param rect1: pygame rect 1
    :param rect2:  pygame rect 2
    :return: a number giving a direction index that coresponds to the list
    [N, E, S, W] or None if not side by side
    """

    if rect1.bottom == rect2.top:
        if (rect1.left <= rect2.left < rect1.right) or\
                (rect1.left < rect2.right <= rect1.right):
            return 2
        elif (rect2.left <= rect1.left < rect2.right) or \
                (rect2.left < rect1.right <= rect2.right):
            return 2
    elif rect1.top == rect2.bottom:
        if (rect1.left <= rect2.left < rect1.right) or\
                (rect1.left < rect2.right <= rect1.right):
            return 0
        elif (rect2.left <= rect1.left < rect2.right) or \
                (rect2.left < rect1.right <= rect2.right):
            return 0
    elif rect1.right == rect2.left:
        if (rect1.top <= rect2.top < rect1.bottom) or \
                (rect1.top < rect2.bottom <= rect1.bottom):
            return 1
        elif (rect2.top <= rect1.top < rect2.bottom) or \
                (rect2.top < rect1.bottom <= rect2.bottom):
            return 1
    elif rect1.left == rect2.right:
        if (rect1.top <= rect2.top < rect1.bottom) or \
                (rect1.top < rect2.bottom <= rect1.bottom):
            return 3
        elif (rect2.top <= rect1.top < rect2.bottom) or \
                (rect2.top < rect1.bottom <= rect2.bottom):
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

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)

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

    # general
    def __len__(self):
        return len(self.size)

    def __str__(self):
        return str(self.size)

    def copy(self):
        return Size(self.width, self.height)


class Gaussian:
    __slots__ = "sd", "mean"

    def __init__(self, mean, sd):
        self.mean = mean
        self.sd = sd

    def to_dict(self):
        return {
            "mean": self.mean,
            "sd": self.sd
        }

    @classmethod
    def from_dict(cls, dct):
        return cls(dct["mean"], dct["sd"])

    def probability(self, x):
        """Give the probability of encountering x exactly"""
        probability = (1 / sqrt(2 * pi * self.sd ** 2)) * (e ** (- 0.5 * (x - self.mean) ** 2 / self.sd ** 2))
        return probability

    def cumulative_probability(self, x):
        two_sided = erfc((x - self.mean) / (self.sd * sqrt(2)))
        return two_sided

    def ci_95(self):
        """95% confidence intervall using 1.96 standard deviations from the mean as estimate"""
        return [self.mean - 1.96 * self.sd, self.mean + 1.96 * self.sd]


class TwoDimensionalGaussian:
    """Special multivariate 2D case with symetrical variance resulting in circular/oval shape based on sigmas"""
    __slots__ = "means", "sigmas", "covariance_matrix", "inv_covariance_matrix", "determinant", "norm_constant"

    def __init__(self, gaussian1, gaussian2, covariance1=0, covariance2=0):
        self.means = array([[gaussian1.mean], [gaussian2.mean]])
        self.sigmas = array([[gaussian1.sd], [gaussian2.sd]])
        self.covariance_matrix = array([[gaussian1.sd, covariance1], [covariance2, gaussian2.sd]])
        self.inv_covariance_matrix = linalg.inv(self.covariance_matrix)
        self.determinant = linalg.det(self.covariance_matrix)
        self.norm_constant = 1 / (((2 * pi) ** (len(self.means) / 2)) * (self.determinant ** 0.5))

    def to_dict(self):
        return {
            "gaussian1": {"mean": self.means[0][0], "sd": self.sigmas[0][0]},
            "gaussian2": {"mean": self.means[1][0], "sd": self.sigmas[1][0]},
            "covariance1": self.covariance_matrix[0][1],
            "covariance2": self.covariance_matrix[1][0],
        }

    @classmethod
    def from_dict(cls, dct):
        gaussian1 = Gaussian.from_dict(dct["gaussian1"])
        gaussian2 = Gaussian.from_dict(dct["gaussian2"])
        return cls(gaussian1, gaussian2, dct["covariance1"], dct["covariance2"])

    def probability(self, x, y):
        x = array([[x], [y]])
        x_mu = array(x - self.means)
        part2 = -0.5 * (x_mu.T.dot(self.inv_covariance_matrix).dot(x_mu))
        return float(self.norm_constant * exp(part2))


def is_abstract(cls):
    """Check if a class is abstract by checking for attribute __abstractmethods__,
    https://stackoverflow.com/questions/14410860/determine-if-a-python-class-is-an-abstract-base-class-or-concrete"""
    return bool(getattr(cls, "__abstractmethods__", False))
