import pygame
from abc import ABC, abstractmethod
from random import randint

from python_code.utility.constants import MODES, BLOCK_SIZE, SHOW_BLOCK_BORDER
from python_code.utility.image_handling import image_sheets


class BaseMaterial(ABC):
    """
    Basic functions that are shared by all materials
    """
    #time to perform a task on this __material in ms
    TASK_TIME = 250
    WHEIGHT = 1
    #all task types that are allowed to a block with this __material
    ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name ] + ["Empty inventory"]
    TEXT_COLOR = (0,0,0)
    def __init__(self, image = None, **kwargs):
        """
        :param image: a pygame Surface object that can be an image instead of
        an automatically configured surface
        :param surface: if the material should configure a surface. Interesting
        when treating the materials as more abstract units instead of actual
        surface defining objects.
        """
        self.surface = self._configure_surface(image)

    @classmethod
    def name(self):
        return self.__name__

    @abstractmethod
    def _configure_surface(self, image):
        """
        Method all material classes should have

        :param image: obtional pre defines pygame Surface object
        :return: a pygame Surface object
        """
        pass

    def task_time(self):
        """
        Return the task time plus a small random factor. To stagger the
        calculation times up to 10% of the task_time

        :return: the task time that the task will take in total
        """
        return self.TASK_TIME + randint(0, int(0.1 * self.TASK_TIME))


class Air(BaseMaterial):
    ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name not in ["Mining"]]  + ["Empty inventory"]

    def _configure_surface(self, image):
        """
        Air has no surface
        """
        return None


class BuildMaterial(BaseMaterial):
    ALLOWED_TASKS = ["Cancel", "Building"]

    def _configure_surface(self, image):
        """
        No surface
        """
        return None

class ColorMaterial(BaseMaterial, ABC):
    """
    Materials can inherit this when they simply are one color
    """
    MIN_COLOR = (20, 20, 20)

    def __init__(self, depth = 0, **kwargs):
        self._depth = depth
        self.__color = self._configure_color()
        self.__border_color = self._configure_border_color()
        super().__init__(**kwargs)

    @property
    @abstractmethod
    def BASE_COLOR(self):
        return None

    def _configure_surface(self, image):
        """
        Create a surface that of a single color based on the color of the
        material

        :param image: obtional pre defines pygame Surface object
        :return: a pygame Surface object
        """
        surface = pygame.Surface(BLOCK_SIZE)
        surface.fill(self.__color)
        if SHOW_BLOCK_BORDER:
            pygame.draw.rect(surface, self.__border_color,
                             (0, 0, BLOCK_SIZE.width,
                              BLOCK_SIZE.height), 1)
        return surface.convert()

    def _configure_color(self):
        """
        Create a color that becomes darker when the depth becomes bigger and
        with some random change in color.

        :return: a tuple with a r, g and b value as integers
        """
        new_color = list(self.BASE_COLOR)
        random_change = randint(-10, 10)
        #dont change the alpha channel if present
        for index, color_component in enumerate(self.BASE_COLOR):
            #make the color darker with depth and add a random component to it
            color_component = max(self.MIN_COLOR[index], color_component - int(self._depth / 2) + random_change)
            new_color[index] = color_component
        return new_color

    def _configure_border_color(self):
        """
        The color of the border that is slightly darker then the base color

        :return: a tuple with a r, g and b value as integers
        """
        new_color = list(self.BASE_COLOR)
        for index, color_component in enumerate(self.BASE_COLOR):
            color_component = max(0, color_component - int(self._depth / 2) - 30)
            new_color[index] = color_component
        return new_color


#filler materials
class Stone(ColorMaterial):
    BASE_COLOR = (155, 155, 155)


class Dirt(ColorMaterial):
    BASE_COLOR = (107, 49, 13)



#ore materials
class Ore(ColorMaterial, ABC):
    """
    Abstract class for all ores. Contains a gaussian distribution for the
    likelyhood of a ore to be at certain percent depth
    """
    WHEIGHT = 2


    def _configure_color(self):
        """
        Make sure the color is not changed to make clearer what is a certain ore

        :return: the base color
        """
        return self.BASE_COLOR

class Iron(Ore):

    MEAN_DEPTH = 50
    SD = 30
    CLUSTER_SIZE = (2, 10)
    BASE_COLOR = (184, 98, 92)
    WHEIGHT = 3


class Gold(Ore):

    MEAN_DEPTH = 70
    SD = 3
    CLUSTER_SIZE = (2, 6)
    BASE_COLOR = (235, 173, 16)
    WHEIGHT = 5


class Zinc(Ore):

    MEAN_DEPTH = 20
    SD = 5
    CLUSTER_SIZE = (2, 15)
    BASE_COLOR = (58, 90, 120)


class Copper(Ore):

    MEAN_DEPTH = 30
    SD = 5
    CLUSTER_SIZE = (5, 8)
    BASE_COLOR = (189, 99, 20)


class Coal(Ore):

    MEAN_DEPTH = 10
    SD = 50
    CLUSTER_SIZE = (6, 12)
    BASE_COLOR = (10, 10, 10)
    TEXT_COLOR = (255,255,255)


class Titanium(Ore):

    MEAN_DEPTH = 100
    SD = 2
    CLUSTER_SIZE = (1, 2)
    BASE_COLOR = (152, 196, 237)
    WHEIGHT = 10

#building materials: materials that are special building blocks like storage containers

class ImageMaterial(BaseMaterial, ABC):
    """
    Materials can inherit from this when displaying an image
    """

    def _configure_surface(self, image):
        """
        Show an image as a surface instead of a single color

        :param image: obtional pre defines pygame Surface object
        :return: a python Surface object
        """
        if image != None:
            return image
        #if an image is provided return that otherwise a color
        else:
            surface = pygame.Surface(BLOCK_SIZE)
            surface.fill((0, 255, 13))
            return surface

#craftables
class StoneBrickMaterial(ImageMaterial):
    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0,0))
        return image


class BuildingMaterial(ImageMaterial, ABC):
    """
    Abstraction level for all building materials, at the moment is useless
    """
    ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name not in ["Building"]]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TerminalMaterial(BuildingMaterial):
    #make sure it is indestructible
    ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name not in ["Building", "Mining"]] + ["Empty inventory"]
    TASK_TIME = 200


class FurnaceMaterial(BuildingMaterial):
    TASK_TIME = 1000
    TEXT_COLOR = (255,255,255)


class StonePipeMaterial(ImageMaterial):
    TASK_TIME = 1000
    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((10,0), color_key=(255,255,255))
        return image
