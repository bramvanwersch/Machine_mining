from typing import TYPE_CHECKING, List, Union, Dict, Set, Callable, Any, Tuple

import utility.constants as con
import utility.utilities as util

if TYPE_CHECKING:
    from block_classes.materials.machine_materials import MultiImageMachineComponent
    from block_classes.materials.materials import MultiImageMaterial


class CombinationComponent:
    # can hold up to three components of different colors

    _wires: Dict[str, Union[None, Union["LogicComponent"]]]
    _connecting_directions: Set[int]

    def __init__(self):
        self._wires = {col: None for col in ("red", "green", "blue")}
        self._connecting_directions = set()

    def next_circuit_tick(self):
        for col in self._wires:
            component = self._wires[col]
            if component is not None:
                component.next_circuit_tick()

    def reset_logic_components(self):
        for component in self._wires.values():
            if component is not None:
                component.reset_component()

    def delete(self):
        for color in self._wires:
            if self._wires[color] is None:
                continue
            self._wires[color].delete()

    def get_active(
        self,
        color: str,
        direction: int
    ) -> bool:
        return self._wires[color].get_active(direction)

    def _can_connect(
        self,
        component: "CombinationComponent",
        component_direction: int
    ) -> bool:
        # get the reverse directions for a comparisson
        other_directions = set((d + 2) % 4 for d in component._connecting_directions)
        if component_direction in self._connecting_directions:
            return len(other_directions & self._connecting_directions) > 0
        return False

    def add_component(
        self,
        component: "LogicComponent"
    ):
        # if component takes up all color connection slots add it to all slots
        if component.full_component:
            colors = con.WIRE_COLORS
        else:
            colors = [component.color]
        for color in colors:
            current_component = self._wires[color]
            if current_component is not None:
                # remove all directions to be sure
                for direction in current_component.connectable_directions():
                    self._connecting_directions.discard(direction)
                current_component.delete()

            # add new directions and component
            self._wires[color] = component
            for direction in component.connectable_directions():
                self._connecting_directions.add(direction)

    def set_connected_component(
        self,
        surrounding_components: List[Union[None, "CombinationComponent"]]
    ):
        for direction, combi_component in enumerate(surrounding_components):
            if combi_component is None:
                continue
            # make sure that the combination components can connect in the first place
            if not self._can_connect(combi_component, direction):
                continue
            for color, component in combi_component._wires.items():
                # add the component for both directions
                if self._wires[color] is not None:
                    self._wires[color].set_component_connection(component, direction, color)
                if component is not None:
                    component.set_component_connection(self._wires[color], (direction + 2) % 4, color)


class LogicComponent:

    _EMITS_POWER: bool = False  # use this flag to indicate if the component naturally emits an active state
    _FULL_COMPONENT: bool = False  # use this flag for components with multiple color channels

    material: "MultiImageMachineComponent"
    color: str
    _active: bool
    _connected_components: List[Union[None, "LogicComponent"]]
    _next_action: Union[None, Tuple[Callable, List[Any]]]

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        self.id = util.unique_id()  # identify what component is sending a signal
        self._signal_received_ids = set()
        self._activated_by_power_source = False
        self.material = material
        self.color = color
        self._active = False
        self._connected_components = [None, None, None, None]
        self._next_action = None

    def next_circuit_tick(self):
        # use this function to have logicomponents take a delayed effect
        if self._next_action is not None:
            function, values = self._next_action
            # allow the next action to be set in the function call
            self._next_action = None
            function(*values)

    def reset_component(self):
        # reset values that are temporarily set
        self._signal_received_ids = set()
        self._activated_by_power_source = False

    def get_active(
        self,
        direction: int
    ) -> bool:
        # return if a given direction gives a active signal --> normal wire is active on all connectable sites
        if direction is self.connectable_directions():
            return self._active
        return False

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        orig_signal_id: int,
        color: str,
        from_power_source: bool
    ):
        # dont calculate if no change or of repeated signals are send
        if value == self._active or orig_signal_id in self._signal_received_ids:
            return
        if value is True and from_power_source:
            self._activated_by_power_source = True
        elif value is False and self._activated_by_power_source is True:
            return
        self._active = value
        self.material.set_active(value)

        self._signal_received_ids.add(orig_signal_id)

        # propagate signal
        if self._connected_components[propagation_direction] is not None:
            self._connected_components[propagation_direction].set_active(value, propagation_direction,
                                                                         orig_signal_id, self.color, from_power_source)

    def set_component_connection(
        self,
        component: Union[None, "LogicComponent"],
        direction_index: int,
        color: str
    ):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component
        if self._active and component is not None:
            component.set_active(True, direction_index, self.id, self.color, self.power_source)

    def delete(self):
        for direction, component in enumerate(self._connected_components):
            if component is not None:
                opposite_direction = (direction + 2) % 4
                component.set_component_connection(None, opposite_direction, self.color)
                if not component.power_source:
                    component.set_active(False, direction, self.id, self.color, self.power_source)
                else:
                    component.set_active(self._active, direction, self.id, self.color, self.power_source)

    def connectable_directions(self):
        return self.material.connecting_directions()

    @property
    def power_source(self) -> bool:
        return self._EMITS_POWER

    @property
    def full_component(self) -> bool:
        return self._FULL_COMPONENT


