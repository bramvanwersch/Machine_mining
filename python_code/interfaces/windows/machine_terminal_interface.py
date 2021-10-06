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
    from machines import base_machine, logic_circuit


class MachineInterface(base_window.Window):
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150, 255)
    SIZE: util.Size = util.Size(540, 500)
    NO_COLOR_LOGIC_COMPONENTS: Set[str] = {"connector"}

    machine_config_grid: Union[None, "MachineGrid"]
    _drill_components: Union[None, "ComponentGroup"]
    _mover_components: Union[None, "ComponentGroup"]
    _placer_components: Union[None, "ComponentGroup"]
    _machine_view: Union[None, "MachineView"]
    _machine: Union[None, "base_machine.Machine"]
    _prev_machine_size: int

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, self.SIZE, sprite_group, color=self.COLOR, static=True, **kwargs)
        self.add_key_event_listener(pygame.K_r, self._add_rotation, types=["pressed"])
        self.machine_config_grid = None
        self._machine = None
        self._drill_components = ComponentGroup()
        self._mover_components = ComponentGroup()
        self._placer_components = ComponentGroup()
        self._machine_view = None
        self._prev_machine_size = 0
        self._wire_color = "red"
        self._component = None
        self._rotate = 0
        self.__init_widgets()

    def __init_widgets(self):
        mc_width = 300
        mc_height = 300
        mc_pos = (10, 25)
        self.machine_config_grid = MachineGrid(util.Size(mc_width, mc_height))
        self.add_widget(mc_pos, self.machine_config_grid)

        component_selection_group = widgets.RadioGroup()

        y = mc_pos[1] + 5

        self._machine_view = MachineView(util.Size(200, 200), [self._drill_components, self._mover_components,
                                                               self._placer_components])
        self.add_widget((mc_width + mc_pos[0] + 5, y), self._machine_view)
        self.add_border(self._machine_view)

        # components
        component_x = mc_pos[0] + 5
        y += 215
        header_lbl = widgets.Label(util.Size(200, 20), text="Machine Components:", font_size=20,
                                   color=con.INVISIBLE_COLOR, text_pos=("west", "center"), selectable=False)
        self.add_widget((mc_width + component_x, y), header_lbl)

        # drill
        y += 20
        drill_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)

        self.add_widget((mc_width + component_x, y), drill_rb)
        component_selection_group.add(drill_rb)

        drill_lbl = widgets.Label(util.Size(35, 15), text="Drill:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((mc_width + component_x + 20, y), drill_lbl)

        nr_drill_lbl = AmountIndicator(util.Size(30, 15), self._drill_components)
        drill_rb.add_key_event_listener(1, self.machine_config_grid.set_component_group,
                                        values=[self._drill_components], types=["unpressed"])
        self.add_widget((mc_width + component_x + 65, y), nr_drill_lbl)

        # mover
        y += 20
        mover_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)

        self.add_widget((mc_width + component_x, y), mover_rb)
        component_selection_group.add(mover_rb)

        mover_lbl = widgets.Label(util.Size(35, 15), text="Mover:", selectable=False, color=con.INVISIBLE_COLOR,
                                  text_pos=("west", "center"))
        self.add_widget((mc_width + component_x + 20, y), mover_lbl)

        nr_mover_lbl = AmountIndicator(util.Size(30, 15), self._mover_components)
        mover_rb.add_key_event_listener(1, self.machine_config_grid.set_component_group,
                                        values=[self._mover_components], types=["unpressed"])
        self.add_widget((mc_width + component_x + 65, y), nr_mover_lbl)

        # placer
        y += 20
        placer_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)

        self.add_widget((mc_width + component_x, y), placer_rb)
        component_selection_group.add(placer_rb)

        placer_lbl = widgets.Label(util.Size(35, 15), text="Placer:", selectable=False, color=con.INVISIBLE_COLOR,
                                   text_pos=("west", "center"))
        self.add_widget((mc_width + component_x + 20, y), placer_lbl)

        nr_placer_lbl = AmountIndicator(util.Size(30, 15), self._placer_components)
        placer_rb.add_key_event_listener(1, self.machine_config_grid.set_component_group,
                                         values=[self._placer_components], types=["unpressed"])
        self.add_widget((mc_width + component_x + 65, y), nr_placer_lbl)

        # logic components
        wire_pane = widgets.Pane(util.Size(mc_width - 16, 150), color=self.COLOR)
        self.add_widget((mc_pos[0] + 8, mc_height + mc_pos[1] + 5), wire_pane)
        self.add_border(wire_pane)

        # wire color
        color_selection_group = widgets.RadioGroup()

        x = 5
        y = 5
        color_lbl = widgets.Label((100, 10), text="Wire color:", text_pos=("west", "center"),
                                  color=self.COLOR, selectable=False)
        wire_pane.add_widget((x, y), color_lbl)

        y += 15
        x += 5
        red_rb = widgets.RadioButton(util.Size(15, 15), selection_group=color_selection_group)
        red_rb.switch(True)
        red_rb.add_key_event_listener(1, self._set_wire_color, values=["red"])
        wire_pane.add_widget((x, y), red_rb)
        color_selection_group.add(red_rb)

        x += 20
        red_lbl = widgets.Label((20, 15), text="red", text_pos=("west", "center"),
                                color=self.COLOR, selectable=False)
        wire_pane.add_widget((x, y), red_lbl)

        x += 20
        green_rb = widgets.RadioButton(util.Size(15, 15), selection_group=color_selection_group)
        green_rb.add_key_event_listener(1, self._set_wire_color, values=["green"])
        wire_pane.add_widget((x, y), green_rb)
        color_selection_group.add(green_rb)

        x += 20
        green_lbl = widgets.Label((35, 15), text="green", text_pos=("west", "center"),
                                  color=self.COLOR, selectable=False)
        wire_pane.add_widget((x, y), green_lbl)

        x += 35
        blue_rb = widgets.RadioButton(util.Size(15, 15), selection_group=color_selection_group)
        blue_rb.add_key_event_listener(1, self._set_wire_color, values=["blue"])
        wire_pane.add_widget((x, y), blue_rb)
        color_selection_group.add(blue_rb)

        x += 20
        blue_lbl = widgets.Label((20, 15), text="blue", text_pos=("west", "center"),
                                 color=self.COLOR, selectable=False)
        wire_pane.add_widget((x, y), blue_lbl)

        y += 25
        # logic component selection
        x = 10
        wire_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)
        wire_rb.add_key_event_listener(1, self._set_logic_component, values=["wire"])
        wire_pane.add_widget((x, y), wire_rb)
        component_selection_group.add(wire_rb)

        wire_lbl = widgets.Label((50, 15), text="wire", text_pos=("west", "center"),
                                 color=self.COLOR, selectable=False)
        wire_pane.add_widget((x + 20, y), wire_lbl)

        y += 20
        inverter_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)
        inverter_rb.add_key_event_listener(1, self._set_logic_component, values=["inverter"])
        wire_pane.add_widget((x, y), inverter_rb)
        component_selection_group.add(inverter_rb)

        inverter_lbl = widgets.Label((50, 15), text="Inverter", text_pos=("west", "center"),
                                     color=self.COLOR, selectable=False)
        wire_pane.add_widget((x + 20, y), inverter_lbl)

        y += 20
        connector_rb = widgets.RadioButton(util.Size(15, 15), selection_group=component_selection_group)
        connector_rb.add_key_event_listener(1, self._set_logic_component, values=["connector"])
        wire_pane.add_widget((x, y), connector_rb)
        component_selection_group.add(connector_rb)

        connector_lbl = widgets.Label((50, 15), text="Connector", text_pos=("west", "center"),
                                      color=self.COLOR, selectable=False)
        wire_pane.add_widget((x + 20, y), connector_lbl)

    def add_machine_block(self, block):
        if isinstance(block.material, machine_materials.MachineDrill):
            self._drill_components.add(block)
        elif isinstance(block.material, machine_materials.MachineMover):
            self._mover_components.add(block)
        elif isinstance(block.material, machine_materials.MachinePlacer):
            self._placer_components.add(block)

    def remove_machine_block(self, block):
        grid_pos = None
        if isinstance(block.material, machine_materials.MachineDrill):
            grid_pos = self._drill_components.remove(block)
        elif isinstance(block.material, machine_materials.MachineMover):
            grid_pos = self._mover_components.remove(block)
        elif isinstance(block.material, machine_materials.MachinePlacer):
            grid_pos = self._placer_components.remove(block)

        if grid_pos is not None:
            self.machine_config_grid.remove_grid_image(grid_pos)

    def set_machine(self, machine):
        self._machine = machine
        self._machine_view.set_machine(machine)
        self.machine_config_grid.set_logic_circuit(self._machine.logic_circuit)

    def _set_logic_component(self, component):
        self._component = component
        if self._component in self.NO_COLOR_LOGIC_COMPONENTS:
            name = self._component
        else:
            name = f"{self._wire_color}:{self._component}"
        self.machine_config_grid.set_logic_component(name)

    def _set_wire_color(self, color):
        self._wire_color = color
        if self._component is not None:
            self._set_logic_component(self._component)

    def _add_rotation(self):
        self._rotate += 1
        self.machine_config_grid.add_rotation()


