

class LogicCircuit:
    def __init__(self):
        self._components = []

    def add_component(self, component, pos):
        self._components.append(component)
