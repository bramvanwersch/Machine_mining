from abc import ABC, abstractmethod
import pygame
from typing import ClassVar, List, Tuple, Dict

from utility.utilities import Size
from block_classes.blocks import NetworkBlock, BaseBlock, ContainerBlock
from block_classes.materials import ImageMaterial, MultiImageMaterial, BaseMaterial, Indestructable, ImageDefinition


class BuildingMaterial(ABC):
    """
    Abstraction level for all building allows for rapid identification
    """
    ALLOWED_TASKS = {task for task in BaseMaterial.ALLOWED_TASKS if task not in ["Building"]}


class Building(ABC):
    BUILDING: ClassVar[bool] = True

    @property
    def full_surface(self) -> pygame.Surface:
        return self.FULL_SURFACE.images()[0]

    @property
    @abstractmethod
    def FULL_SURFACE(self) -> ImageDefinition:
        pass


class TerminalMaterial(Building, Indestructable, MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP = 2
    _BLOCK_TYPE: ClassVar[BaseBlock] = ContainerBlock
    FULL_SURFACE = ImageDefinition("buildings", (0, 0), size=Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[ImageDefinition]]] = {1: ImageDefinition("buildings", (0, 0)),
                                                                     2: ImageDefinition("buildings", (10, 0)),
                                                                     3: ImageDefinition("buildings", (0, 10)),
                                                                     4: ImageDefinition("buildings", (10, 10))}


class FurnaceMaterial(Building, BuildingMaterial, MultiImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP = 3
    _BLOCK_TYPE: ClassVar[BaseBlock] = ContainerBlock
    FULL_SURFACE = ImageDefinition("buildings", (20, 0), size=Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[ImageDefinition]]] = {1: ImageDefinition("buildings", (20, 0)),
                                                                     2: ImageDefinition("buildings", (30, 0)),
                                                                     3: ImageDefinition("buildings", (20, 10)),
                                                                     4: ImageDefinition("buildings", (30, 10))}


class FactoryMaterial(Building, BuildingMaterial, MultiImageMaterial):
    TEXT_COLOR = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP = 4
    _BLOCK_TYPE: ClassVar[BaseBlock] = ContainerBlock
    FULL_SURFACE = ImageDefinition("buildings", (40, 0), size=Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[ImageDefinition]]] = {1: ImageDefinition("buildings", (40, 0)),
                                                                     2: ImageDefinition("buildings", (50, 0)),
                                                                     3: ImageDefinition("buildings", (40, 10)),
                                                                     4: ImageDefinition("buildings", (50, 10))}


class StonePipeMaterial(BuildingMaterial, MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP = 5
    _BLOCK_TYPE: ClassVar[BaseBlock] = NetworkBlock
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_DEFINITIONS: ClassVar[Dict[str, List[ImageDefinition]]] = {"2_13": ImageDefinition("materials", (10, 0)),
                                                                     "2_02": ImageDefinition("materials", (20, 0)),
                                                                     "2_23": ImageDefinition("materials", (30, 0)),
                                                                     "2_03": ImageDefinition("materials", (40, 0)),
                                                                     "2_12": ImageDefinition("materials", (50, 0)),
                                                                     "2_01": ImageDefinition("materials", (60, 0)),
                                                                     "3_013": ImageDefinition("materials", (70, 0)),
                                                                     "3_012": ImageDefinition("materials", (80, 0)),
                                                                     "3_023": ImageDefinition("materials", (90, 0)),
                                                                     "3_123": ImageDefinition("materials", (0, 10)),
                                                                     "4_0123": ImageDefinition("materials", (10, 10)),
                                                                     "1_3": ImageDefinition("materials", (20, 10)),
                                                                     "1_0": ImageDefinition("materials", (30, 10)),
                                                                     "1_1": ImageDefinition("materials", (40, 10)),
                                                                     "1_2": ImageDefinition("materials", (50, 10)),
                                                                     "0_": ImageDefinition("materials", (60, 10))}

    image_key: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_key = "0_"

    # def _configure_surface(self, image):
    #     #TODO at some point in the future make these class varaibles to avoid triggerign on class instantiation
    #     images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10))[0]
    #     images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10))[0])
    #     return {self.__IMAGE_NAMES[i] : images[i] for i in range(len(images))}


class StoneBrickMaterial(ImageMaterial):

    HARDNESS = 4
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (0, 0))
