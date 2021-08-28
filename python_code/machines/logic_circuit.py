import utility.utilities as util


class LogicCircuit:
    def __init__(
        self,
        grid_size: util.Size
    ):
        self._components = [[None for _ in range(grid_size.width)] for _ in range(grid_size.height)]

    def add_component(self, component, pos):
        self._components[pos[1]][pos[0]] = component

    def remove_component(self, pos):
        self._components[pos[1]][pos[0]] = None

    def size(self) -> util.Size:
        return util.Size(len(self._components[0]), len(self._components))
