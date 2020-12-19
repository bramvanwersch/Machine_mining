#!/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import ClassVar, List, Tuple, Dict, Set
import pygame

# own imports
import utility.utilities as util
import block_classes.blocks as blocks
import block_classes.materials as base_materials


class BuildingMaterial(ABC):
    ALLOWED_TASKS: ClassVar[Set] = {task for task in base_materials.BaseMaterial.ALLOWED_TASKS
                                    if task not in ["Building"]}


class Building(ABC):
    """abstraction level for all buildings"""

    FULL_SURFACE: ClassVar[base_materials.ImageDefinition]

    @property
    def full_surface(self) -> pygame.Surface:
        return self.FULL_SURFACE.images()[0]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FULL_SURFACE(self) -> base_materials.ImageDefinition:
        pass


class TerminalMaterial(Building, base_materials.Indestructable, base_materials.MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 2
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.ContainerBlock
    FULL_SURFACE: ClassVar[base_materials.ImageDefinition] =\
        base_materials.ImageDefinition("buildings", (0, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[base_materials.ImageDefinition]]] = \
        {1: base_materials.ImageDefinition("buildings", (0, 0)),
         2: base_materials.ImageDefinition("buildings", (10, 0)),
         3: base_materials.ImageDefinition("buildings", (0, 10)),
         4: base_materials.ImageDefinition("buildings", (10, 10))}


class FurnaceMaterial(Building, BuildingMaterial, base_materials.MultiImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 3
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.ContainerBlock
    FULL_SURFACE: ClassVar[base_materials.ImageDefinition] = \
        base_materials.ImageDefinition("buildings", (20, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[base_materials.ImageDefinition]]] = \
        {1: base_materials.ImageDefinition("buildings", (20, 0)),
         2: base_materials.ImageDefinition("buildings", (30, 0)),
         3: base_materials.ImageDefinition("buildings", (20, 10)),
         4: base_materials.ImageDefinition("buildings", (30, 10))}


class FactoryMaterial(Building, BuildingMaterial, base_materials.MultiImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 4
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.ContainerBlock
    FULL_SURFACE: ClassVar[base_materials.ImageDefinition] = \
        base_materials.ImageDefinition("buildings", (40, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[base_materials.ImageDefinition]]] = \
        {1: base_materials.ImageDefinition("buildings", (40, 0)),
         2: base_materials.ImageDefinition("buildings", (50, 0)),
         3: base_materials.ImageDefinition("buildings", (40, 10)),
         4: base_materials.ImageDefinition("buildings", (50, 10))}


class StonePipeMaterial(BuildingMaterial, base_materials.MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 5
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.NetworkEdgeBlock
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_DEFINITIONS: ClassVar[Dict[str, List[base_materials.ImageDefinition]]] = \
        {"2_13": base_materials.ImageDefinition("materials", (10, 0)),
         "2_02": base_materials.ImageDefinition("materials", (20, 0)),
         "2_23": base_materials.ImageDefinition("materials", (30, 0)),
         "2_03": base_materials.ImageDefinition("materials", (40, 0)),
         "2_12": base_materials.ImageDefinition("materials", (50, 0)),
         "2_01": base_materials.ImageDefinition("materials", (60, 0)),
         "3_013": base_materials.ImageDefinition("materials", (70, 0)),
         "3_012": base_materials.ImageDefinition("materials", (80, 0)),
         "3_023": base_materials.ImageDefinition("materials", (90, 0)),
         "3_123": base_materials.ImageDefinition("materials", (0, 10)),
         "4_0123": base_materials.ImageDefinition("materials", (10, 10)),
         "1_3": base_materials.ImageDefinition("materials", (20, 10)),
         "1_0": base_materials.ImageDefinition("materials", (30, 10)),
         "1_1": base_materials.ImageDefinition("materials", (40, 10)),
         "1_2": base_materials.ImageDefinition("materials", (50, 10)),
         "0_": base_materials.ImageDefinition("materials", (60, 10))}

    def __init__(self, **kwargs):
        super().__init__(image_key="0_", **kwargs)


class StoneBrickMaterial(base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 4
    IMAGE_DEFINITIONS: ClassVar[List[base_materials.ImageDefinition]] = \
        base_materials.ImageDefinition("materials", (0, 0))
