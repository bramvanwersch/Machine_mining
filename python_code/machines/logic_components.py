from typing import TYPE_CHECKING, List, Tuple, Union, Dict, Set, Callable, Any

if TYPE_CHECKING:
    from block_classes.materials.machine_materials import MultiImageMachineComponent
    from block_classes.materials.materials import MultiImageMaterial


class LogicQueue:
    QUEUE_LENGTH: int = 10

    _queue: List[Union[None, Tuple[Callable, List[Any]]]]

    def __init__(self):
        self._queue = [None for _ in range(self.QUEUE_LENGTH)]
        self._insertion_pos = 0
        self._queue_pos = 0

    def add(self, function: Callable, values: List[Any] = None):
        if self._queue[self._insertion_pos] is not None:
            print("Warning: Queue is full deleting old call.")
        self._queue[self._insertion_pos] = (function, values)

        if self._insertion_pos + 1 >= self.QUEUE_LENGTH:
            self._insertion_pos = 0
        else:
            self._insertion_pos += 1

    def execute_oldest(self):
        # execute the oldest call in the queue, if there is a call
        if self._queue[self._queue_pos] is None:
            return
        self._queue[self._queue_pos][0](*self._queue[self._queue_pos][1])
        self._queue[self._queue_pos] = None

        if self._queue_pos + 1 >= self.QUEUE_LENGTH:
            self._queue_pos = 0
        else:
            self._queue_pos += 1


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
        current_component = self._wires[component.color]
        if current_component is not None:
            # remove all directions to be sure
            for direction in current_component.connectable_directions():
                self._connecting_directions.discard(direction)
            current_component.delete()

        # add new directions and component
        self._wires[component.color] = component
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
                        component.set_component_connection(self._wires[color], (direction + 2) % 4)
                    if self._wires[color] is not None:
                        self._wires[color].set_component_connection(component, direction)


class LogicComponent:

    _EMITS_POWER: bool = False  # use this flag to indicate if the component naturally emits an active state
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
        propagation_direction: int
    ):
        # dont calculate if no change
        if value == self._active:
            return
        self._active = value
        self.material.set_active(value)

        # propagate signal
        if self._connected_components[propagation_direction] is not None:
            self._connected_components[propagation_direction].set_active(value, propagation_direction)

    def set_component_connection(self, component: Union[None, "LogicComponent"], direction_index: int):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component
        if self._active and component is not None:
            component.set_active(True, direction_index)

    def delete(self):
        for direction, component in enumerate(self._connected_components):
            if component is not None:
                opposite_direction = (direction + 2) % 4
                component.set_component_connection(None, opposite_direction)
                if not component.power_source:
                    component.set_active(False, direction)

    def connectable_directions(self):
        return self.material.connecting_directions()

    @property
    def power_source(self):
        return self._EMITS_POWER


class ConnectorLogicComponent(LogicComponent):
    pass
    # def set_active(
    #     self,
    #     value: bool,
    #     activation_direction: int
    # ):
    #     active_key = ""
    #     if any(self._wire_actives["red"]):
    #         active_key += "r"
    #     if any(self._wire_actives["green"]):
    #         active_key += "g"
    #     if any(self._wire_actives["blue"]):
    #         active_key += "b"
    #     self.material.change_image_key(active_key)


class InverterLogicComponent(LogicComponent):

    _EMITS_POWER: bool = True

    def set_active(
        self,
        value: bool,
        propagation_direction: int
    ):
        # dont calculate if no change
        if value == self._active:
            return
        # change the power delayed by a circuit tick
        if propagation_direction == self.material.image_key:
            self._queue.add(self._switch_active, [value])

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

    def set_component_connection(self, component, direction_index):
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
                self._connected_components[self.material.image_key].set_active(False, self.material.image_key)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(True, opposing_direction)
        else:
            if self._connected_components[self.material.image_key] is not None:
                self._connected_components[self.material.image_key].set_active(True, self.material.image_key)
            if self._connected_components[opposing_direction] is not None:
                self._connected_components[opposing_direction].set_active(False, opposing_direction)
