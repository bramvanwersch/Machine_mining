from typing import List, TYPE_CHECKING, ClassVar, Type

import block_classes.blocks as blocks
from utility import inventories
import utility.utilities as util
import interfaces.windows.machine_terminal_interface as terminal_interface
from block_classes.materials import machine_materials

if TYPE_CHECKING:
    from board import sprite_groups


class MachineTerminalBlock(blocks.InterfaceBlock):

    BASE_INV_WHEIGHT: ClassVar[int] = 25

    def __init__(
        self,
        pos: List[int],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        interface = terminal_interface.MachineTerminal(pos, util.Size(400, 300), sprite_group)
        inventory = inventories.Inventory(self.BASE_INV_WHEIGHT)
        super().__init__(pos, machine_materials.MachineTerminalMaterial(), interface, inventory=inventory, **kwargs)
