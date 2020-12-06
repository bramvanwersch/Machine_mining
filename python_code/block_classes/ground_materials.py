

# library imports
from abc import ABC, abstractmethod
from typing import Tuple, ClassVar

#own imports
from block_classes.materials import MaterialCollection, ColorMaterial, UnbuildableMaterial
from utility.image_handling import image_sheets


class FillerMaterial(ColorMaterial, ABC):

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MEAN_DEPTH(self) -> float:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def SD(self) -> float:
        pass


class TopDirt(FillerMaterial):

    MEAN_DEPTH: ClassVar[float] = 0.0
    SD: ClassVar[float] = 2.0
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (137, 79, 33)


class Stone(FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    HARDNESS = 3
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (155, 155, 155)


class GreenStone(FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    HARDNESS = 3
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (126, 155, 126)


class RedStone(FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    HARDNESS = 3
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (155, 126, 126)


class BlueStone(FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    HARDNESS = 3
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (126, 126, 155)


class YellowStone(FillerMaterial):

    MEAN_DEPTH = 30
    SD = 10
    HARDNESS = 3
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (155, 155, 126)


class StoneCollection(MaterialCollection):

    MATERIAL_PROBABILITIES = {Stone:0.95, GreenStone:0.01, RedStone:0.01, BlueStone:0.01, YellowStone:0.01}


class Granite(FillerMaterial):

    HARDNESS = 10
    MEAN_DEPTH = 70
    SD = 7
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (105, 89, 76)


class FinalStone(FillerMaterial):

    HARDNESS = 20
    MEAN_DEPTH = 100
    SD = 2
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (199, 127, 195)


class Dirt(ColorMaterial):

    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (107, 49, 13)


class OreMaterial(ColorMaterial, ABC):
    """
    Abstract class for all ores. Contains a gaussian distribution for the
    likelyhood of a ore to be at certain percent depth
    """
    WHEIGHT = 2
    HARDNESS = 5

    def _configure_color(self):
        """
        Make sure the color is not changed to make clearer what is a certain ore

        :return: the base color
        """
        return self.BASE_COLOR

    @property
    @abstractmethod
    def MEAN_DEPTH(self):
        return 0

    @property
    @abstractmethod
    def SD(self):
        return 0

    @property
    @abstractmethod
    def CLUSTER_SIZE(self):
        return


class FuelMaterial(ABC):

    @property
    @abstractmethod
    def FUEL_VALUE(self):
        return 0


class Iron(OreMaterial):

    MEAN_DEPTH = 50
    SD = 30
    CLUSTER_SIZE = (2, 10)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (184, 98, 92)
    WHEIGHT = 3


class Gold(OreMaterial):

    HARDNESS = 3
    MEAN_DEPTH = 70
    SD = 3
    CLUSTER_SIZE = (2, 6)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (235, 173, 16)
    WHEIGHT = 5


class Zinc(OreMaterial):

    HARDNESS = 3
    MEAN_DEPTH = 20
    SD = 5
    CLUSTER_SIZE = (2, 15)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (58, 90, 120)


class Copper(OreMaterial):

    HARDNESS = 4
    MEAN_DEPTH = 30
    SD = 5
    CLUSTER_SIZE = (5, 8)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (189, 99, 20)


class Coal(OreMaterial, FuelMaterial):

    MEAN_DEPTH = 10
    SD = 50
    CLUSTER_SIZE = (6, 12)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (10, 10, 10)
    TEXT_COLOR = (255,255,255)
    FUEL_VALUE = 5


class Titanium(OreMaterial):

    HARDNESS = 50
    MEAN_DEPTH = 100
    SD = 2
    CLUSTER_SIZE = (1, 2)
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (152, 196, 237)
    WHEIGHT = 10


class IronIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((70, 10))
        return image


class GoldIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((80, 10))
        return image


class ZincIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((90, 10))
        return image


class CopperIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((0, 20))
        return image


class TitaniumIngot(UnbuildableMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((10, 20))
        return image

