from abc import ABC


class LogicComponent(ABC):
    def __init__(self, material):
        self.material = material