class MachineView(widgets.Pane):

    _machine: Union[None, "base_machine.Machine"]
    _prev_machine_size: int

    def __init__(
        self,
        size,
        component_groups: List["ComponentGroup"],
        **kwargs
    ):
        super().__init__(size, color=(255, 255, 255), **kwargs)
        self._machine = None
        self._prev_machine_size = 0
        self._component_groups = component_groups

    def wupdate(self, *args):
        super().wupdate(*args)
        if self._machine is not None and self._machine.size != self._prev_machine_size:
            self._prev_machine_size = self._machine.size
            # do not itterate over a list were deletions are made
            for widget in self.widgets.copy():
                self.remove_widget(widget)
            self.create_machine_view()

    def set_machine(self, machine):
        self._machine = machine
        self.create_machine_view()

    def create_machine_view(self):
        topleft_offset = self._machine.rect.topleft
        for row_dict in self._machine.blocks.values():
            for block in row_dict.values():
                topleft = int((block.rect.left - topleft_offset[0]) +
                              ((self.rect.width / 2) - (self._machine.rect.width / 2))), \
                          int((block.rect.top - topleft_offset[1]) +
                              ((self.rect.height / 2) - (self._machine.rect.height / 2)))
                if block.material.VIEWABLE:  # noqa --> always machineComponent
                    present_group = None
                    for group in self._component_groups:
                        if block in group:
                            present_group = group
                            break
                    component_lbl = MachineViewLabel(present_group, block, image=block.material.surface,
                                                     selection_color=(0, 0, 0))
                else:
                    component_lbl = widgets.Label(block.rect.size, color=(175, 175, 175), selectable=False)
                self.add_widget(topleft, component_lbl)


