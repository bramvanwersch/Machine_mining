from typing import Union, Tuple, List, TYPE_CHECKING, ClassVar, Dict, Set
import pygame

import interfaces.windows.base_window as base_window
import utility.utilities as util
import utility.constants as con
import interfaces.widgets as widgets
import block_classes.materials.machine_materials as machine_materials
from block_classes.materials.materials import BaseMaterial

if TYPE_CHECKING:
    from board import sprite_groups


class MachineInterface(base_window.Window):
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150, 255)
    SIZE: util.Size = util.Size(540, 500)

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, color=self.COLOR, static=True, **kwargs)
        self._machine = None

    def set_machine(self, machine):
        self._machine = machine
