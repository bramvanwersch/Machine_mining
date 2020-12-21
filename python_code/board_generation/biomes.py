from abc import ABC, abstractmethod
from typing import List, Union, Set, Dict, TYPE_CHECKING, ClassVar

import utility.utilities as util
import block_classes.block_utility as block_util
import block_classes.ground_materials as ground_materials
if TYPE_CHECKING:
    from block_classes.materials import DepthMaterial
    from block_classes.flora_materials import FloraMaterial


all_biomes: List[type]


class Biome(ABC):
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]]
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]]
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]]
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]]

    def __init__(
        self,
        x_gaussian: util.Gaussian,
        y_gaussian: util.Gaussian,
    ):
        self.distribution = util.TwoDimensionalGaussian(x_gaussian, y_gaussian)

    def get_likelyhood_at_coord(self, x: int, y: int) -> float:
        return self.distribution.probability(x, y)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FILLER_MATERIALS(self) -> List["DepthMaterial"]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def ORE_MATERIALS(self) -> List["DepthMaterial"]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FLORA_MATERIALS(self) -> List["FloraMaterial"]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def BACKGROUND_MATERIALS(self) -> List["DepthMaterial"]:
        pass

    def get_filler_lh_at_depth(self, depth: int) -> Dict[str, float]:
        return self.__get_material_lh_at_depth(self.FILLER_MATERIALS, depth)

    def get_ore_lh_at_depth(self, depth) -> Dict[str, float]:
        return self.__get_material_lh_at_depth(self.ORE_MATERIALS, depth)

    def get_flora_lh_at_depth(self, depth) -> List[Dict[str, float]]:
        """Give likelyhoods for all growing directions"""
        return [self.__get_material_lh_at_depth([m for m in self.FLORA_MATERIALS if m.START_DIRECTION == 0], depth),
                self.__get_material_lh_at_depth([m for m in self.FLORA_MATERIALS if m.START_DIRECTION == 1], depth),
                self.__get_material_lh_at_depth([m for m in self.FLORA_MATERIALS if m.START_DIRECTION == 2], depth),
                self.__get_material_lh_at_depth([m for m in self.FLORA_MATERIALS if m.START_DIRECTION == 3], depth)]

    def get_background_lh_at_depth(self, depth) -> Dict[str, float]:
        return self.__get_material_lh_at_depth(self.BACKGROUND_MATERIALS, depth)

    def __get_material_lh_at_depth(self, material_list: Union[List, Set], depth: int) -> Dict[str, float]:
        """Get the likelyhood that a material in a collection is at a given depth given the gaussian function associated
        with it

        Args:
            material_list (iterable): an iterable list of material types
            depth (int): integer of the depth.

        Returns:
            Dictionary containing the material names linked to a normalised likelyhood that the material is at the
            given depth
        """
        likelyhoods = []
        material_list = list(material_list)
        for material in material_list:
            lh = material.get_lh_at_depth(depth)
            likelyhoods.append(round(lh, 10))
        norm_likelyhoods = util.normalize(likelyhoods)
        return {material_list[index].name(): lh for index, lh in enumerate(norm_likelyhoods)}


class NormalBiome(Biome):
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]] = block_util.filler_materials
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]] = block_util.ore_materials
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]] = block_util.flora_materials
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]] = [ground_materials.Dirt()]


all_biomes = [NormalBiome]
