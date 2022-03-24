from typing import TYPE_CHECKING, List, Union, Dict, Set, Callable, Any, Iterator
from collections import deque

import utility.constants as con

if TYPE_CHECKING:
    from block_classes.materials.machine_materials import MultiImageMachineComponent
    from block_classes.materials.materials import MultiImageMaterial


class LogicQueue:
    MAX_QUEUE_LENGTH: int = 10

    _queue: deque

    def __init__(self):
        self._queue = deque()

    def add(self, function: Callable, values: List[Any] = None):
        if len(self._queue) == self.MAX_QUEUE_LENGTH:
            print(f"Warning: Cannot add {function} to queue. Queue is full.")
            return
        self._queue.append((function, values))

    def execute_oldest(self) -> Any:
        function, values = self._queue.popleft()
        # execute the function
        return_value = function(*values)
        return return_value

    def __len__(self) -> int:
        return len(self._queue)


class CombinationComponent:
    # can hold up to three components of different colors

    _wires: Dict[str, Union[None, Union["LogicComponent"]]]
    _connecting_directions: Set[int]

    def __init__(self):
        self._wires = {col: None for col in ("red", "green", "blue")}
        self._connecting_directions = set()

    def reset_component(self):
        for col in self._wires:
            component = self._wires[col]
            if component is not None:
                component.reset_component()

    def clear(self):
        for color in self._wires:
            if self._wires[color] is None:
                continue
            self._wires[color].reset_connections()

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
                current_component.reset_connections()

            # add new directions and component
            self._wires[color] = component
            for direction in component.connectable_directions():
                self._connecting_directions.add(direction)

    def set_connected_component(
        self,
        surrounding_components: List[Union[None, "CombinationComponent"]]
    ):
        for direction, combi_component in enumerate(surrounding_components):
            if combi_component is not None:
                # make sure that the combination components can connect in the first place
                if not self._can_connect(combi_component, direction):
                    continue
                for color, component in combi_component._wires.items():
                    # add the component for both directions
                    if component is not None:
                        component.set_component_connection(self._wires[color], (direction + 2) % 4, color)
                    if self._wires[color] is not None:
                        self._wires[color].set_component_connection(component, direction, color)

    def __iter__(self) -> Iterator["LogicComponent"]:
        return iter(self._wires.values())


class LogicComponent:

    _EMITS_POWER: bool = False  # use this flag to indicate if the component naturally emits an active state
    _FULL_COMPONENT: bool = False  # use this flag for components with multiple color channels

    material: "MultiImageMachineComponent"
    color: str
    _activated_this_tick: bool
    _active: bool
    _connected_components: List[Union[None, "LogicComponent"]]

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        # first the material of the wire then the state active or not
        self.material = material
        self.color = color
        self._activated_this_tick = False
        self._active = False
        self._connected_components = [None, None, None, None]

    def update(self):
        # used to update components for power transfer for instance
        pass

    def get_active(
        self,
        direction: int
    ) -> bool:
        # return if a given direction gives a active signal --> normal wire is active on all connectable sites
        if direction is self.connectable_directions():
            return self._active
        return False

    def get_active_state(self) -> bool:
        # return if the state of the component is active
        return self._active

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        from_power_source: bool,  # needed to prevent infinite feedback loops for inverter components
        color: str
    ):
        # dont calculate again
        if self._activated_this_tick:
            return
        self._change_material_active(value)

        # propagate signal
        if self._connected_components[propagation_direction] is not None:
            self._activated_this_tick = True
            self._connected_components[propagation_direction].set_active(value, propagation_direction,
                                                                         self.power_source, self.color)

    def reset_component(self):
        # will be set while updating and makes sure that unpowered wires are unpowered
        self._change_material_active(False)
        self._activated_this_tick = False

    def set_component_connection(
        self,
        component: Union[None, "LogicComponent"],
        direction_index: int,
        color: str
    ):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component
        if self._active and component is not None:
            component.set_active(True, direction_index, self.power_source, self.color)

    def reset_connections(self):
        for direction, component in enumerate(self._connected_components):
            if component is not None:
                opposite_direction = (direction + 2) % 4
                component.set_component_connection(None, opposite_direction, self.color)
                if not component.power_source:
                    component.set_active(False, direction, self.power_source, self.color)
                else:
                    component.set_active(self._active, direction, self.power_source, self.color)

    def connectable_directions(self):
        return self.material.connecting_directions()

    def _change_material_active(
        self,
        value: bool
    ):
        self._active = value
        if value != self._active:
            self.material.set_active(value)

    @property
    def power_source(self) -> bool:
        return self._EMITS_POWER

    @property
    def full_component(self) -> bool:
        return self._FULL_COMPONENT


