from typing import List, TYPE_CHECKING, ClassVar

import block_classes.blocks as blocks
from utility import inventories
from block_classes.materials import machine_materials

if TYPE_CHECKING:
    from board import sprite_groups
    import interfaces.windows.machine_terminal_interface as terminal_interface


class MachineTerminalBlock(blocks.InterfaceBlock):

    BASE_INV_WHEIGHT: ClassVar[int] = 25

    interface: "terminal_interface.MachineInterface"

    def __init__(
        self,
        pos: List[int],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        # circular imports :(
        import interfaces.windows.machine_terminal_interface as terminal_interface
        interface = terminal_interface.MachineInterface(pos, sprite_group)
        inventory = inventories.Inventory(self.BASE_INV_WHEIGHT)
        super().__init__(pos, machine_materials.MachineTerminal(), interface, inventory=inventory, **kwargs)

    def set_machine(self, machine):
        # set machine for the interface
        self.interface.set_machine(machine)
