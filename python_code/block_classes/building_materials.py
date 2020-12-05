from abc import ABC

from block_classes.blocks import NetworkBlock
from block_classes.materials import ImageMaterial
from utility.constants import MULTI_TASKS, MODES
from utility.image_handling import image_sheets


class BuildingMaterial(ImageMaterial, ABC):
    """
    Abstraction level for all building materials, at the moment is useless
    """
    _ALLOWED_TASKS = [task for task in MULTI_TASKS if task not in ["Building"]]


class TerminalMaterial(BuildingMaterial):
    #make sure it is indestructible
    _ALLOWED_TASKS = [mode.name for mode in MODES.values() if mode.name not in ["Building", "Mining"]] + ["Empty inventory"]
    TRANSPARANT_GROUP = 2


class FurnaceMaterial(BuildingMaterial):
    TEXT_COLOR = (255,255,255)
    TRANSPARANT_GROUP = 3


class FactoryMaterial(BuildingMaterial):
    TEXT_COLOR = (255, 255, 255)
    TRANSPARANT_GROUP = 4


class StonePipeMaterial(ImageMaterial):
    TRANSPARANT_GROUP = 5
    _BLOCK_TYPE = NetworkBlock
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    __IMAGE_NAMES = ["2_13", "2_02", "2_23", "2_03", "2_12", "2_01", "3_013", "3_012", "3_023", "3_123", "4_0123",
                   "1_3", "1_0", "1_1", "1_2", "0_"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_key = "0_"

    def _configure_surface(self, image):
        #TODO at some point in the future make these class varaibles to avoid triggerign on class instantiation
        images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10), color_key=(255,255,255))[0]
        images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10), color_key=(255,255,255))[0])
        return {self.__IMAGE_NAMES[i] : images[i] for i in range(len(images))}

    @property
    def surface(self):
        return self._surface[self.image_key]


class StoneBrickMaterial(ImageMaterial):

    HARDNESS = 4
    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0,0))
        return image