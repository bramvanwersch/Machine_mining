from typing import Union, Tuple, List, TYPE_CHECKING
import pygame

import interfaces.windows.base_window as base_window
import utility.utilities as util
import interfaces.windows.interface_utility as interface_util
import interfaces.widgets as widgets

if TYPE_CHECKING:
    from board import sprite_groups


class MachineTerminal(base_window.Window):

    SIZE = util.Size(500, 500)

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, static=True, **kwargs)
        self.movable_item_pane = None
        self.__init_widgets()

    def __init_widgets(self):
        self.movable_item_pane = MovableItemPane(util.Size(400, 450))
        self.add_widget((25, 25), self.movable_item_pane)

        block_button = widgets.Button(util.Size(20, 10), text="Block", selectable=False)
        block_button.add_key_event_listener(1, self.movable_item_pane.add_item, values=["block"], types=["unpressed"])
        self.add_widget((425, 25), block_button)


class MovableItemPane(widgets.Pane):

    def __init__(self, size, **kwargs):
        super().__init__(size, **kwargs)
        self._moving_widget = None
        self.__previous_pos = [0, 0]
        self.__precise_change = [0.0, 0.0]

    def wupdate(self, *args):
        super().wupdate(*args)
        if self._moving_widget is not None:
            self.__move_moving_widget()

    def add_item(self, type_):
        if type_ == "block":
            self.add_block()

    def add_block(self):
        block = widgets.Label(util.Size(10, 10), color=(0, 0, 0), selectable=False)
        block.add_key_event_listener(1, self._select_movable_block, values=[block], types=["pressed"])
        self.add_widget((0, 0), block)

    def _select_movable_block(self, block):
        self._moving_widget = block
        self.__previous_pos = pygame.mouse.get_pos()

    def __move_moving_widget(self):
        mouse_pos = pygame.mouse.get_pos()
        moved_x = (mouse_pos[0] - self.__previous_pos[0]) + self.__precise_change[0]
        moved_y = (mouse_pos[1] - self.__previous_pos[1]) + self.__precise_change[1]
        self.__previous_pos = mouse_pos
        self._moving_widget.move((int(moved_x), int(moved_y)))
        if moved_x > 0:
            residual_x = moved_x % 1
        else:
            residual_x = - (moved_x % 1)

        if moved_y > 0:
            residual_y = moved_y % 1
        else:
            residual_y = - (moved_y % 1)
        self.__precise_change = (residual_x, residual_y)
