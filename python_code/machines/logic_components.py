from typing import TYPE_CHECKING, List, Tuple, Union, Dict

if TYPE_CHECKING:
    from block_classes.materials.machine_materials import MachineComponent
    from block_classes.materials.materials import MultiImageMaterial


class LogicComponent:

    _wire_materials: Dict[str, Union[None, Union["MachineComponent", "MultiImageMaterial"]]]
    _wire_actives: Dict[str, List[bool]]
    _surrounding_components: List[Union[None, "LogicComponent"]]

    def __init__(
        self,
        material: Union["MachineComponent", "MultiImageMaterial"],
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
        active: bool = False
    ):
        # first the material of the wire then the state active or not
        self._wire_materials = {col: material if col in colors else None for col in ("red", "green", "blue")}
        self._wire_actives = {col: [False, False, False, False] for col in ("red", "green", "blue")}
        self._configure_innitial_active(colors, material, active)
        self._surrounding_components = []

    def _configure_innitial_active(
        self,
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
        material: "MachineComponent",
        active: bool
    ):
        if active is True:
            for color in colors:
                for direction in material.connecting_directions():
                    self.set_active(True, color, direction)

    def get_active(
        self,
        color: str,
        direction: int
    ) -> bool:
        opposing_direction = (direction + 2) % 4
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return False
        connecting_dirs = wire_material.connecting_directions()
        if opposing_direction in connecting_dirs:
            return self._wire_actives[color][opposing_direction]
        return False

    def set_active(
        self,
        value: bool,
        color: str,
        direction: int
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        # for a 2 sided wire
        self._wire_actives[color][direction] = value
        self._wire_actives[color][(direction + 2) % 4] = value
        wire_material.set_active(value)

    def add_component(
        self,
        component: "LogicComponent"
    ):
        # add / overwrite current wires with a new component
        for col, values in component._wire_materials.items():
            self._wire_materials[col] = values
            self._wire_actives[col] = component._wire_actives[col]

    def set_surrounding_components(
        self,
        surrounding_components: List[Union[None, "LogicComponent"]]
    ):
        self._surrounding_components = surrounding_components
        for index, component in enumerate(surrounding_components):
            if component is not None:
                for color in self._wire_materials:
                    if self._wire_materials[color] is not None:
                        if component.get_active(color, index):
                            self.set_active(True, color, index)
                    # set the component in the opposite direction
                    component._set_surrounding_component(component, (index + 2) % 4)

    def _set_surrounding_component(self, component, direction_index):
        # N = 0, E = 1, S = 2, W = 3
        self._surrounding_components[direction_index] = component


class ConnectorLogicComponent(LogicComponent):

    def set_active(
        self,
        value: bool,
        color: str,
        direction: int
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        self._wire_actives[color][direction] = value
        active_key = ""
        if any(self._wire_actives["red"]):
            active_key += "r"
        if any(self._wire_actives["green"]):
            active_key += "g"
        if any(self._wire_actives["blue"]):
            active_key += "b"
        wire_material.image_key = active_key


class InverterLogicComponent(LogicComponent):

    def _configure_innitial_active(
        self,
        colors: Union[List[str], Tuple[str], Tuple[str, str], Tuple[str, str, str]],
        material: Union["MachineComponent", "MultiImageMaterial"],
        active: bool
    ):
        for color in colors:
            for direction in material.connecting_directions():
                if material.image_key == direction:
                    self.set_active(active, color, direction)
                else:
                    self.set_active(not active, color, direction)

    def set_active(
        self,
        value: bool,
        color: str,
        direction: int
    ):
        wire_material = self._wire_materials[color]
        if wire_material is None:
            return
        self._wire_actives[color][direction] = value
        if direction != wire_material.image_key and value is True:
            wire_material.set_active(value)
        elif wire_material.active:
            pass