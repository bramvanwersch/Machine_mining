from typing import TYPE_CHECKING, List, Union, Dict, Set, Callable, Any
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

    def next_circuit_tick(self):
        for col in self._wires:
            component = self._wires[col]
            if component is not None:
                component.next_circuit_tick()

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


class LogicComponent:

    _EMITS_POWER: bool = False  # use this flag to indicate if the component naturally emits an active state
    _FULL_COMPONENT: bool = False  # use this flag for components with multiple color channels

    material: "MultiImageMachineComponent"
    color: str
    _active: bool
    _connected_components: List[Union[None, "LogicComponent"]]
    _queue: LogicQueue

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        # first the material of the wire then the state active or not
        self.material = material
        self.color = color
        self._active = False
        self._connected_components = [None, None, None, None]
        self._queue = LogicQueue()

    def next_circuit_tick(self):
        # use this function to have logicomponents take a delayed effect
        if len(self._queue) > 0:
            self._queue.execute_oldest()

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
        from_power_source: bool,  # needed to prevent infinite feedback loops for inverter components
        color: str
    ):
        # dont calculate if no change
        if value == self._active:
            return
        self._active = value
        self.material.set_active(value)

        # propagate signal
        if self._connected_components[propagation_direction] is not None:
            self._connected_components[propagation_direction].set_active(value, propagation_direction,
                                                                         self.power_source, self.color)

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

    def delete(self):
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
    _connected_components: Dict[str, List[Union[None, "LogicComponent"]]]
    _queue: LogicQueue

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
        self._queue = LogicQueue()

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
        self._active[color] = value
        material_key = self._get_material_image_key()
        if material_key != self.material.image_key:
            self.material.change_image_key(material_key)
        all_prop_directions = [propagation_direction, (propagation_direction + 1) % 4, (propagation_direction - 1) % 4]
        # propagate signals
        for direction in all_prop_directions:
            if self._connected_components[color][direction] is not None:
                self._connected_components[color][direction].set_active(value, direction, self.power_source, color)

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

    def delete(self):
        for color, components in self._connected_components.items():
            for direction, component in enumerate(components):
                if component is not None:
                    opposite_direction = (direction + 2) % 4
                    component.set_component_connection(None, opposite_direction, color)
                    if not component.power_source:
                        component.set_active(False, direction, self.power_source, color)
                    else:
                        component.set_active(self._active[color], direction, self.power_source, color)


class InverterLogicComponent(LogicComponent):

    _EMITS_POWER: bool = True

    def set_active(
        self,
        value: bool,
        propagation_direction: int,
        from_power_source: bool,  # needed to prevent infinite feedback loops for inverter components
        color: str
    ):
        # change the power delayed by a circuit tick
        if propagation_direction == self.material.image_key:
            self._queue.add(self._switch_active, [value])
        elif (propagation_direction + 2) % 4 == self.material.image_key and not from_power_source:
            self._propagate_signal()

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
        self._propagate_signal()

    def _propagate_signal(self):
        # propagate the signal
        opposing_direction = (self.material.image_key + 2) % 4
        if self._active is True:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(False, self.material.image_key,
                                                                               self.power_source, self.color)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(True, opposing_direction,
                                                                          self.power_source, self.color)
        else:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(True, self.material.image_key,
                                                                               self.power_source, self.color)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(False, opposing_direction,
                                                                          self.power_source, self.color)
