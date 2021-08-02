from abc import ABC
from typing import List, ClassVar, Dict

# own imports
from utility import constants as con
import utility.image_handling

import block_classes.materials.materials as base_materials
import block_classes.materials.building_materials as building_materials
import block_classes.blocks as blocks


class MachineComponent(base_materials.ImageMaterial, building_materials.BuildingMaterial, ABC):
    pass


class Connector(MachineComponent):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (60, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineTerminalMaterial(MachineComponent):
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.InterfaceBlock
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (70, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineInventoryMaterial(MachineComponent):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("materials", (60, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class RotatableMachineComponent(base_materials.MultiImageMaterial, base_materials.RotatableMaterial):

    def rotate(
        self,
        rotate_count: int
    ):
        self.image_key += 1
        self.image_key %= 4


class DrillMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (60, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (70, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (80, 0)),
         4: utility.image_handling.ImageDefinition("buildings", (90, 0))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MoverMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (60, 10)),
         2: utility.image_handling.ImageDefinition("buildings", (70, 10)),
         3: utility.image_handling.ImageDefinition("buildings", (80, 10)),
         4: utility.image_handling.ImageDefinition("buildings", (90, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class PlacerMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {1: utility.image_handling.ImageDefinition("buildings", (60, 20)),
         2: utility.image_handling.ImageDefinition("buildings", (70, 20)),
         3: utility.image_handling.ImageDefinition("buildings", (80, 20)),
         4: utility.image_handling.ImageDefinition("buildings", (90, 20))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 20), image_size=con.TRANSPORT_BLOCK_SIZE)
