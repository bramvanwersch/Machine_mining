from typing import Union, Tuple, List, TYPE_CHECKING

import interfaces.windows.base_window as base_window
import utility.utilities as util

if TYPE_CHECKING:
    from board import sprite_groups


class MachineTerminal(base_window.Window):

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        size: Union[util.Size, Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, size, sprite_group, static=True, **kwargs)
