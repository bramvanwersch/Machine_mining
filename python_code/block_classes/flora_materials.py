from abc import ABC, abstractmethod
from typing import ClassVar, List

from block_classes.materials import ImageMaterial, MaterialCollection, DepthMaterial,\
    MultiImageMaterial, ImageDefinition
from utility.constants import INVISIBLE_COLOR
from utility.utilities import Gaussian


class FloraMaterial(DepthMaterial, ABC):

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


class Fern(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (30, 20), flip=True)


class Reed(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (40, 20), flip=True)


class Moss(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(40, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (90, 20), flip=True)


class BrownShroom(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (50, 20), flip=True)


class BrownShroomers(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (70, 20), flip=True)


class RedShroom(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (80, 20), flip=True)


class RedShroomers(FloraMaterial, ImageMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (60, 20), flip=True)


class ShroomCollection(MaterialCollection):

    MATERIAL_PROBABILITIES = {BrownShroom: 0.4, BrownShroomers: 0.1, RedShroom: 0.4, RedShroomers: 0.1}


class MultiFloraMaterial(FloraMaterial, ABC):
    MAX_SIZE = 6
    # default no growth
    GROW_CHANCE = 0


class Vine(MultiFloraMaterial, MultiImageMaterial):
    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 0
    CONTINUATION_DIRECTION = 2
    # -1 key is reserved for the starting image, 0-3 for the direction of addition
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = {-1: ImageDefinition("materials", (0, 30), flip=True),
                                                          2: ImageDefinition("materials", (10, 30), flip=True)}
    GROW_CHANCE = 0.1
