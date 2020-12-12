

# library imports
from abc import ABC, abstractmethod
from typing import Tuple, ClassVar, Dict, List
from random import randint

# own imports
from block_classes.materials import MaterialCollection, ColorMaterial, Unbuildable, ImageMaterial, DepthMaterial,\
    BaseMaterial, ImageDefinition, ColorDefinition
from utility.utilities import Gaussian
from utility.constants import INVISIBLE_COLOR


class FillerMaterial(ABC):
    """Purely for filtering purposes"""
    pass


class TopDirt(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 2)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((137, 79, 33))


class Stone(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((155, 155, 155))


class GreenStone(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((126, 155, 126))


class RedStone(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((155, 126, 126))


class BlueStone(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((126, 126, 155))


class YellowStone(FillerMaterial, DepthMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((155, 155, 126))


class StoneCollection(MaterialCollection):

    MATERIAL_PROBABILITIES: ClassVar[Dict[BaseMaterial, float]] = \
        {Stone: 0.95, GreenStone: 0.01, RedStone:  0.01, BlueStone: 0.01, YellowStone: 0.01}


class Granite(FillerMaterial, DepthMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 10
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(70, 7)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((105, 89, 76))


class FinalStone(FillerMaterial, DepthMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 20
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(100, 2)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((199, 127, 195))


class Dirt(ColorMaterial):

    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((107, 49, 13))


class OreMaterial(DepthMaterial, ABC):
    WHEIGHT: ClassVar[int] = 2
    HARDNESS: ClassVar[int] = 5

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CLUSTER_SIZE(self) -> Tuple[int, int]:
        pass

    @classmethod
    def get_cluster_size(cls) -> int:
        # noinspection PyArgumentList
        return randint(*cls.CLUSTER_SIZE)


class Burnable(ABC):

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FUEL_VALUE(self) -> int:
        pass


class Iron(OreMaterial, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(50, 30)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 10)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((184, 98, 92))
    WHEIGHT: ClassVar[int] = 3


class Gold(OreMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(70, 3)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 6)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((235, 173, 16))
    WHEIGHT: ClassVar[int] = 5


class Zinc(OreMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(20, 5)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 15)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((58, 90, 120))


class Copper(OreMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 4
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(30, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (5, 8)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((189, 99, 20))


class Coal(OreMaterial, Burnable, ColorMaterial):

    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(10, 50)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (6, 12)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((10, 10, 10))
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    FUEL_VALUE: ClassVar[int] = 5


class Titanium(OreMaterial, ColorMaterial):

    HARDNESS: ClassVar[int] = 50
    DISTRIBUTION: ClassVar[Gaussian] = Gaussian(100, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (1, 2)
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((152, 196, 237))
    WHEIGHT: ClassVar[int] = 10


class IronIngot(Unbuildable, ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (70, 10))


class GoldIngot(Unbuildable, ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (80, 10))


class ZincIngot(Unbuildable, ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (90, 10))


class CopperIngot(Unbuildable, ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (0, 20))


class TitaniumIngot(Unbuildable, ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (10, 20))
