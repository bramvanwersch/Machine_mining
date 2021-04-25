from typing import List, ClassVar, Dict, Union, Tuple, Type

from board_generation.structures.base_structures import StructurePart, Structure
from block_classes import materials, ground_materials
import block_classes.block_utility as block_util
from utility import utilities as util, loot_pools


class StoneBrickCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("StoneBrickMaterial"): 0.39, block_util.MCD("MossBrickMaterial"): 0.3,
        block_util.MCD("ManyMossBrickMaterial"): 0.3, block_util.MCD("Air"): 0.01
    }


class HorizontalBeltCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("Air"): 0.9, block_util.MCD("BasicConveyorBelt", needs_board_update=True, image_key="1_1",
                                                   direction=1): 0.1
    }


class VerticalBeltCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("Air"): 0.9, block_util.MCD("BasicConveyorBelt", needs_board_update=True, image_key="1_0"): 0.1
    }


class MachineCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("FurnaceMaterial", needs_board_update=True): 0.3,
        block_util.MCD("FactoryMaterial", needs_board_update=True): 0.3,
        block_util.MCD("Air"): 0.4
    }


class ChestCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[block_util.MCD, float]] = {
        block_util.MCD("StoneChestMaterial", needs_board_update=True,
                       block_kwargs={
                           "starting_items": loot_pools.ItemLootPool(5, {ground_materials.IronIngot: 0.2,
                                                                         ground_materials.GoldIngot: 0.1,
                                                                         ground_materials.ZincIngot: 0.4,
                                                                         ground_materials.CopperIngot: 0.25,
                                                                         ground_materials.TitaniumIngot: 0.05})
                       }): 0.5,
        block_util.MCD("Air"): 0.5
    }


class HorizontalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air")],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [("HorizontalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerSouthWestMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("MachineRoom", 0)],
        [],
        [("HorizontalMinePart", 0), ("CornerNorthEastMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthEastSouth", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("MachineRoom", 0)]
    )


class VerticalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0), ("CornerSouthWestMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("MachineRoom", 0)],
        [],
        [("VerticalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerNorthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionNorthEastWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("MachineRoom", 0)],
        []
    )


class CornerNorthWestMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [],
        [],
        [("HorizontalMinePart", 0)]
    )


class CornerNorthEastMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air")],
        [StoneBrickCollection, block_util.MCD("Air"), HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [],
        []
    )


class CornerSouthWestMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), StoneBrickCollection],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class CornerSouthEastMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air")],
        [StoneBrickCollection, block_util.MCD("Air"), HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        []
    )


class JunctionEastSouthWest(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air")],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class JunctionNorthEastSouth(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air")],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        []
    )


class JunctionNorthEastWest(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air")],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [],
        [("HorizontalMinePart", 0)]
    )


class JunctionNorthSouthWest(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class JunctionNorthEastSouthWest(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air")],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class MachineRoom(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection,
         StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection,
         block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), HorizontalBeltCollection, MachineCollection,
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         ChestCollection, ChestCollection, HorizontalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection,
         StoneBrickCollection, block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         StoneBrickCollection, StoneBrickCollection, VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
        [block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"), block_util.MCD("Air"),
         block_util.MCD("Air"), block_util.MCD("Air"), VerticalBeltCollection, block_util.MCD("Air")],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, HorizontalBeltCollection,
         HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection,
         HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection,
         StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection,
         block_util.MCD("Air"), VerticalBeltCollection, StoneBrickCollection],
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 8)],
        [("HorizontalMinePart", 0), ("HorizontalMinePart", 8)],
        [("VerticalMinePart", 8)],
        [("HorizontalMinePart", 0), ("HorizontalMinePart", 8)],
    )


class AbandonedMineStructure(Structure):
    STRUCTURE_START_PARTS: ClassVar[List["StructurePart"]] = [
        MachineRoom
    ]
    MAX_PARTS: ClassVar[int] = 100
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(10, 10)

    def _str_to_part_class(
        self,
        part_name: str
    ) -> Type["StructurePart"]:
        return globals()[part_name]
