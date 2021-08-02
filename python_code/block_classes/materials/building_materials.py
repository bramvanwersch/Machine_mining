#!/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import ClassVar, List, Tuple, Dict, Set
import pygame

# own imports
import utility.image_handling
import utility.utilities as util
import block_classes.blocks as blocks
import block_classes.materials.materials as base_materials
import utility.constants as con
import utility.loading_saving


class Building(ABC):
    """abstraction level for all buildings"""

    FULL_SURFACE: ClassVar[utility.image_handling.ImageDefinition]

    @property
    def full_surface(self) -> pygame.Surface:
        return self.FULL_SURFACE.images()[0]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FULL_SURFACE(self) -> utility.image_handling.ImageDefinition:
        pass


class TerminalMaterial(Building, base_materials.Indestructable, base_materials.MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 2
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.InterfaceBlock
    FULL_SURFACE: ClassVar[utility.image_handling.ImageDefinition] =\
        utility.image_handling.ImageDefinition("buildings", (0, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (0, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (10, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (0, 10)),
         4: utility.image_handling.ImageDefinition("buildings", (10, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (0, 0), size=util.Size(20, 20),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class FurnaceMaterial(Building, base_materials.TransportableMaterial, base_materials.MultiImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 3
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.InterfaceBlock
    FULL_SURFACE: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (20, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (20, 20)),
         2: utility.image_handling.ImageDefinition("buildings", (30, 20)),
         3: utility.image_handling.ImageDefinition("buildings", (20, 30)),
         4: utility.image_handling.ImageDefinition("buildings", (30, 30))}
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (20, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (30, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (20, 10)),
         4: utility.image_handling.ImageDefinition("buildings", (30, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (20, 0), size=util.Size(20, 20),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class FactoryMaterial(Building, base_materials.TransportableMaterial, base_materials.MultiImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 4
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.InterfaceBlock
    FULL_SURFACE: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (40, 0), size=util.Size(20, 20))
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (40, 20)),
         2: utility.image_handling.ImageDefinition("buildings", (50, 20)),
         3: utility.image_handling.ImageDefinition("buildings", (40, 30)),
         4: utility.image_handling.ImageDefinition("buildings", (50, 30))}
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (40, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (50, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (40, 10)),
         4: utility.image_handling.ImageDefinition("buildings", (50, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (40, 0), size=util.Size(20, 20),
                                               image_size=con.TRANSPORT_BLOCK_SIZE)


class StonePipeMaterial(base_materials.TransportableMaterial, base_materials.MultiImageMaterial):
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 5
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.NetworkEdgeBlock
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_DEFINITIONS: ClassVar[Dict[str, List[utility.image_handling.ImageDefinition]]] = \
        {"2_13": utility.image_handling.ImageDefinition("materials", (10, 0)),
         "2_02": utility.image_handling.ImageDefinition("materials", (20, 0)),
         "2_23": utility.image_handling.ImageDefinition("materials", (30, 0)),
         "2_03": utility.image_handling.ImageDefinition("materials", (40, 0)),
         "2_12": utility.image_handling.ImageDefinition("materials", (50, 0)),
         "2_01": utility.image_handling.ImageDefinition("materials", (60, 0)),
         "3_013": utility.image_handling.ImageDefinition("materials", (70, 0)),
         "3_012": utility.image_handling.ImageDefinition("materials", (80, 0)),
         "3_023": utility.image_handling.ImageDefinition("materials", (90, 0)),
         "3_123": utility.image_handling.ImageDefinition("materials", (0, 10)),
         "4_0123": utility.image_handling.ImageDefinition("materials", (10, 10)),
         "1_3": utility.image_handling.ImageDefinition("materials", (20, 10)),
         "1_0": utility.image_handling.ImageDefinition("materials", (30, 10)),
         "1_1": utility.image_handling.ImageDefinition("materials", (40, 10)),
         "1_2": utility.image_handling.ImageDefinition("materials", (50, 10)),
         "0_": utility.image_handling.ImageDefinition("materials", (60, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (10, 0), image_size=con.TRANSPORT_BLOCK_SIZE)

    def __init__(self, **kwargs):
        super().__init__(image_key="0_", **kwargs)


class StoneChestMaterial(Building, base_materials.TransportableMaterial, base_materials.ImageMaterial):
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.InterfaceBlock
    FULL_SURFACE: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (0, 70))
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (0, 70))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (0, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class StoneBrickMaterial(base_materials.TransportableMaterial, base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 4
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (0, 0))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (0, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MossBrickMaterial(base_materials.TransportableMaterial, base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 4
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (10, 70))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (10, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class ManyMossBrickMaterial(base_materials.TransportableMaterial, base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 4
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (20, 70))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (20, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class IronSheetWall(base_materials.TransportableMaterial, base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 50
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (30, 70))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (30, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class RustedIronSheetWall(base_materials.TransportableMaterial, base_materials.ImageMaterial):

    HARDNESS: ClassVar[int] = 50
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("materials", (40, 70), flip=(True, True))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (40, 70), image_size=con.TRANSPORT_BLOCK_SIZE)


class ConveyorBelt(base_materials.RotatableMaterial, base_materials.MultiImageMaterial,
                   base_materials.TransportableMaterial, utility.loading_saving.Savable, ABC):
    __slots__ = "direction"

    direction: int

    def __init__(self, direction=0, **kwargs):
        base_materials.MultiImageMaterial.__init__(self, **kwargs)
        self.direction = direction  # direction the belt is facing.

    def to_dict(self):
        d = base_materials.MultiImageMaterial.to_dict(self)
        d["direction"] = self.direction
        return d

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def TRANSFER_TIME(self) -> int:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def STACK_SIZE(self) -> int:
        pass


class BasicConveyorBelt(ConveyorBelt):
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 6
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.ConveyorNetworkBlock

    TRANSFER_TIME: ClassVar[int] = 1000
    STACK_SIZE: ClassVar[int] = 2
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (255, 255, 255)

    # 0-3 for the 4 directions, N, E, S, W
    IMAGE_DEFINITIONS: ClassVar[Dict[str, List[utility.image_handling.ImageDefinition]]] = \
        {"1_0": utility.image_handling.ImageDefinition("materials", (0, 40)),
         "1_1": utility.image_handling.ImageDefinition("materials", (80, 30)),
         "1_2": utility.image_handling.ImageDefinition("materials", (10, 40)),
         "1_3": utility.image_handling.ImageDefinition("materials", (90, 30)),
         "2_30": utility.image_handling.ImageDefinition("materials", (20, 40)),
         "2_03": utility.image_handling.ImageDefinition("materials", (30, 40)),
         "2_32": utility.image_handling.ImageDefinition("materials", (40, 40)),
         "2_23": utility.image_handling.ImageDefinition("materials", (50, 40)),
         "2_10": utility.image_handling.ImageDefinition("materials", (60, 40)),
         "2_01": utility.image_handling.ImageDefinition("materials", (70, 40)),
         "2_12": utility.image_handling.ImageDefinition("materials", (80, 40)),
         "2_21": utility.image_handling.ImageDefinition("materials", (90, 40)),
         "3_023_0": utility.image_handling.ImageDefinition("materials", (0, 50)),
         "3_023_1": utility.image_handling.ImageDefinition("materials", (10, 50)),
         "3_023_2": utility.image_handling.ImageDefinition("materials", (20, 50)),
         "3_023_3": utility.image_handling.ImageDefinition("materials", (30, 50)),
         "3_123_0": utility.image_handling.ImageDefinition("materials", (40, 50)),
         "3_123_1": utility.image_handling.ImageDefinition("materials", (50, 50)),
         "3_123_2": utility.image_handling.ImageDefinition("materials", (60, 50)),
         "3_123_3": utility.image_handling.ImageDefinition("materials", (70, 50)),
         "3_012_0": utility.image_handling.ImageDefinition("materials", (80, 50)),
         "3_012_1": utility.image_handling.ImageDefinition("materials", (90, 50)),
         "3_012_2": utility.image_handling.ImageDefinition("materials", (0, 60)),
         "3_012_3": utility.image_handling.ImageDefinition("materials", (10, 60)),
         "3_013_0": utility.image_handling.ImageDefinition("materials", (20, 60)),
         "3_013_1": utility.image_handling.ImageDefinition("materials", (30, 60)),
         "3_013_2": utility.image_handling.ImageDefinition("materials", (40, 60)),
         "3_013_3": utility.image_handling.ImageDefinition("materials", (50, 60)),
         "4_0123_0": utility.image_handling.ImageDefinition("materials", (60, 60)),
         "4_0123_1": utility.image_handling.ImageDefinition("materials", (70, 60)),
         "4_0123_2": utility.image_handling.ImageDefinition("materials", (80, 60)),
         "4_0123_3": utility.image_handling.ImageDefinition("materials", (90, 60))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (0, 40), image_size=con.TRANSPORT_BLOCK_SIZE)

    def __init__(self, image_key=None, **kwargs):
        super().__init__(image_key=image_key if image_key is not None else "1_0", **kwargs)

    def rotate(
        self,
        rotate_count: int
    ):
        """Works only for rotating the straight base belt"""
        self.direction = rotate_count % 4
        self.image_key = f"{self.image_key.split('_')[0]}_{rotate_count % 4}"
