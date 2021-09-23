from typing import List, Union, Tuple, TYPE_CHECKING

import utility.utilities as util
from machines.logic_components import CombinationComponent

if TYPE_CHECKING:
    from machines.logic_components import LogicComponent


class LogicCircuit:

    _components: List[List[Union["CombinationComponent", None]]]

    def __init__(
        self,
        grid_size: util.Size
    ):
        if grid_size.height == 0 or grid_size.width == 0:
            raise util.GameException("Logic circuit height and width have to be at least 1")
        self._components = [[None for _ in range(grid_size.width)] for _ in range(grid_size.height)]
        self._power_components = set()

    def update(self):
        for row in self._components:
            for component in row:
                component.next_circuit_tick()

    def add_component(
        self,
        component: "LogicComponent",
        pos: Union[List[int], Tuple[int, int]]
    ):

        if self._components[pos[1]][pos[0]] is not None:
            self._components[pos[1]][pos[0]].add_component(component)
            self._components[pos[1]][pos[0]].set_connected_component(self._get_neighbouring_components(pos))
        else:
            combi_component = CombinationComponent()
            combi_component.add_component(component)
            self._components[pos[1]][pos[0]] = combi_component
            self._components[pos[1]][pos[0]].set_connected_component(self._get_neighbouring_components(pos))

    def _get_neighbouring_components(
        self,
        pos: Union[List[int], Tuple[int, int]]
    ) -> List[Union[None, "CombinationComponent"]]:
        # return list of N E S W
        components = [None, None, None, None]
        # north
        if pos[1] > 0:
            components[0] = self._components[pos[1] - 1][pos[0]]
        # east
        if pos[0] < len(self._components[0]) - 1:
            components[1] = self._components[pos[1]][pos[0] + 1]
        # south
        if pos[1] < len(self._components) - 1:
            components[2] = self._components[pos[1] + 1][pos[0]]
        # west
        if pos[0] > 0:
            components[3] = self._components[pos[1]][pos[0] - 1]
        return components

    def remove_component(
        self,
        pos: Union[List[int], Tuple[int, int]]
    ):
        self._components[pos[1]][pos[0]] = None

    def size(self) -> util.Size:
        return util.Size(len(self._components[0]), len(self._components))
