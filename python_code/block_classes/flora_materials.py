from abc import ABC, abstractmethod
from typing import ClassVar, List

import block_classes.materials as base_materials
import utility.utilities as util


class FloraMaterial(base_materials.DepthMaterial, ABC):

    # the index that the plant grows that side N, E, S, W order, default is north (up)
    CONTINUATION_DIRECTION = 0
    # TODO make unique per plants
    _BASE_TRANSPARANT_GROUP = 100

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def START_DIRECTION(self) -> int:
        # direction of connection 0-3 N, E, S, W
        pass


class Fern(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (30, 20), flip=True)


class Reed(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (40, 20), flip=True)


class Moss(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(40, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (90, 20), flip=True)


class BrownShroom(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (50, 20), flip=True)


class BrownShroomers(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (70, 20), flip=True)


class RedShroom(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (80, 20), flip=True)


class RedShroomers(FloraMaterial, base_materials.ImageMaterial):

    DISTRIBUTION = util.Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (60, 20), flip=True)


class ShroomCollection(base_materials.MaterialCollection):

    MATERIAL_PROBABILITIES = {BrownShroom: 0.4, BrownShroomers: 0.1, RedShroom: 0.4, RedShroomers: 0.1}


class MultiFloraMaterial(FloraMaterial, ABC):
    MAX_SIZE = 6
    # default no growth
    GROW_CHANCE = 0


class Vine(MultiFloraMaterial, base_materials.MultiImageMaterial):
    DISTRIBUTION = util.Gaussian(30, 10)
    START_DIRECTION = 0
    CONTINUATION_DIRECTION = 2
    # -1 key is reserved for the starting image, 0-3 for the direction of addition
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        {-1: base_materials.ImageDefinition("materials", (0, 30), flip=True),
         2: base_materials.ImageDefinition("materials", (10, 30), flip=True)}
    GROW_CHANCE = 0.1