class MachineViewLabel(widgets.Label):

    def __init__(self, component_group, block, **kwargs):
        self._component_group = component_group
        self._block = block
        super().__init__(block.rect.size, **kwargs)

    def wupdate(self):
        super().wupdate()
        if self._component_group is not None:
            if self.selected and not self._component_group.is_block_selected(self._block):
                self.set_selected(False)
            if not self.selected and self._component_group.is_block_selected(self._block):
                self.set_selected(True)

    def set_selected(
        self,
        selected: bool,
        color: Union[Tuple[int, int, int], List[int]] = None,
        redraw: bool = True
    ):
        super().set_selected(selected, color, redraw)
        if self._component_group is not None:
            self._component_group.select_block(self._block, selected)


class MachineGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    BORDER_SIZE: ClassVar[util.Size] = util.Size(5, 5)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (100, 100, 100, 255)

    _crafting_size: List
    __component_group: Union[None, "ComponentGroup"]
    __logic_component: Union[None, str]
    _logic_circuit: Union[None, "logic_circuit.LogicCircuit"]

    def __init__(
        self,
        size,
        **kwargs
    ):
        super().__init__(size, color=con.INVISIBLE_COLOR, **kwargs)
        self._rotation_count = 0
        self._logic_grid = []
        self.__component_group = None
        self.__logic_component = None
        self._logic_circuit = None

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

                lbl = GridLabel(label_size, (col_i, row_i))
                lbl.add_key_event_listener(1, self.set_grid_image, values=[(col_i, row_i)], types=["pressed"])
                lbl.add_key_event_listener(3, self.remove_grid_image, values=[(col_i, row_i)], types=["pressed"])
                self.add_widget(pos, lbl)
                row.append(lbl)
            self._logic_grid.append(row)
            
    def _get_machine_material(self):
        mat = None
        if self.__logic_component == "red:wire":
            mat = machine_materials.RedWire()
        elif self.__logic_component == "green:wire":
            mat = machine_materials.GreenWire()
        elif self.__logic_component == "blue:wire":
            mat = machine_materials.BlueWire()
        elif self.__logic_component == "red:inverter":
            mat = machine_materials.RedInverterWire()
        elif self.__logic_component == "green:inverter":
            mat = machine_materials.GreenInverterWire()
        elif self.__logic_component == "blue:inverter":
            mat = machine_materials.BlueInverterWire()
        elif self.__logic_component == "connector":
            mat = machine_materials.WireConnector()
        if mat is None:
            # crashes the game
            raise util.GameException(f"No material for logic component with name: {self.__logic_component}")
        if isinstance(mat, machine_materials.RotatableMachineComponent):
            mat.rotate(self._rotation_count)
        return mat
            
    def add_rotation(self):
        self._rotation_count += 1

    def set_component_group(self, group):
        self.__component_group = group
        self.__logic_component = None

    def set_logic_component(self, name):
        self.__logic_component = name
        self.__component_group = None

    def set_grid_image(self, grid_pos: Union[Tuple[int, int], List[int]]):
        grid_label = self._logic_grid[grid_pos[1]][grid_pos[0]]
        if self.__logic_component is not None:
            # make sure that this is guaranteed a machinecomponent
            material: machine_materials.MultiImageMachineComponent = self._get_machine_material()
            if ":" in self.__logic_component:
                colors = [self.__logic_component.split(":")[0]]
                grid_label.set_logic_image(material, colors[0])
            else:
                grid_label.set_logic_image(material, "red")
                grid_label.set_logic_image(None, "green")
                grid_label.set_logic_image(None, "blue")
                colors = ["red", "green", "blue"]

            # add the logic component
            for color in colors:
                component = material.LOGIC_COMPONENT(material, color)
                self._logic_circuit.add_component(component, grid_pos)

        elif self.__component_group is not None:
            block = self.__component_group.assign_block(grid_label.grid_pos)
            if block is not None:
                grid_label.set_component_group(block, self.__component_group)

    def remove_grid_image(self, grid_pos: Union[Tuple[int, int], List[int]]):
        grid_label = self._logic_grid[grid_pos[1]][grid_pos[0]]
        grid_label.remove_component_image()
        self._logic_circuit.remove_component(grid_pos)

    def set_logic_circuit(self, circuit):
        self._logic_circuit = circuit
        self.__init_grid(self._logic_circuit.size())


