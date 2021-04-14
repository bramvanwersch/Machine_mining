from abc import ABC, abstractmethod
from typing import List, Union, Set, Dict, TYPE_CHECKING, ClassVar, Type
from random import choices

from utility import utilities as util, constants as con
import block_classes.environment_materials as environment_materials
import block_classes.ground_materials as ground_materials
from board_generation.structures import base_structures, abandoned_mine
if TYPE_CHECKING:
    from block_classes.materials import DepthMaterial
    from block_classes.environment_materials import EnvironmentMaterial


all_biomes: List[type]


class Biome(ABC):
    CLUSTER_LIKELYHOOD: float = 1 / 120
    # max distance of ores from the center of a cluster 49 max ores in a cluster
    MAX_CLUSTER_SIZE: int = 3
    # chance of a plant to occur when location is valid 10%
    FLORA_LIKELYHOOD = 0.1

    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian]
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]]
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]]
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]]
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]]

    distribution: util.TwoDimensionalGaussian

    def __init__(
        self,
        x_gaussian: util.Gaussian,
        y_gaussian: util.Gaussian,
        covariance1: float = 0.0,
        covariance2: float = 0.0,
    ):
        self.distribution = util.TwoDimensionalGaussian(x_gaussian, y_gaussian, covariance1, covariance2)

    def get_likelyhood_at_coord(self, x: int, y: int) -> float:
        """The likelyhood of the given coordinate being part of this biome"""
        return self.distribution.probability(x, y)

    @classmethod
    def get_likelyhood_at_depth(cls, depth: int) -> float:
        """Likelyhood of this biome occuring at exactly depth"""
        # make sure that the depth is expressed between 1 and 100
        norm_depth = depth / con.MAX_DEPTH * 100
        return cls.DEPTH_DISTRIBUTION.probability(norm_depth)  # noqa

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def DEPTH_DISTRIBUTION(self) -> util.Gaussian:
        """The likelyhood of this biome occuring at a given depth"""
        pass

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
    def FLORA_MATERIALS(self) -> List["EnvironmentMaterial"]:
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

        # calculate accumulated probabilities when relevant
        material_likelyhoods = {}
        for index, lh in enumerate(norm_likelyhoods):
            name = material_list[index].name()
            if name in material_likelyhoods:
                material_likelyhoods[name] += lh
            else:
                material_likelyhoods[name] = lh
        return material_likelyhoods


class NormalBiome(Biome):
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(50, 30)
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.StoneCollection(),
        ground_materials.Dirt,
        ground_materials.Granite,
        ground_materials.FinalStone
    ]
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.Iron,
        ground_materials.Gold,
        ground_materials.Copper,
        ground_materials.Coal,
        ground_materials.Titanium
    ]
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        environment_materials.Fern,
        environment_materials.Reed,
        environment_materials.Moss,
        environment_materials.ShroomCollection(),
        environment_materials.Vine
    ]
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.BackDirt,
        ground_materials.BackStone,
        ground_materials.BackFinalStone
    ]


class IceBiome(Biome):
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(10, 20)
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.DirtIceCollection(),
        ground_materials.StoneIceCollection(),
        ground_materials.GraniteIceCollection(),
        ground_materials.FinalIceCollection()
    ]
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.Iron,
        ground_materials.Gold,
        ground_materials.Zinc,
        ground_materials.Coal,
        ground_materials.Titanium
    ]
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        environment_materials.Icicle,
        environment_materials.SnowLayer
    ]
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.BackIce
    ]


class SlimeBiome(Biome):
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(60, 10)
    FILLER_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.DirtSlimeCollection(),
        ground_materials.StoneSlimeCollection(),
        ground_materials.GraniteSlimeCollection(),
        ground_materials.FinalSlimeCollection()
    ]
    ORE_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.Oralchium,
        ground_materials.Iron,
        ground_materials.Coal,
        ground_materials.Titanium
    ]
    FLORA_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        environment_materials.Vine,
        environment_materials.SlimeBush
    ]
    BACKGROUND_MATERIALS: ClassVar[List["DepthMaterial"]] = [
        ground_materials.BackSlime1,
        ground_materials.BackSlime2,
    ]


class BiomeGenerationDefinition(ABC):
    BIOME_PROBABILITIES: ClassVar[Dict[Type[Biome], float]]
    STRUCTURE_PROBABILITIES: ClassVar[Dict[Type[base_structures.Structure], float]]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def BIOME_PROBABILITIES(self) -> Dict[type, float]:
        """Dictionary linking biome to a gaussian expressing the frequency of the biome over the generation"""
        pass

    # noinspection PyPep8Naming
    @property
    def STRUCTURE_PROBABILITIES(self) -> Dict[type, float]:
        """Probabilities of structures for this map"""
        return {}

    @classmethod
    def get_biome(
        cls,
        depth: int
    ) -> Type[Biome]:
        """Calculate the likelyhood of a biome for a given depth based on the frequency of the biome overall and a
        likelyhood given the depth"""
        # noinspection PyUnresolvedReferences
        biome_lhs_at_depth = {biome: biome.get_likelyhood_at_depth(depth) * frequency
                              for biome, frequency in cls.BIOME_PROBABILITIES.items()}
        biome_type = choices(list(biome_lhs_at_depth.keys()), list(biome_lhs_at_depth.values()), k=1)[0]
        return biome_type

    @classmethod
    def get_structure(
        cls,
        depth: int
    ) -> Union[Type[base_structures.Structure], None]:
        # noinspection PyTypeChecker
        if len(cls.STRUCTURE_PROBABILITIES) > 0:
            # noinspection PyUnresolvedReferences
            structure_lhs_at_depth = {structure: structure.get_likelyhood_at_depth(depth) * frequency
                                      for structure, frequency in cls.STRUCTURE_PROBABILITIES.items()}
            # noinspection PyUnresolvedReferences
            return choices(list(structure_lhs_at_depth.keys()), list(structure_lhs_at_depth.values()), k=1)[0]
        return None


class NormalBiomeGeneration(BiomeGenerationDefinition):
    BIOME_PROBABILITIES: ClassVar[Dict[type, float]] = {
        NormalBiome: 0.80, IceBiome: 0.10, SlimeBiome: 0.10
    }
    STRUCTURE_PROBABILITIES: ClassVar[Dict[type, float]] = {
        abandoned_mine.AbandonedMineStructure: 1
    }
