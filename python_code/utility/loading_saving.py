from abc import ABC, abstractmethod
from typing import Dict, Any


class Savable(ABC):

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


class Loadable(ABC):

    def __init_load__(self, **kwargs):
        # method that can be defined that will be run as the init when loading the class from json. Dont overwrite if
        # no __init__ is needed
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, dct):
        pass

    @classmethod
    def load(cls, **init_arguments):
        obj = cls.__new__(cls)
        obj.__init_load__(**init_arguments)
        return obj