class ConnectorLogicComponent(LogicComponent):

    _FULL_COMPONENT: bool = True

    _active: Dict[str, bool]
    _connected_components: Dict[str, List[Union[None, "LogicComponent"]]]

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        super().__init__(material, color)
        self._active = {"red": False, "green": False, "blue": False}
        self._connected_components = {"red": [None, None, None, None],
                                      "green": [None, None, None, None],
                                      "blue": [None, None, None, None]}

    def get_active(
        self,
        direction: int
    ) -> bool:
        # return if a given direction gives an active signal
        if direction is self.connectable_directions():
            return all(self._active.values())
        return False

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        orig_signal_id: int,
        color: str,
        from_power_source: bool
    ):
        if orig_signal_id in self._signal_received_ids:
            return
        if value is True and from_power_source:
            self._activated_by_power_source = True
        elif value is False and self._activated_by_power_source is True:
            return
        self._signal_received_ids.add(orig_signal_id)
        self._active[color] = value
        material_key = self._get_material_image_key()
        if material_key != self.material.image_key:
            self.material.change_image_key(material_key)
        all_prop_directions = [propagation_direction, (propagation_direction + 1) % 4, (propagation_direction - 1) % 4]
        # propagate signals
        for direction in all_prop_directions:
            if self._connected_components[color][direction] is not None:
                self._connected_components[color][direction].set_active(value, direction, orig_signal_id, color,
                                                                        from_power_source)

    def _get_material_image_key(self):
        active_key = ""
        if self._active["red"] is True:
            active_key += "r"
        if self._active["green"] is True:
            active_key += "g"
        if self._active["blue"] is True:
            active_key += "b"
        return active_key

    def set_component_connection(
        self,
        component: Union[None, "LogicComponent"],
        direction_index: int,
        color: str
    ):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[color][direction_index] = component
        if self._active[color] is True and component is not None:
            component.set_active(True, direction_index, self.id, color, self.power_source)

    def delete(self):
        for color, components in self._connected_components.items():
            for direction, component in enumerate(components):
                if component is not None:
                    opposite_direction = (direction + 2) % 4
                    component.set_component_connection(None, opposite_direction, color)
                    if not component.power_source:
                        component.set_active(False, direction, self.id, color, self.power_source)
                    else:
                        component.set_active(self._active[color], direction, self.id, color, self.power_source)


class InverterLogicComponent(LogicComponent):

    _EMITS_POWER: bool = True

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        orig_signal_id: int,
        color: str,
        from_power_source: bool
    ):
        # change the power delayed by a circuit tick
        if propagation_direction == self.material.image_key:
            self._next_action = (self._switch_active, [value])
        elif orig_signal_id in self._signal_received_ids:
            return
        elif (propagation_direction + 2) % 4 == self.material.image_key:
            self._propagate_signal(self.id)
        self._signal_received_ids.add(orig_signal_id)

    def get_active(
        self,
        direction: int
    ) -> bool:
        # return if a given direction gives a active signal --> normal wire is active on all connectable sites
        if direction is self.connectable_directions():
            # if requested direction is facing direction the signal is inverted from active state
            if direction == self.material.image_key:
                return not self._active
            else:
                return self._active
        return False

    def set_component_connection(
        self,
        component: Union[None, "LogicComponent"],
        direction_index: int,
        color: str
    ):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component
        self._propagate_signal(self.id)

    def _switch_active(
        self,
        value: bool,
    ):
        self.material.set_active(value)
        self._active = value
        self._propagate_signal(self.id)

    def _propagate_signal(self, orig_signal_id):
        # propagate the signal
        opposing_direction = (self.material.image_key + 2) % 4
        if self._active is True:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(False, self.material.image_key,
                                                                               orig_signal_id, self.color,
                                                                               self.power_source)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(True, opposing_direction,
                                                                          orig_signal_id, self.color, self.power_source)
        else:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(True, self.material.image_key,
                                                                               orig_signal_id, self.color,
                                                                               self.power_source)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(False, opposing_direction,
                                                                          orig_signal_id, self.color, self.power_source)
