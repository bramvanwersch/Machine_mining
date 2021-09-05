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
    _queue: LogicQueue

    def __init__(self):
        self._wires = {col: None for col in ("red", "green", "blue")}
        self._connecting_directions = set()
        self._queue = LogicQueue()

    def next_circuit_tick(self):
        # use this function to have logicomponents take a delayed effect
        self._queue.execute_oldest()

    def get_active(
        self,
        color: str,
        direction: int
    ) -> bool:
        return self._wires[color].get_active(direction)

    def _can_connect(self, component: "CombinationComponent"):
        # get the reverse directions for a comparisson
        other_directions = set((d + 2) % 4 for d in component._connecting_directions)
        return len(other_directions & self._connecting_directions) > 0

    def add_component(
        self,
        component: "LogicComponent"
    ):
        current_component = self._wires[component.color]
        if current_component is not None:
            # remove all directions to be sure
            for direction in current_component.connectable_directions():
                self._connecting_directions.remove(direction)
            current_component.remove()

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
                if not self._can_connect(combi_component):
                    continue
                for color, component in combi_component._wires.items():
                    # add the component for both directions
                    if component is not None:
                        component.set_component_connection(self._wires[color], direction)
                    if self._wires[color] is not None:
                        self._wires[color].set_component_connection(component, (direction + 2) % 4)


class LogicComponent:

    _EMITS_POWER: bool = False  # use this flag to indicate if the component naturally emits an active state

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        color: str,
    ):
        # first the material of the wire then the state active or not
        self.material = material
        self.color = color
        self.wire_actives = self._innitial_wire_actives()
        self._connected_components = [None, None, None, None]

    def _innitial_wire_actives(self) -> List[bool]:
        return [False, False, False, False]

    def get_active(self, direction):
        return self.wire_actives[direction]

    def set_active(
        self,
        value: bool,
        activation_direction: int  # direction activation comes from
    ):
        # for a 2 sided wire
        opposing_direction = (activation_direction + 2) % 4
        self.wire_actives[activation_direction] = value
        self.wire_actives[opposing_direction] = value
        self.material.set_active(value)

    def set_component_connection(self, component, direction_index):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component

    def remove(self):
        # function to remove certain information on deletion of this component
        pass

    def connectable_directions(self):
        return self.material.connecting_directions()


class ConnectorLogicComponent(LogicComponent):
    pass
    # def set_active(
    #     self,
    #     value: bool,
    #     color: str,
    #     activation_direction: int
    # ):
    #     wire_material = self._wire_materials[color]
    #     if wire_material is None:
    #         return
    #     self._wire_actives[color][activation_direction] = value
    #     active_key = ""
    #     if any(self._wire_actives["red"]):
    #         active_key += "r"
    #     if any(self._wire_actives["green"]):
    #         active_key += "g"
    #     if any(self._wire_actives["blue"]):
    #         active_key += "b"
    #     self._wire_materials["red"].change_image_key(active_key)


class InverterLogicComponent(LogicComponent):

    EMITS_POWER: bool = True

    def _innitial_wire_actives(self) -> List[bool]:
        return [True if self.material.image_key == index else False for index in range(4)]

    def set_active(
        self,
        value: bool,
        activation_direction: int
    ):
        self.material.set_active(value)
        opposing_direction = (activation_direction + 2) % 4
        if self.material.image_key == opposing_direction:
            self.wire_actives[activation_direction] = value
            self.wire_actives[opposing_direction] = not value