class GridLabel(widgets.Label):

    _component_group: Union[None, "ComponentGroup"]
    _logic_image: Union[None, "LogicImage"]

    def __init__(self, size, grid_pos, **kwargs):
        super().__init__(size, color=MachineGrid.COLOR, border=True, border_color=(0, 0, 0), border_width=1, **kwargs)
        self._current_indicator = None
        self.grid_pos = grid_pos

        # tracked in case of a component group
        self._component_group = None
        self._logic_image = None
        self._block = None

    def wupdate(self):
        super().wupdate()
        if self._component_group is not None:
            if self.selected and not self._component_group.is_block_selected(self._block):
                self.set_selected(False)
            if not self.selected and self._component_group.is_block_selected(self._block):
                self.set_selected(True)
        if self._logic_image is None:
            return

        # check for changed component materials
        any_changed = False
        for mat in self._logic_image.materials.values():
            if mat is not None and mat.changed:
                # have to get all changed to avoid repeated updates
                any_changed = True
        if any_changed:
            self.set_image(self._logic_image.get_surface())

    def set_selected(
        self,
        selected: bool,
        color: Union[Tuple[int, int, int], List[int]] = None,
        redraw: bool = True
    ):
        super().set_selected(selected, color, redraw)
        if self._component_group is not None:
            self._component_group.select_block(self._block, selected)

    def set_component_group(self, block, component_group):
        self._unassign_component_group()
        self._component_group = component_group
        self._block = block
        image = pygame.transform.scale(block.material.surface, (self.rect.width - 5, self.rect.height - 5))
        self._logic_image = None
        self.set_image(image)

    def set_logic_image(
        self,
        material: Union[BaseMaterial, machine_materials.RotatableMachineComponent, None],
        color,
    ):
        if self._logic_image is None:
            self._logic_image = LogicImage(util.Size(*self.rect.size) - (2, 2))
        self._logic_image.set_material(material, color)
        self._unassign_component_group()
        self.set_image(self._logic_image.get_surface())

    def _unassign_component_group(self):
        if self._component_group is not None:
            self._component_group.unassign_block(self._block)
            self._component_group.select_block(self._block, False)
            self._component_group = None
            self._block = None

    def remove_component_image(self):
        self._unassign_component_group()
        self.clean_surface()
        self._logic_image = None
        self._reset_specifications(image=True)


