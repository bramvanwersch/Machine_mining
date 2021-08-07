from abc import ABC
from typing import List, ClassVar, Dict

# own imports
from utility import constants as con
import utility.image_handling

import block_classes.materials.materials as base_materials
import block_classes.blocks as blocks
import block_classes.machine_blocks as machine_blocks


class MachineComponent(base_materials.TransportableMaterial, ABC):
    pass


class UnbuildableMachineComponent(base_materials.ImageMaterial, base_materials.Unbuildable, ABC):
    pass


class MachineWireMaterial(UnbuildableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (90, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (90, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class NormalMachineComponent(base_materials.ImageMaterial, MachineComponent, ABC):
    pass


class MachineConnector(NormalMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineTerminalMaterial(NormalMachineComponent):
    _BLOCK_TYPE: ClassVar[blocks.Block] = machine_blocks.MachineTerminalBlock
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (70, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (70, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineInventoryMaterial(NormalMachineComponent):
    """Visual not an actual inventory will increase the carying capacity of the terminal"""
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (80, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (80, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class RotatableMachineComponent(base_materials.MultiImageMaterial, base_materials.RotatableMaterial,
                                MachineComponent, ABC):

    def rotate(
        self,
        rotate_count: int
    ):
        self.image_key = rotate_count
        self.image_key %= 4


class MachineDrillMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 0)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 0))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineMoverMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 10)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 10)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 10)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 10), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachinePlacerMaterial(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 20)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 20)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 20)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 20))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 20), image_size=con.TRANSPORT_BLOCK_SIZE)
