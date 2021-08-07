from typing import Union, Tuple, List, TYPE_CHECKING, ClassVar

import interfaces.windows.base_window as base_window
import utility.utilities as util
import utility.constants as con
import interfaces.widgets as widgets
import pygame
import block_classes.materials.machine_materials as machine_materials

if TYPE_CHECKING:
    from board import sprite_groups


class MachineInterface(base_window.Window):

    SIZE = util.Size(525, 500)

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, static=True, **kwargs)
        self.machine_config_grid = None
        self._machine = None
        self._nr_drill_lbl = None
        self._nr_mover_lbl = None
        self._nr_placer_lbl = None
        self.__init_widgets()

    def __init_widgets(self):
        self.machine_config_grid = MachineGrid(util.Size(400, 400), util.Size(7, 7))
        self.add_widget((25, 25), self.machine_config_grid)

        radio_selection_group = widgets.RadioGroup()

        y = 35
        header_lbl = widgets.Label(util.Size(100, 20), text="Components:", font_size=20, color=con.INVISIBLE_COLOR,
                                   text_pos=("west", "center"))
        self.add_widget((425, y), header_lbl)

        # wire
        y += 25
        wire_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)
        wire_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=["wire"],
                                       types=["unpressed"])
        self.add_widget((425, y), wire_rb)
        radio_selection_group.add(wire_rb)

        wire_lbl = widgets.Label(util.Size(35, 15), text="Wire:", selectable=False, color=con.INVISIBLE_COLOR,
                                 text_pos=("west", "center"))
        self.add_widget((445, y), wire_lbl)

        self._nr_wire_lbl = widgets.Label(util.Size(25, 15), text="inf", selectable=False, color=con.INVISIBLE_COLOR,
                                          text_pos=("west", "center"))
        self.add_widget((490, y), self._nr_wire_lbl)

        # drill
        y += 20
        drill_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)
        drill_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=["drill"],
                                        types=["unpressed"])
        self.add_widget((425, y), drill_rb)
        radio_selection_group.add(drill_rb)

        drill_lbl = widgets.Label(util.Size(35, 15), text="Drill:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((445, y), drill_lbl)

        self._nr_drill_lbl = widgets.Label(util.Size(25, 15), text="0/0", selectable=False, color=con.INVISIBLE_COLOR,
                                           text_pos=("west", "center"))
        self.add_widget((490, y), self._nr_drill_lbl)

        # mover
        y += 20
        mover_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)
        mover_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=["mover"],
                                        types=["unpressed"])
        self.add_widget((425, y), mover_rb)
        radio_selection_group.add(mover_rb)

        mover_lbl = widgets.Label(util.Size(35, 15), text="Mover:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((445, y), mover_lbl)

        self._nr_mover_lbl = widgets.Label(util.Size(25, 15), text="0/0", selectable=False, color=con.INVISIBLE_COLOR,
                                           text_pos=("west", "center"))
        self.add_widget((490, y), self._nr_mover_lbl)

        # placer
        y += 20
        placer_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)
        placer_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=["placer"],
                                         types=["unpressed"])
        self.add_widget((425, y), placer_rb)
        radio_selection_group.add(placer_rb)

        placer_lbl = widgets.Label(util.Size(35, 15), text="Placer:", selectable=False, color=con.INVISIBLE_COLOR,
                                   text_pos=("west", "center"))
        self.add_widget((445, y), placer_lbl)

        self._nr_placer_lbl = widgets.Label(util.Size(25, 15), text="0/0", selectable=False, color=con.INVISIBLE_COLOR,
                                            text_pos=("west", "center"))
        self.add_widget((490, y), self._nr_placer_lbl)

    def _create_circuit_buttons(self):
        for row_dict in self._machine.blocks.values():
            for block in row_dict.values():
                if isinstance(block.material, machine_materials.MachineDrillMaterial):
                    pass

    def set_machine(self, machine):
        self._machine = machine


class MachineGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (173, 94, 29)
    BORDER_SIZE: ClassVar[util.Size] = util.Size(5, 5)

    _WIRE_IMAGE = None
    _DRILL_IMAGE = None
    _MOVER_IMAGE = None
    _PLACER_IMAGE = None

    def __init__(
        self,
        size,
        grid_size,
        **kwargs
    ):
        super().__init__(size, color=con.INVISIBLE_COLOR, **kwargs)
        self._crafting_grid = []
        self.__addition_item = None
        self.__init_images(grid_size)

        self.__init_grid(grid_size)

    def __init_images(
        self,
        grid_size: util.Size
    ):
        label_size = [int((self.rect.width - self.BORDER_SIZE.width * 2) / grid_size.width),
                      int((self.rect.height - self.BORDER_SIZE.height * 2) / grid_size.height)]
        self._WIRE_IMAGE = pygame.transform.scale(machine_materials.MachineWireMaterial().surface, label_size)
        self._DRILL_IMAGE = pygame.transform.scale(machine_materials.MachineDrillMaterial().surface, label_size)
        self._MOVER_IMAGE = pygame.transform.scale(machine_materials.MachineMoverMaterial().surface, label_size)
        self._PLACER_IMAGE = pygame.transform.scale(machine_materials.MachinePlacerMaterial().surface, label_size)

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
            image = self._WIRE_IMAGE
            label.set_image(image)
        elif self.__addition_item == "drill":
            image = self._DRILL_IMAGE
            label.set_image(image)
        elif self.__addition_item == "mover":
            image = self._MOVER_IMAGE
            label.set_image(image)
        elif self.__addition_item == "placer":
            image = self._PLACER_IMAGE
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
