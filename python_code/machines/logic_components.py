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

    def pop(self):
        if self._queue[self._queue_pos] is None:
            return
        self._queue[self._queue_pos][0](*self._queue[self._queue_pos][1])
        self._queue[self._queue_pos] = None

        if self._queue_pos + 1 >= self.QUEUE_LENGTH:
            self._queue_pos = 0
        else:
            self._queue_pos += 1


class LogicComponent:

    _wire_materials: Dict[str, Union[None, Union["MultiImageMachineComponent", "MultiImageMaterial"]]]
    _wire_actives: Dict[str, List[bool]]
    _connected_components: List[Union[None, "LogicComponent"]]
    _connecting_directions: Set[int]
    _queue: LogicQueue

    def __init__(
        self,
        material: Union["MultiImageMachineComponent", "MultiImageMaterial"],
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
    ):
        # first the material of the wire then the state active or not
        self._wire_materials = {col: material if col in colors else None for col in ("red", "green", "blue")}
        self._wire_actives = {col: [False, False, False, False] for col in ("red", "green", "blue")}
        self._connected_components = [None, None, None, None]
        self._connecting_directions = set()
        self._queue = LogicQueue()
        self._configure_innitial_active(colors, material)

    def next_circuit_tick(self):
        # use this function to have logicomponents take a delayed effect
        pass

    def _configure_innitial_active(
        self,
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
        material: "MultiImageMachineComponent",
    ):
        # use this method to set innitial active states for more complex components
        pass

    def get_active(
        self,
        color: str,
        direction: int
    ) -> bool:
        opposing_direction = (direction + 2) % 4
        return self._wire_actives[color][opposing_direction]

    def _can_connect(self, component: "LogicComponent"):
        other_directions = set((d + 2) % 4 for d in component._connecting_directions)
        return len(other_directions & self._connecting_directions) > 0

    def set_active(
        self,
        value: bool,
        color: str,
        activation_direction: int  # direction activation comes from
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        # for a 2 sided wire
        opposing_direction = (activation_direction + 2) % 4
        self._wire_actives[color][activation_direction] = value
        self._wire_actives[color][opposing_direction] = value
        wire_material.set_active(value)

    def add_component(
        self,
        component: "LogicComponent"
    ):
        for wire_mat in component._wire_materials.values():
            if wire_mat is not None:
                self._connecting_directions = set(wire_mat.connecting_directions()) | self._connecting_directions
        # add / overwrite current wires with a new component
        for col, values in component._wire_materials.items():
            self._wire_materials[col] = values
            self._wire_actives[col] = component._wire_actives[col]

    def set_connected_component(
        self,
        surrounding_components: List[Union[None, "LogicComponent"]]
    ):
        for index, component in enumerate(surrounding_components):
            if component is not None:
                if self._can_connect(component):
                    self._connected_components[index] = component
                    component._set_component_connection(self, (index + 2) % 4)

    def _set_component_connection(self, component, direction_index):
        # N = 0, E = 1, S = 2, W = 3
        self._connected_components[direction_index] = component


class ConnectorLogicComponent(LogicComponent):

    def set_active(
        self,
        value: bool,
        color: str,
        activation_direction: int
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        self._wire_actives[color][activation_direction] = value
        active_key = ""
        if any(self._wire_actives["red"]):
            active_key += "r"
        if any(self._wire_actives["green"]):
            active_key += "g"
        if any(self._wire_actives["blue"]):
            active_key += "b"
        self._wire_materials["red"].change_image_key(active_key)


class InverterLogicComponent(LogicComponent):

    def _configure_innitial_active(
        self,
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
        material: "MultiImageMachineComponent",
    ):
        for color in colors:
            wire_material = self._wire_materials[color]
            if wire_material is not None:
                self.set_active(False, color, (wire_material.image_key + 2) % 4)

    def set_active(
        self,
        value: bool,
        color: str,
        activation_direction: int
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        wire_material.set_active(value)
        opposing_direction = (activation_direction + 2) % 4
        if wire_material.image_key == opposing_direction:
            self._wire_actives[color][activation_direction] = value
            self._wire_actives[color][opposing_direction] = not value
