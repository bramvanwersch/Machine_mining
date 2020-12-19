#!/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import Tuple, ClassVar, Dict, List
from random import randint

# own imports
import block_classes.materials as base_materials
import utility.utilities as util


class FillerMaterial(ABC):
    """Purely for filtering purposes"""
    pass


class TopDirt(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((137, 79, 33))


class Stone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 155, 155))


class GreenStone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((126, 155, 126))


class RedStone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 126, 126))


class BlueStone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((126, 126, 155))


class YellowStone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 155, 126))


class StoneCollection(base_materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {Stone: 0.95, GreenStone: 0.01, RedStone:  0.01, BlueStone: 0.01, YellowStone: 0.01}


class Granite(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 10
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 7)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((105, 89, 76))


class FinalStone(FillerMaterial, base_materials.DepthMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 20
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((199, 127, 195))


class Dirt(base_materials.ColorMaterial):
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((107, 49, 13))


class OreMaterial(base_materials.DepthMaterial, ABC):
    WHEIGHT: ClassVar[int] = 2
    HARDNESS: ClassVar[int] = 5

    CLUSTER_SIZE: Tuple[int, int]

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
    FUEL_VALUE: int

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FUEL_VALUE(self) -> int:
        pass


class Iron(OreMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 30)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 10)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((184, 98, 92))
    WHEIGHT: ClassVar[int] = 3


class Gold(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 3)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 6)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((235, 173, 16))
    WHEIGHT: ClassVar[int] = 5


class Zinc(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(20, 5)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 15)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((58, 90, 120))


class Copper(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 4
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (5, 8)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((189, 99, 20))


class Coal(OreMaterial, Burnable, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(10, 50)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (6, 12)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((10, 10, 10))
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    FUEL_VALUE: ClassVar[int] = 5


class Titanium(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 50
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (1, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((152, 196, 237))
    WHEIGHT: ClassVar[int] = 10


class IronIngot(base_materials.Unbuildable, base_materials.ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (70, 10))


class GoldIngot(base_materials.Unbuildable, base_materials.ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (80, 10))


class ZincIngot(base_materials.Unbuildable, base_materials.ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (90, 10))


class CopperIngot(base_materials.Unbuildable, base_materials.ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (0, 20))


class TitaniumIngot(base_materials.Unbuildable, base_materials.ImageMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (10, 20))