class ConnectorLogicComponent(LogicComponent):

    _FULL_COMPONENT: bool = True

    color: str
    _active: Dict[str, bool]
    _activated_this_tick: Dict[str, bool]
    _connected_components: Dict[str, List[Union[None, "LogicComponent"]]]

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        super().__init__(material, color)
        self._active = {"red": False, "green": False, "blue": False}
        self._activated_this_tick = {"red": False, "green": False, "blue": False}
        self._connected_components = {"red": [None, None, None, None],
                                      "green": [None, None, None, None],
                                      "blue": [None, None, None, None]}

    def get_active(
        self,
        direction: int
    ) -> bool:
        # return if a given direction gives a active signal
        if direction is self.connectable_directions():
            return all(self._active.values())
        return False

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        from_power_source: bool,  # needed to prevent infinite feedback loops for inverter components
        color: str
    ):
        if self._activated_this_tick[color]:
            return
        self._change_material_active(value, color)
        all_prop_directions = [propagation_direction, (propagation_direction + 1) % 4, (propagation_direction - 1) % 4]
        # propagate signals
        for direction in all_prop_directions:
            if self._connected_components[color][direction] is not None:
                self._activated_this_tick[color] = True
                self._connected_components[color][direction].set_active(value, direction, self.power_source, color)

    def reset_component(self):
        for color in self._activated_this_tick:
            self._activated_this_tick[color] = False
            self._change_material_active(False, color)

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
        if self._active[color] and component is not None:
            component.set_active(True, direction_index, self.power_source, color)

    def reset_connections(self):
        for color, components in self._connected_components.items():
            for direction, component in enumerate(components):
                if component is not None:
                    opposite_direction = (direction + 2) % 4
                    component.set_component_connection(None, opposite_direction, color)
                    if not component.power_source:
                        component.set_active(False, direction, self.power_source, color)
                    else:
                        component.set_active(self._active[color], direction, self.power_source, color)

    def _change_material_active(
        self,
        value: bool,
        color: str = "red"  # keep it sort of consistent :/
    ):
        self._active[color] = value
        material_key = self._get_material_image_key()
        if material_key != self.material.image_key:
            self.material.change_image_key(material_key)


class InverterLogicComponent(LogicComponent):

    _EMITS_POWER: bool = True

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        from_power_source: bool,  # needed to prevent infinite feedback loops for inverter components
        color: str
    ):
        self._activated_this_tick = True

        # change the power delayed by a circuit tick
        if propagation_direction == self.material.image_key:
            self._switch_active(value)

    def update(self):
        self._propagate_signal()

    def reset_component(self):
        # dont change p[ower off here since this is a controlling power component
        self._activated_this_tick = False

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
        self._propagate_signal()

    def _switch_active(
        self,
        value: bool,
    ):
        self.material.set_active(value)
        self._active = value

    def _propagate_signal(self):
        # propagate the signal
        if self._active:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(False, self.material.image_key,
                                                                               self.power_source, self.color)
        else:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(True, self.material.image_key,
                                                                               self.power_source, self.color)
