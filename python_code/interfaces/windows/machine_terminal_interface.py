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
        if self.__addition_item == "wire":
            image = machine_materials.MachineWireMaterial().surface
            label.set_image(image)
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
