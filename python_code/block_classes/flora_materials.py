from abc import ABC, abstractmethod
from random import choice

import pygame

from block_classes.materials import ImageMaterial, MaterialCollection
from utility.image_handling import image_sheets


class FloraMaterial(ImageMaterial, ABC):

    #default no growth
    GROW_CHANCE = 0
    # the index that the plant grows that side N, E, S, W order, default is north (up)
    CONTINUATION_DIRECTION = 0
    MAX_SIZE = 1
    #TODO make unique per plants
    _BASE_TRANSPARANT_GROUP = 100

    @property
    @abstractmethod
    def LOCATION_INFORMATION(self):
        #information about location of images on the image sheets
        return tuple

    def _configure_surface(self, image):
        image1 = image_sheets["materials"].image_at(self.LOCATION_INFORMATION)
        image2 = pygame.transform.flip(image1, True, False)
        return [image1, image2]

    @property
    def surface(self):
        #this requires the self._surface to be an itterable
        return choice(self._surface)

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
    def START_DIRECTION(self):
        #direction of connection 0-3 N, E, S, W
        return -1


class Fern(FloraMaterial):

    MEAN_DEPTH = 30
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (30, 20)


class Reed(FloraMaterial):

    MEAN_DEPTH = 30
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (40, 20)


class Moss(FloraMaterial):

    MEAN_DEPTH = 40
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (90, 20)


class BrownShroom(FloraMaterial):

    MEAN_DEPTH= 80
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (50, 20)


class BrownShroomers(FloraMaterial):

    MEAN_DEPTH= 80
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (70, 20)


class RedShroom(FloraMaterial):

    MEAN_DEPTH= 80
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (80, 20)


class RedShroomers(FloraMaterial):

    MEAN_DEPTH = 80
    SD = 10
    START_DIRECTION = 2
    LOCATION_INFORMATION = (60, 20)


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
    MEAN_DEPTH = 30
    SD = 10
    START_DIRECTION = 0
    CONTINUATION_DIRECTION = 2
    #-1 key is reserved for the starting image, 0-3 for the direction of addition
    LOCATION_INFORMATION = {-1:(0, 30), 2:(10, 30)}
    GROW_CHANCE = 0.1