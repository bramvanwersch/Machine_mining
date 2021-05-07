from abc import ABC, abstractmethod
import json


class Serializer(ABC):
    """
    adapted from gamci/cblaster :)
    """

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    def from_dict(cls, **arguments):
        return cls(**arguments)

    def to_json(self, fp=None, **kwargs):
        """Serialises class to JSON."""
        d = self.to_dict()
        if fp:
            json.dump(d, fp, **kwargs)
        else:
            return json.dumps(d, **kwargs)

    @classmethod
    def from_json(cls, js):
        """Instantiates class from JSON handle."""
        if isinstance(js, str):
            d = json.loads(js)
        else:
            d = json.load(js)
        return cls.from_dict(**d)


class Savable(ABC):

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, dct):
        pass
