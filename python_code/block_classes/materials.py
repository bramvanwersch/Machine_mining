from abc import abstractmethod
from random import randint, choices

from utility.constants import SHOW_BLOCK_BORDER
from utility.image_handling import image_sheets
from block_classes.blocks import *


class BaseMaterial(ABC):
    """
    Basic functions that are shared by all materials
    """
    WHEIGHT = 1
    #all task types that are allowed to a block with this __material
    ALLOWED_TASKS = MULTI_TASKS
    TEXT_COLOR = (0,0,0)
    #group 0 are not transparant
    TRANSPARANT_GROUP = 0
    MINING_SPEED_PER_HARDNESS = 100 #ms
    HARDNESS = 1

    BLOCK_TYPE = Block
    def __init__(self, image = None, **kwargs):
        """
        :param image: a pygame Surface object that can be an image instead of
        an automatically configured surface
        :param surface: if the material should configure a surface. Interesting
        when treating the materials as more abstract units instead of actual
        surface defining objects.
        """
        self._surface = self._configure_surface(image)
        self.transparant_group = self.TRANSPARANT_GROUP
        self.unbuildable = False

    @classmethod
    def name(self):
        return self.__name__

    @property
    def surface(self):
        #allow inheriting classes to push muliple surfaces or a choice
        return self._surface

    @abstractmethod
    def _configure_surface(self, image):
        """
        Method all material classes should have

        :param image: obtional pre defines pygame Surface object
        :return: a pygame Surface object
        """
        pass

    def mining_speed(self):
        """
        Return the task time plus a small random factor. To stagger the
        calculation times up to 10% of the task_time

        :return: the task time that the task will take in total
        """
        return self.HARDNESS * self.MINING_SPEED_PER_HARDNESS


class MaterialCollection(ABC):
    # class that holds a collection of items that are randomly returned based on wheights
    # this is mainly meant for board generation purposes

    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self):
        return None

    @classmethod
    def name(self):
        return choices([k.name() for k in self.MATERIAL_PROBABILITIES.keys()],
                self.MATERIAL_PROBABILITIES.values(), k=1)[0]

    def __getattr__(self, item):
        return getattr(list(self.MATERIAL_PROBABILITIES.keys())[0], item)

    def __contains__(self, item):
        return item in self.MATERIAL_PROBABILITIES


class Air(BaseMaterial):
    ALLOWED_TASKS = [task for task in MULTI_TASKS if task not in ["Mining"]]
    HARDNESS = 0
    TRANSPARANT_GROUP = 1

    def _configure_surface(self, image):
        """
        Air has no surface
        """
        return None


class ColorMaterial(BaseMaterial, ABC):
    """
    Materials can inherit this when they simply are one color
    """
    MIN_COLOR = (20, 20, 20)

    def __init__(self, **kwargs):
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
            color_component = max(self.MIN_COLOR[index], color_component + random_change)
            new_color[index] = color_component
        return new_color

    def _configure_border_color(self):
        """
        The color of the border that is slightly darker then the base color

        :return: a tuple with a r, g and b value as integers
        """
        new_color = list(self.BASE_COLOR)
        for index, color_component in enumerate(self.BASE_COLOR):
            color_component = max(0, color_component - 30)
            new_color[index] = color_component
        return new_color


class BorderMaterial(ColorMaterial):
    ALLOWED_TASKS = []
    BASE_COLOR = (0,0,0)
    MIN_COLOR = (0,0,0)


#building materials: materials that are special building block_classes like storage containers

class ImageMaterial(BaseMaterial, ABC):
    """
    Materials can inherit from this when displaying an image
    """

    def _configure_surface(self, image):
        """
        Show an image as a surface instead of a single color

        :param image: optional pre defines pygame Surface object
        :return: a python Surface object
        """
        if image != None:
            return image
        #if an image is provided return that otherwise a color
        else:
            surface = pygame.Surface(BLOCK_SIZE)
            surface.fill((0, 255, 13))
            return surface


class CancelMaterial(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((20,20), color_key=(255, 255, 255))
        return image


class UnbuildableMaterial(ImageMaterial):
    ALLOWED_TASKS = ["Fetch", "Request", "Deliver"]

    def __init__(self):
        super().__init__()
        self.unbuildable = True
