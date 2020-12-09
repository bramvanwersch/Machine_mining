from abc import ABC
from typing import ClassVar, List

from block_classes.blocks import NetworkBlock
from block_classes.materials import ImageMaterial, MultiImageMaterial, BaseMaterial, Indestructable, ImageDefinition
from utility.constants import MODES
from utility.image_handling import image_sheets


class BuildingMaterial(ABC):
    """
    Abstraction level for all building allows for rapid identification
    """
    ALLOWED_TASKS = {task for task in BaseMaterial.ALLOWED_TASKS if task not in ["Building"]}

    F


class TerminalMaterial(Indestructable, MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP = 2
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = {1: ImageDefinition("buildings", (0, 0)),
                                                          2: ImageDefinition("buildings", (10, 0)),
                                                          3: ImageDefinition("buildings", (0, 10)),
                                                          4: ImageDefinition("buildings", (10, 10))}


class FurnaceMaterial(BuildingMaterial, MultiImageMaterial):
    TEXT_COLOR = (255,255,255)
    _BASE_TRANSPARANT_GROUP = 3


class FactoryMaterial(BuildingMaterial, MultiImageMaterial):
    TEXT_COLOR = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP = 4


class StonePipeMaterial(BuildingMaterial, MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP = 5
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
        images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10))[0]
        images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10))[0])
        return {self.__IMAGE_NAMES[i] : images[i] for i in range(len(images))}

    @property
    def surface(self):
        return self._surface[self.image_key]


class StoneBrickMaterial(ImageMaterial):

    HARDNESS = 4
    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0,0))
        return image