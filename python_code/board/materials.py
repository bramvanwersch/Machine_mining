import pygame, sys, inspect
from abc import ABC, abstractmethod
from random import randint, choices

from python_code.utility.constants import MODES, BLOCK_SIZE, SHOW_BLOCK_BORDER, MULTI_TASKS
from python_code.utility.image_handling import image_sheets
from python_code.utility.utilities import Gaussian
from python_code.board.blocks import *


fuel_materials = []
ore_materials = []
filler_materials = []
flora_materials = []

def configure_material_collections():
    global fuel_materials, ore_materials, filler_materials, flora_materials
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(obj, FuelMaterial) and obj != FuelMaterial:
            fuel_materials.append(obj)
        elif issubclass(obj, OreMaterial) and obj != OreMaterial:
            ore_materials.append(obj)
        elif issubclass(obj, FillerMaterial) and obj != FillerMaterial:
            filler_materials.append(obj)
        elif issubclass(obj, FloraMaterial) and obj != FloraMaterial:
            flora_materials.append(obj)


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
        self.surface = self._configure_surface(image)
        self.transparant_group = self.TRANSPARANT_GROUP
        self.unbuildable = False

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

    def mining_speed(self):
        """
        Return the task time plus a small random factor. To stagger the
        calculation times up to 10% of the task_time

        :return: the task time that the task will take in total
        """
        return self.HARDNESS * self.MINING_SPEED_PER_HARDNESS


class MaterialCollection(ABC):
    # class that holds a collection of items that can be selected with a certain wheight

    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self):
        return None

    @classmethod
    def name(self):
        return choices([k.name() for k in self.MATERIAL_PROBABILITIES.keys()],
                self.MATERIAL_PROBABILITIES.values(), k=1)[0]


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
        #TODO see waht to do with the depth stat
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

#filler materials
class FillerMaterial(ABC):

    @property
    @abstractmethod
    def MEAN_DEPTH(self):
        return

    @property
    @abstractmethod
    def SD(self):
        return


class TopDirt(ColorMaterial, FillerMaterial):

    MEAN_DEPTH = 0
    SD = 2
    BASE_COLOR = (137, 79, 33)


class Stone(ColorMaterial):

    HARDNESS = 3
    BASE_COLOR = (155, 155, 155)


class GreenStone(ColorMaterial):

    HARDNESS = 3
    BASE_COLOR = (126, 155, 126)


class RedStone(ColorMaterial):

    HARDNESS = 3
    BASE_COLOR = (155, 126, 126)


class BlueStone(ColorMaterial):

    HARDNESS = 3
    BASE_COLOR = (126, 126, 155)


class YellowStone(ColorMaterial):

    HARDNESS = 3
    BASE_COLOR = (155, 155, 126)