class LogicImage:
    # combines multiple logic images into one image and uses a cache to prevent repeated image creation if possible

    materials: Dict[str, Union[None, BaseMaterial, machine_materials.RotatableMachineComponent]]

    def __init__(self, size):
        self.materials = {"red": None, "green": None, "blue": None}
        self.rotation = 0
        self.size = size

    def set_material(
        self,
        material: Union[BaseMaterial, machine_materials.RotatableMachineComponent, None],
        component_color
    ):
        if material is None:
            self.materials[component_color] = material
            return
        if isinstance(material, machine_materials.RotatableMachineComponent):
            # if a component with new rotation is introduced reset all other materials
            if material.image_key != self.rotation:
                self.rotation = material.image_key
                for color in self.materials:
                    self.materials[color] = None
        self.materials[component_color] = material

    def get_surface(self):
        full_image = pygame.Surface(self.size)
        full_image.fill(MachineGrid.COLOR)
        for color in self.materials:
            material = self.materials[color]
            if material is None:
                continue
            surface = material.surface
            surface = pygame.transform.scale(surface, self.size)
            full_image.blit(surface, (0, 0))
        return full_image


class AmountIndicator(widgets.Label):
    def __init__(self, size, component_group: "ComponentGroup", **kwargs):
        super().__init__(size, color=MachineInterface.COLOR, text_pos=("west", "center"), selectable=False, **kwargs)
        self._component_group = component_group
        self._current_text = ""

    def wupdate(self):
        super().wupdate()
        if self._current_text != self._component_group.get_amount_text():
            self.set_text(self._component_group.get_amount_text())


class ComponentGroup:
    def __init__(self):
        self._blocks = set()
        self._selected_blocks = {}
        self._assigned_blocks = {}

    def add(self, block):
        self._blocks.add(block)

    def assign_block(self, grid_pos):
        chosen_block = None
        for block in self._blocks:
            if block.id not in self._assigned_blocks:
                self._assigned_blocks[block.id] = grid_pos
                chosen_block = block
                break
        return chosen_block

    def unassign_block(self, block):
        if block.id in self._assigned_blocks:
            return self._assigned_blocks.pop(block.id)
        return None

    def select_block(self, block, select: bool):
        self._selected_blocks[block.id] = select

    def is_block_selected(self, block):
        if block.id in self._selected_blocks:
            return self._selected_blocks[block.id]
        return False

    def remove(self, block):
        self._blocks.remove(block)
        grid_pos = None
        if block.id in self._assigned_blocks:
            grid_pos = self.unassign_block(block)
        return grid_pos

    def get_amount_text(self):
        return f"{len(self._assigned_blocks)} / {len(self._blocks)}"

    def __contains__(self, block):
        return block in self._blocks
