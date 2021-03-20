#!/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import ClassVar, List, Dict

# own imports
import block_classes.materials as base_materials
import utility.image_handling
import utility.utilities as util
import utility.constants as con


class EnvironmentMaterial(base_materials.TransportableMaterial, ABC):
    """Class for materials that are part of the environment of the board"""
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 100

    START_DIRECTION: int

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def START_DIRECTION(self) -> int:
        # direction of connection 0-3 N, E, S, W
        pass


class Fern(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (30, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (30, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class Reed(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (40, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (40, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class Moss(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(40, 10)
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (90, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (90, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class BrownShroom(EnvironmentMaterial, base_materials.ImageMaterial):
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (50, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (50, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class BrownShroomers(EnvironmentMaterial, base_materials.ImageMaterial):
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class RedShroom(EnvironmentMaterial, base_materials.ImageMaterial):
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (80, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (80, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class RedShroomers(EnvironmentMaterial, base_materials.ImageMaterial):
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (60, 20), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (60, 20), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class ShroomCollection(base_materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[base_materials.BaseMaterial, float]] = \
        {BrownShroom: 0.4, BrownShroomers: 0.1, RedShroom: 0.4, RedShroomers: 0.1}
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(80, 10)


class Icicle(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    START_DIRECTION: ClassVar[int] = 0
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (20, 30), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (20, 30), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class SnowLayer(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 50)
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (30, 30), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (30, 30), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class MultiFloraMaterial(EnvironmentMaterial, ABC):
    # the index that the plant grows that side N, E, S, W order, default is north (up)
    CONTINUATION_DIRECTION: ClassVar[int] = 0
    MAX_SIZE: ClassVar[int] = 6
    # default no growth
    GROW_CHANCE: ClassVar[float] = 0.0


class Vine(MultiFloraMaterial, base_materials.DepthMaterial, base_materials.MultiImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(30, 10)
    START_DIRECTION: ClassVar[int] = 0
    CONTINUATION_DIRECTION: ClassVar[int] = 2
    # -1 key is reserved for the starting image, 0-3 for the direction of addition
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        {-1: utility.image_handling.ImageDefinition("materials", (0, 30), flip=(True, False)),
         2: utility.image_handling.ImageDefinition("materials", (10, 30), flip=(True, False))}
    GROW_CHANCE: ClassVar[float] = 0.1
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (10, 30), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class SlimeBush(EnvironmentMaterial, base_materials.DepthMaterial, base_materials.ImageMaterial):
    DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 10)
    START_DIRECTION: ClassVar[int] = 2
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 30), flip=(True, False))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (70, 30), flip=(True, False),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)
