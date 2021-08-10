from typing import Union, Tuple, List, TYPE_CHECKING, ClassVar

import interfaces.windows.base_window as base_window
import utility.utilities as util
import utility.constants as con
import interfaces.widgets as widgets
import pygame
import block_classes.materials.machine_materials as machine_materials

if TYPE_CHECKING:
    from board import sprite_groups
    from machines import base_machine


class MachineInterface(base_window.Window):
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150, 255)
    SIZE = util.Size(525, 500)

    _nr_drill_lbl: Union[None, "AmountIndicator"]
    _nr_mover_lbl: Union[None, "AmountIndicator"]
    _nr_placer_lbl: Union[None, "AmountIndicator"]
    _machine: Union[None, "base_machine.Machine"]
    _prev_machine_size: int

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, color=self.COLOR, static=True, **kwargs)
        self.machine_config_grid = None
        self._machine = None
        self._nr_drill_lbl = None
        self._nr_mover_lbl = None
        self._nr_placer_lbl = None
        self._prev_machine_size = 0
        self.__init_widgets()
        self._set_total_amounts()

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

        self.add_widget((425, y), wire_rb)
        radio_selection_group.add(wire_rb)

        wire_lbl = widgets.Label(util.Size(35, 15), text="Wire:", selectable=False, color=con.INVISIBLE_COLOR,
                                 text_pos=("west", "center"))
        self.add_widget((445, y), wire_lbl)

        self._nr_wire_lbl = AmountIndicator(util.Size(30, 15), "wire", current="inf", total="inf")
        wire_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=[self._nr_wire_lbl],
                                       types=["unpressed"])
        self.add_widget((490, y), self._nr_wire_lbl)

        # drill
        y += 20
        drill_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)

        self.add_widget((425, y), drill_rb)
        radio_selection_group.add(drill_rb)

        drill_lbl = widgets.Label(util.Size(35, 15), text="Drill:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((445, y), drill_lbl)

        self._nr_drill_lbl = AmountIndicator(util.Size(30, 15), name="drill")
        drill_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=[self._nr_drill_lbl],
                                        types=["unpressed"])
        self.add_widget((490, y), self._nr_drill_lbl)

        # mover
        y += 20
        mover_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)

        self.add_widget((425, y), mover_rb)
        radio_selection_group.add(mover_rb)

        mover_lbl = widgets.Label(util.Size(35, 15), text="Mover:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((445, y), mover_lbl)

        self._nr_mover_lbl = AmountIndicator(util.Size(30, 15), name="mover")
        mover_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=[self._nr_mover_lbl],
                                        types=["unpressed"])
        self.add_widget((490, y), self._nr_mover_lbl)

        # placer
        y += 20
        placer_rb = widgets.RadioButton(util.Size(15, 15), selection_group=radio_selection_group)

        self.add_widget((425, y), placer_rb)
        radio_selection_group.add(placer_rb)

        placer_lbl = widgets.Label(util.Size(35, 15), text="Placer:", selectable=False, color=con.INVISIBLE_COLOR,
                                   text_pos=("west", "center"))
        self.add_widget((445, y), placer_lbl)

        self._nr_placer_lbl = AmountIndicator(util.Size(30, 15), name="placer")
        placer_rb.add_key_event_listener(1, self.machine_config_grid.set_addition_item, values=[self._nr_placer_lbl],
                                         types=["unpressed"])
        self.add_widget((490, y), self._nr_placer_lbl)

    def wupdate(self, *args):
        super().wupdate(*args)
        if self._machine is not None and self._machine.size != self._prev_machine_size:
            self._set_total_amounts()

    def _set_total_amounts(self):
        if self._machine is None:
            return
        for row_dict in self._machine.blocks.values():
            for block in row_dict.values():
                if isinstance(block.material, machine_materials.MachineDrillMaterial):
                    self._nr_drill_lbl.add_total(1)
                    self._nr_drill_lbl.add_current(1)
                elif isinstance(block.material, machine_materials.MachineMoverMaterial):
                    self._nr_mover_lbl.add_total(1)
                    self._nr_mover_lbl.add_current(1)
                elif isinstance(block.material, machine_materials.MachinePlacerMaterial):
                    self._nr_placer_lbl.add_total(1)
                    self._nr_placer_lbl.add_current(1)
        self._prev_machine_size = self._machine.size

    def set_machine(self, machine):
        self._machine = machine
        self._set_total_amounts()


class MachineGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    BORDER_SIZE: ClassVar[util.Size] = util.Size(5, 5)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (100, 100, 100, 255)

    _WIRE_IMAGE = None
    _DRILL_IMAGE = None
    _MOVER_IMAGE = None
    _PLACER_IMAGE = None

    __addition_item: Union[None, "AmountIndicator"]

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
        image_size = [int((self.rect.width - self.BORDER_SIZE.width * 2) / grid_size.width) - 2,
                      int((self.rect.height - self.BORDER_SIZE.height * 2) / grid_size.height) - 2]
        self._WIRE_IMAGE = pygame.transform.scale(machine_materials.MachineWireMaterial().surface, image_size)
        self._DRILL_IMAGE = pygame.transform.scale(machine_materials.MachineDrillMaterial().surface, image_size)
        self._MOVER_IMAGE = pygame.transform.scale(machine_materials.MachineMoverMaterial().surface, image_size)
        self._PLACER_IMAGE = pygame.transform.scale(machine_materials.MachinePlacerMaterial().surface, image_size)

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

                lbl = GridLabel(label_size)
                lbl.add_key_event_listener(1, self.change_label_image, values=[lbl], types=["pressed"])
                lbl.add_key_event_listener(3, self.clear_label_image, values=[lbl], types=["pressed"])
                self.add_widget(pos, lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def set_addition_item(self, amount_lbl):
        self.__addition_item = amount_lbl

    def change_label_image(self, label):
        if self.__addition_item is None:
            self.clear_label_image(label)
            return
        if not self.__addition_item.can_place():
            return
        elif self.__addition_item.name == "wire":
            image = self._WIRE_IMAGE
        elif self.__addition_item.name == "drill":
            image = self._DRILL_IMAGE
        elif self.__addition_item.name == "mover":
            image = self._MOVER_IMAGE
        elif self.__addition_item.name == "placer":
            image = self._PLACER_IMAGE
        else:
            print(f"Warning: No case for component with name {self.__addition_item.name}")
            return
        label.switch_indicator(self.__addition_item)
        label.set_image(image)

    def clear_label_image(self, label):
        label.clean_surface()

    def wupdate(self, *args):
        super().wupdate()

    def reset(self):
        for row in self._crafting_grid:
            for lbl in row:
                lbl.set_item_image(None)
                lbl.set_item_presence(False)


class GridLabel(widgets.Label):
    def __init__(self, size, **kwargs):
        super().__init__(size, color=MachineGrid.COLOR, selectable=False, text_pos=("west", "center"),
                         border=True, border_color=(0, 0, 0), border_width=1, **kwargs)
        self._current_indicator = None

    def switch_indicator(self, new_indicator):
        if self._current_indicator is not None:
            self._current_indicator.add_current(1)
        self._current_indicator = new_indicator
        if self._current_indicator is not None:
            self._current_indicator.add_current(-1)


class AmountIndicator(widgets.Label):
    def __init__(self, size, name, current: Union[str, int] = 0, total: Union[str, int] = 0, **kwargs):
        super().__init__(size, color=MachineInterface.COLOR, text_pos=("west", "center"), **kwargs)
        self.name = name
        self._current = current
        self._total = total
        self._changed_numbers = False
        self._create_text()

    def _create_text(self):
        self.set_text("")
        self.set_text(f"{self._current}/{self._total}")

    def wupdate(self):
        super().wupdate()
        if self._changed_numbers:
            self._create_text()
            self._changed_numbers = False

    def add_current(self, value):
        if self._current == "inf":
            return
        self._current += value
        self._changed_numbers = True

    def add_total(self, value):
        if self._total == "inf":
            return
        self._total += value
        self._changed_numbers = True

    def can_place(self):
        return self._current == "inf" or self._current > 0