class StoneCollection(MaterialCollection, FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    MATERIAL_PROBABILITIES = {Stone:0.95, GreenStone:0.01, RedStone:0.01, BlueStone:0.01, YellowStone:0.01}


class Granite(ColorMaterial, FillerMaterial):

    HARDNESS = 10
    MEAN_DEPTH = 70
    SD = 7
    BASE_COLOR = (105, 89, 76)


class FinalStone(ColorMaterial, FillerMaterial):

    HARDNESS = 20
    MEAN_DEPTH = 100
    SD = 2
    BASE_COLOR = (199, 127, 195)


class Dirt(ColorMaterial):

    BASE_COLOR = (107, 49, 13)


#ore materials
class OreMaterial(ColorMaterial, ABC):
    """
    Abstract class for all ores. Contains a gaussian distribution for the
    likelyhood of a ore to be at certain percent depth
    """
    WHEIGHT = 2
    HARDNESS = 5

    def _configure_color(self):
        """
        Make sure the color is not changed to make clearer what is a certain ore

        :return: the base color
        """
        return self.BASE_COLOR

    @property
    @abstractmethod
    def MEAN_DEPTH(self):
        return 0

    @property
    @abstractmethod
    def SD(self):
        return 0

    @property
    @abstractmethod
    def CLUSTER_SIZE(self):
        return


class FuelMaterial(ABC):

    @property
    @abstractmethod
    def FUEL_VALUE(self):
        return 0


class Iron(OreMaterial):

    MEAN_DEPTH = 50
    SD = 30
    CLUSTER_SIZE = (2, 10)
    BASE_COLOR = (184, 98, 92)
    WHEIGHT = 3


class Gold(OreMaterial):

    HARDNESS = 3
    MEAN_DEPTH = 70
    SD = 3
    CLUSTER_SIZE = (2, 6)
    BASE_COLOR = (235, 173, 16)
    WHEIGHT = 5


class Zinc(OreMaterial):

    HARDNESS = 3
    MEAN_DEPTH = 20
    SD = 5
    CLUSTER_SIZE = (2, 15)
    BASE_COLOR = (58, 90, 120)


class Copper(OreMaterial):

    HARDNESS = 4
    MEAN_DEPTH = 30
    SD = 5
    CLUSTER_SIZE = (5, 8)
    BASE_COLOR = (189, 99, 20)


class Coal(OreMaterial, FuelMaterial):

    MEAN_DEPTH = 10
    SD = 50
    CLUSTER_SIZE = (6, 12)
    BASE_COLOR = (10, 10, 10)
    TEXT_COLOR = (255,255,255)
    FUEL_VALUE = 5


class Titanium(OreMaterial):

    HARDNESS = 50
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


class FloraMaterial(ImageMaterial, ABC):

    @property
    @abstractmethod
    def MEAN_DEPTH(self):
        return 0

    @property
    @abstractmethod
    def SD(self):
        return 0

    @property
    @abstractmethod
    def DIRECTION(self):
        #direction of connection 0-3 N, E, S, W
        return -1


class Fern(FloraMaterial):

    MEAN_DEPTH = 30
    SD = 10
    DIRECTION = 2

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((30,20), color_key=(255, 255, 255))
        return image


class Reed(FloraMaterial):

    MEAN_DEPTH = 30
    SD = 10
    DIRECTION = 2

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((40,20), color_key=(255, 255, 255))
        return image


class BrownShroom(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((50,20), color_key=(255, 255, 255))
        return image


class BrownShroomers(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((70,20), color_key=(255, 255, 255))
        return image


class RedShroom(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((80,20), color_key=(255, 255, 255))
        return image


class RedShroomers(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((60,20), color_key=(255, 255, 255))
        return image


class ShroomCollection(MaterialCollection, FloraMaterial):

    MEAN_DEPTH= 80
    SD = 10
    DIRECTION = 2
    MATERIAL_PROBABILITIES = {BrownShroom:0.4, BrownShroomers:0.1, RedShroom:0.4, RedShroomers:0.1}


class CancelMaterial(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((20,20), color_key=(255, 255, 255))
        return image

#craftables
class StoneBrickMaterial(ImageMaterial):

    HARDNESS = 4
    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0,0))
        return image


class UnbuildableMaterial(ImageMaterial):
    ALLOWED_TASKS = ["Fetch", "Request", "Deliver"]

    def __init__(self):
        super().__init__()
        self.unbuildable = True


class IronIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((70, 10), color_key=(255, 255, 255))
        return image


class GoldIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((80, 10), color_key=(255, 255, 255))
        return image


class ZincIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((90, 10), color_key=(255, 255, 255))
        return image


class CopperIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0, 20), color_key=(255, 255, 255))
        return image


class TitaniumIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((10, 20), color_key=(255, 255, 255))
        return image


class BuildingMaterial(ImageMaterial, ABC):
    """
    Abstraction level for all building materials, at the moment is useless
    """
    ALLOWED_TASKS = ALLOWED_TASKS = [task for task in MULTI_TASKS if task not in ["Building"]]


class TerminalMaterial(BuildingMaterial):
    #make sure it is indestructible
    ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name not in ["Building", "Mining"]] + ["Empty inventory"]
    TRANSPARANT_GROUP = 2


class FurnaceMaterial(BuildingMaterial):
    TEXT_COLOR = (255,255,255)
    TRANSPARANT_GROUP = 3


class FactoryMaterial(BuildingMaterial):
    TEXT_COLOR = (255, 255, 255)
    TRANSPARANT_GROUP = 4


class StonePipeMaterial(ImageMaterial):
    TRANSPARANT_GROUP = 5
    BLOCK_TYPE = NetworkBlock

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((10,0), color_key=(255,255,255))
        return image
