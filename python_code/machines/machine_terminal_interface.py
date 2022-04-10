from typing import Union, Tuple, List, TYPE_CHECKING

from interfaces.windows import console_windows
from utility import consoles
import utility.utilities as util


if TYPE_CHECKING:
    from board import sprite_groups
    from machines.base_machine import Machine


class MachineConsole(console_windows.ConsoleWindow):
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150, 255)
    SIZE: util.Size = util.Size(540, 500)

    _console: consoles.MachineConsole

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        color=COLOR,
        static=True,
        title="MACHINE CONSOLE",
        max_line_size=SIZE.width,
        **kwargs
    ):
        console_ = consoles.MachineConsole()
        super().__init__(pos, self.SIZE, sprite_group, console_, color=color, static=static, title=title,
                         max_line_size=max_line_size, **kwargs)

    def set_machine(self, machine: "Machine"):
        self._console.set_machine(machine)
