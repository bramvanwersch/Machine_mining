from abc import ABC, abstractmethod
from random import choice
from typing import ClassVar, Dict

import pygame

from block_classes.materials import ImageMaterial, MaterialCollection, DepthMaterial
from utility.constants import INVISIBLE_COLOR
from utility.utilities import Gaussian


class FloraMaterial(DepthMaterial, ImageMaterial, ABC):

    #default no growth
    GROW_CHANCE = 0
    # the index that the plant grows that side N, E, S, W order, default is north (up)
    CONTINUATION_DIRECTION = 0
    MAX_SIZE = 1
    #TODO make unique per plants
    _BASE_TRANSPARANT_GROUP = 100

    def _configure_surface(self, image):
        image1 = super()._configure_surface(image=image)
        image2 = pygame.transform.flip(image1, True, False)
        return [image1, image2]

    @property
    def surface(self):
        #this requires the self._surface to be an itterable
        return choice(self._surface)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def START_DIRECTION(self) -> int:
        # direction of connection 0-3 N, E, S, W
        pass


class Fern(FloraMaterial):

    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (30, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class Reed(FloraMaterial):

    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (40, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class Moss(FloraMaterial):

    DISTRIBUTION = Gaussian(40, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (90, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class BrownShroom(FloraMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (50, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class BrownShroomers(FloraMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (70, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class RedShroom(FloraMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (80, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class RedShroomers(FloraMaterial):

    DISTRIBUTION = Gaussian(80, 10)
    START_DIRECTION = 2
    IMAGE_SPECIFICATIONS: ClassVar[Dict[str, str]] = {"sheet_name": "materials", "image_location": (60, 20),
                                                      "color_key": INVISIBLE_COLOR[:-1]}


class ShroomCollection(MaterialCollection):

    MATERIAL_PROBABILITIES = {BrownShroom: 0.4, BrownShroomers: 0.1, RedShroom: 0.4, RedShroomers: 0.1}


class MultiFloraMaterial(FloraMaterial, ABC):
    MAX_SIZE = 6

    def __init__(self, image_number=-1, **kwargs):
        super().__init__(**kwargs)
        self.image_key = image_number

    def _configure_surface(self, image):
        images = {}
        for direction, loc in self.LOCATION_INFORMATION.items():
            image = image_sheets["materials"].image_at(loc)
            images[direction] = [image]
            images[direction].append(pygame.transform.flip(image, True, False))
        return images

    @property
    def surface(self):
        #this requires the self._surface to be an itterable
        return choice(self._surface[self.image_key])


class Vine(MultiFloraMaterial):
    DISTRIBUTION = Gaussian(30, 10)
    START_DIRECTION = 0
    CONTINUATION_DIRECTION = 2
    #-1 key is reserved for the starting image, 0-3 for the direction of addition
    LOCATION_INFORMATION = {-1:(0, 30), 2:(10, 30)}
    GROW_CHANCE = 0.1