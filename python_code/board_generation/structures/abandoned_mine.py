from typing import List, ClassVar, Dict, Union, Tuple, Type

from board_generation.structures.base_structures import StructurePart, Structure
from block_classes import materials
import utility.utilities as util


class StoneBrickCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]] = {
        "StoneBrickMaterial": 0.39, "MossBrickMaterial": 0.3, "ManyMossBrickMaterial": 0.3, "Air": 0.01
    }


class HorizontalBeltCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]] = {
        "Air": 0.9, "BasicConveyorBelt:image_key=1_1": 0.1
    }


class VerticalBeltCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]] = {
        "Air": 0.9, "BasicConveyorBelt:image_key=1_0": 0.1
    }


class HorizontalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        ["Air", "Air", "Air", "Air"],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [("HorizontalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerSouthWestMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("FurnaceRoom", 0)],
        [],
        [("HorizontalMinePart", 0), ("CornerNorthEastMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthEastSouth", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("FurnaceRoom", 0)]
    )


class VerticalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0), ("CornerSouthWestMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("FurnaceRoom", 0)],
        [],
        [("VerticalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerNorthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionNorthEastWest", 0),
         ("JunctionNorthEastSouthWest", 0), ("FurnaceRoom", 0)],
        []
    )


class CornerNorthWestMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        ["Air", "Air", VerticalBeltCollection, StoneBrickCollection],
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
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air"],
        [StoneBrickCollection, "Air", HorizontalBeltCollection, HorizontalBeltCollection],
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
        ["Air", "Air", "Air", StoneBrickCollection],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
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
        [StoneBrickCollection, "Air", "Air", "Air"],
        [StoneBrickCollection, VerticalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
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
        ["Air", "Air", "Air", "Air"],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
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
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air"],
        [StoneBrickCollection, "Air", VerticalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
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
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        ["Air", "Air", VerticalBeltCollection, "Air"],
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
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        ["Air", "Air", VerticalBeltCollection, StoneBrickCollection],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
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
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection],
        ["Air", "Air", VerticalBeltCollection, "Air"],
        [HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class FurnaceRoom(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection, StoneBrickCollection,
         StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, "Air",
         VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air",
         "Air", VerticalBeltCollection, StoneBrickCollection],
        ["Air", "Air", VerticalBeltCollection, "Air", "Air", "Air", "Air", "Air", "Air", "Air", VerticalBeltCollection,
         "Air"],
        [HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, HorizontalBeltCollection,
         HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection, HorizontalBeltCollection,
         HorizontalBeltCollection, HorizontalBeltCollection, VerticalBeltCollection, HorizontalBeltCollection],
        [StoneBrickCollection, "Air", VerticalBeltCollection, StoneBrickCollection, StoneBrickCollection,
         StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, "Air",
         VerticalBeltCollection, StoneBrickCollection],
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
        FurnaceRoom
    ]
    MAX_PARTS: ClassVar[int] = 100
    DEPTH_DISTRIBUTION: ClassVar[util.Gaussian] = util.Gaussian(10, 10)

    def _str_to_part_class(
        self,
        part_name: str
    ) -> Type["StructurePart"]:
        return globals()[part_name]
