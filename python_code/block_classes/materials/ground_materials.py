#!/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import Tuple, ClassVar, Dict, List
from random import randint

# own imports
import block_classes.materials.materials as base_materials
import utility.image_handling
import utility.utilities as util
import utility.constants as con


class Dirt(base_materials.DepthMaterial, base_materials.ColorMaterial, base_materials.TransportableMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(0, 10)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((137, 79, 33))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((137, 79, 33), image_size=con.TRANSPORT_BLOCK_SIZE)


class Stone(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 155, 155))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((155,155, 155), image_size=con.TRANSPORT_BLOCK_SIZE)


class GreenStone(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((126, 155, 126))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((126, 155, 126), image_size=con.TRANSPORT_BLOCK_SIZE)


class RedStone(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 126, 126))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((155, 126, 126), image_size=con.TRANSPORT_BLOCK_SIZE)


class BlueStone(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((126, 126, 155))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((126, 126, 155), image_size=con.TRANSPORT_BLOCK_SIZE)


class YellowStone(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 3
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((155, 155, 126))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((155, 155, 126), image_size=con.TRANSPORT_BLOCK_SIZE)


class StoneCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {Stone: 0.95, GreenStone: 0.01, RedStone:  0.01, BlueStone: 0.01, YellowStone: 0.01}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)


class Granite(base_materials.DepthMaterial, base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 10
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 7)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((105, 89, 76))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((105, 89, 76), image_size=con.TRANSPORT_BLOCK_SIZE)


class FinalStone(base_materials.DepthMaterial, base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 20
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((199, 127, 195))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((199, 127, 195), image_size=con.TRANSPORT_BLOCK_SIZE)


class BasicIce(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 1
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((74, 131, 168))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((74, 131, 168), image_size=con.TRANSPORT_BLOCK_SIZE)


class Snow(base_materials.ColorMaterial, base_materials.TransportableMaterial):
    HARDNESS: ClassVar[int] = 1
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((193, 197, 199))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((193, 197, 199), image_size=con.TRANSPORT_BLOCK_SIZE)


class DirtIceCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {BasicIce: 0.5, Snow: 0.45, Dirt: 0.05}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(0, 10)


class StoneIceCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {BasicIce: 0.5, Snow: 0.45, Stone: 0.05}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)


class GraniteIceCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {BasicIce: 0.45, Snow: 0.40, Granite: 0.15}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 7)


class FinalIceCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {BasicIce: 0.40, Snow: 0.35, FinalStone: 0.25}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)


class BackDirt(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(20, 10)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((97, 39, 3))


class BackStone(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 10)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((55, 55, 55))


class BackFinalStone(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((72, 0, 70))


class BackIce(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((24, 81, 118))


class SlimeBlock1(base_materials.DepthMaterial, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    IMAGE_DEFINITIONS: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (40, 30), flip=(True, True))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (40, 30), flip=(True, True),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class SlimeBlock2(base_materials.DepthMaterial, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    IMAGE_DEFINITIONS: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (50, 30), flip=(True, True))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (50, 30), flip=(True, True),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class DirtSlimeCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {SlimeBlock1: 0.48, SlimeBlock2: 0.48, Dirt: 0.04}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(0, 10)


class StoneSlimeCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {SlimeBlock1: 0.48, SlimeBlock2: 0.48, Stone: 0.04}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)


class GraniteSlimeCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {SlimeBlock1: 0.46, SlimeBlock2: 0.46, Granite: 0.08}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 7)


class FinalSlimeCollection(base_materials.MaterialDepthCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {SlimeBlock1: 0.45, SlimeBlock2: 0.45, FinalStone: 0.10}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)


class BackSlime1(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((6, 99, 31))


class BackSlime2(base_materials.DepthMaterial, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((36, 120, 59))


class OreMaterial(base_materials.DepthMaterial, base_materials.TransportableMaterial, ABC):
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
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((184, 98, 92), image_size=con.TRANSPORT_BLOCK_SIZE)


class Gold(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(70, 3)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 6)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((235, 173, 16))
    WHEIGHT: ClassVar[int] = 5
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((235, 173, 16), image_size=con.TRANSPORT_BLOCK_SIZE)


class Zinc(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 3
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(20, 5)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (2, 15)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((58, 90, 120))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((58, 90, 120), image_size=con.TRANSPORT_BLOCK_SIZE)


class Copper(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 4
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (5, 8)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((189, 99, 20))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((189, 99, 20), image_size=con.TRANSPORT_BLOCK_SIZE)


class Coal(OreMaterial, Burnable, base_materials.ColorMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(10, 50)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (6, 12)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((10, 10, 10))
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    FUEL_VALUE: ClassVar[int] = 5
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((10, 10, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class Titanium(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 50
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(100, 2)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (1, 2)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((152, 196, 237))
    WHEIGHT: ClassVar[int] = 10
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((152, 196, 237), image_size=con.TRANSPORT_BLOCK_SIZE)


class Oralchium(OreMaterial, base_materials.ColorMaterial):
    HARDNESS: ClassVar[int] = 30
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    CLUSTER_SIZE: ClassVar[Tuple[int, int]] = (5, 10)
    COLOR_DEFINITIONS: ClassVar[base_materials.ColorDefinition] = base_materials.ColorDefinition((0, 255, 70))
    WHEIGHT: ClassVar[int] = 3
    TRANSPORT_IMAGE_DEFINITION: ClassVar[base_materials.ColorDefinition] = \
        base_materials.ColorDefinition((0, 255, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class IronIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 10))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class GoldIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (80, 10))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (80, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class ZincIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (90, 10))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (90, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class CopperIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (0, 20))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (0, 20), image_size=con.TRANSPORT_BLOCK_SIZE)


class TitaniumIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (10, 20))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (10, 20), image_size=con.TRANSPORT_BLOCK_SIZE)


class OralchiumIngot(base_materials.Unbuildable, base_materials.ImageMaterial, base_materials.TransportableMaterial):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (60, 30), image_size=con.TRANSPORT_BLOCK_SIZE)
