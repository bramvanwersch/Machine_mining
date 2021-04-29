from typing import ClassVar, List, Type, Union, Dict, Tuple

from utility import utilities as util, loot_pools
from block_classes import materials, block_utility as block_util, ground_materials
from board_generation.structures.base_structures import Structure, StructurePart


class IronSheetCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("IronSheetWall"): 0.8, block_util.MCD("RustedIronSheetWall"): 0.19, block_util.MCD("Air"): 0.01
    }


class VaultChestCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("StoneChestMaterial", needs_board_update=True,
                       block_kwargs={
                           "starting_items": loot_pools.ItemLootPool(50, {ground_materials.IronIngot: 0.2,
                                                                          ground_materials.GoldIngot: 0.1,
                                                                          ground_materials.ZincIngot: 0.4,
                                                                          ground_materials.CopperIngot: 0.25,
                                                                          ground_materials.TitaniumIngot: 0.05})
                       }): 0.5,
        block_util.MCD("Air"): 0.5
    }


class VaultStructure(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, VaultChestCollection, VaultChestCollection,
         VaultChestCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, VaultChestCollection, VaultChestCollection,
         VaultChestCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
        [IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection,
         IronSheetCollection, IronSheetCollection, IronSheetCollection, IronSheetCollection],
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [],
        [],
        []
    )


class ProtectedVaultStructure(Structure):
    STRUCTURE_START_PARTS: ClassVar[List["StructurePart"]] = [
        VaultStructure
    ]
    MAX_PARTS: ClassVar[int] = 1
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(90, 10)

    def _str_to_part_class(
        self,
        part_name: str
    ) -> Type["StructurePart"]:
        return globals()[part_name]