from typing import Union, Tuple, List, TYPE_CHECKING, ClassVar
import pygame

import interfaces.windows.base_window as base_window
import utility.utilities as util
import utility.constants as con
import interfaces.widgets as widgets
import block_classes.materials.machine_materials as machine_materials

if TYPE_CHECKING:
    from board import sprite_groups


class MachineInterface(base_window.Window):

    SIZE = util.Size(500, 500)

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, static=True, **kwargs)
        self.machine_config_grid = None
        self._machine = None
        self.__init_widgets()

    def __init_widgets(self):
        self.machine_config_grid = MachineGrid(util.Size(400, 400), util.Size(7, 7))
        self.add_widget((25, 25), self.machine_config_grid)

        wire_rb = widgets.RadioButton(util.Size(15, 15))
        wire_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=["wire"],
                                       types=["unpressed"])
        self.add_widget((425, 35), wire_rb)

        wire_lbl = widgets.Label(util.Size(50, 15), text="Wire", selectable=False)
        self.add_widget((450, 35), wire_lbl)

    def _create_circuit_buttons(self):
        pass

    def set_machine(self, machine):
        self._machine = machine


class MachineGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (173, 94, 29)
    BORDER_SIZE: ClassVar[util.Size] = util.Size(5, 5)

    def __init__(
        self,
        size,
        grid_size,
        **kwargs
    ):
        super().__init__(size, color=con.INVISIBLE_COLOR, **kwargs)
        self._crafting_grid = []
        self.__addition_item = None
        self.__init_grid(grid_size)

    def __init_grid(
        self,
        grid_size: util.Size
    ):
        label_size = util.Size((self.rect.width - self.BORDER_SIZE.width * 2) / grid_size.width,
                               (self.rect.height - self.BORDER_SIZE.height * 2) / grid_size.height)
        for row_i in range(grid_size.height):
            row = []
            for col_i in range(grid_size.width):
                pos = self.BORDER_SIZE.width + label_size.width * col_i, \
                      self.BORDER_SIZE.height + label_size.height * row_i

                lbl = widgets.Label(label_size, color=self.COLOR, border=True, border_color=(0, 0, 0), border_width=1,
                                    selectable=False)
                lbl.add_key_event_listener(1, self.change_label_image, values=[lbl], types=["pressed"])
                lbl.add_key_event_listener(3, self.clear_label_image, values=[lbl], types=["pressed"])
                self.add_widget(pos, lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def set_addition_item(self, name):
        self.__addition_item = name

    def change_label_image(self, label):
        if self.__addition_item == "block":
            s = pygame.Surface((25, 25))
            s.fill((0, 0, 0))
            label.set_image(s)
        elif self.__addition_item is None:
            self.clear_label_image(label)

    def clear_label_image(self, label):
        label.clean_surface()

    def wupdate(self, *args):
        super().wupdate()

    def reset(self):
        for row in self._crafting_grid:
            for lbl in row:
                lbl.set_item_image(None)
                lbl.set_item_presence(False)



# class MovableItemPane(widgets.Pane):
#
#     def __init__(self, size, **kwargs):
#         super().__init__(size, **kwargs)
#         self._moving_widget = None
#         self.__previous_pos = [0, 0]
#         self.__precise_change = [0.0, 0.0]
#
#     def wupdate(self, *args):
#         super().wupdate(*args)
#         if self._moving_widget is not None:
#             self.__move_moving_widget()
#
#     def add_item(self, type_):
#         if type_ == "block":
#             self.add_block()
#
#     def add_block(self):
#         block = widgets.Label(util.Size(10, 10), color=(0, 0, 0), selectable=False)
#         block.add_key_event_listener(1, self._select_movable_block, values=[block], types=["pressed"])
#         self.add_widget((0, 0), block)
#
#     def _select_movable_block(self, block):
#         self._moving_widget = block
#         self.__previous_pos = pygame.mouse.get_pos()
#
#     def __move_moving_widget(self):
#         mouse_pos = pygame.mouse.get_pos()
#         moved_x = (mouse_pos[0] - self.__previous_pos[0]) + self.__precise_change[0]
#         moved_y = (mouse_pos[1] - self.__previous_pos[1]) + self.__precise_change[1]
#         self.__previous_pos = mouse_pos
#         self._moving_widget.move((int(moved_x), int(moved_y)))
#         if moved_x > 0:
#             residual_x = moved_x % 1
#         else:
#             residual_x = - (moved_x % 1)
#
#         if moved_y > 0:
#             residual_y = moved_y % 1
#         else:
#             residual_y = - (moved_y % 1)
#         self.__precise_change = (residual_x, residual_y)
