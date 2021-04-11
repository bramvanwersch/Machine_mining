from typing import List, ClassVar, Dict, Union, Tuple

from board_generation.structures.base_structures import StructurePart, Structure
from block_classes import materials


class StoneBrickCollection(materials.MaterialCollection):
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]] = {
        "StoneBrickMaterial": 0.2, "MossBrickMaterial": 0.4, "ManyMossBrickMaterial": 0.4
    }


class HorizontalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection],
        ["Air", "Air", "Air", "Air"],
        ["Air", "Air", "Air", "Air"],
        [StoneBrickCollection, StoneBrickCollection, StoneBrickCollection, StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [],
        [("HorizontalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerSouthWestMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0)],
        [],
        [("HorizontalMinePart", 0), ("CornerNorthEastMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastWest", 0), ("JunctionNorthEastSouth", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0)]
    )


class VerticalMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0), ("CornerSouthWestMinePart", 0), ("CornerSouthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionEastSouthWest", 0),
         ("JunctionNorthEastSouthWest", 0)],
        [],
        [("VerticalMinePart", 0), ("CornerNorthWestMinePart", 0), ("CornerNorthEastMinePart", 0),
         ("JunctionNorthEastSouth", 0), ("JunctionNorthSouthWest", 0), ("JunctionNorthEastWest", 0),
         ("JunctionNorthEastSouthWest", 0)
         ],
        []
    )


class CornerNorthWestMinePart(StructurePart):
    FORM_DEFINITION: ClassVar[List[List[Union[materials.MaterialCollection, str]]]] = [
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", StoneBrickCollection],
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
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", "Air"],
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
        ["Air", "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
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
        [StoneBrickCollection, "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
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
        ["Air", "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
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
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
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
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", "Air"],
        ["Air", "Air", "Air", "Air"],
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
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", StoneBrickCollection],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
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
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection],
        ["Air", "Air", "Air", "Air"],
        ["Air", "Air", "Air", "Air"],
        [StoneBrickCollection, "Air", "Air", StoneBrickCollection]
    ]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]] = (
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)],
        [("VerticalMinePart", 0)],
        [("HorizontalMinePart", 0)]
    )


class AbandonedMineStructure(Structure):
    STRUCTURE_START_PARTS: ClassVar[List["StructurePart"]] = [
        HorizontalMinePart,
        VerticalMinePart,
        CornerNorthWestMinePart
    ]
    MAX_PARTS: ClassVar[int] = 100

    def _str_to_part_class(self, part_name):
        return globals()[part_name]




