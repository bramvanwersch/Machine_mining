from typing import List, ClassVar, Dict, Any, Union, Tuple
from random import choice
import pygame

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
        [("HorizontalMinePart", 0), ("CornerNortWestMinePart", 0)],
        [],
        [("HorizontalMinePart", 0)]
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
        [("VerticalMinePart", 0)],
        [],
        [("VerticalMinePart", 0), ("CornerNortWestMinePart", 0)],
        []
    )


class CornerNortWestMinePart(StructurePart):
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


class AbandonedMineStructure(Structure):
    STRUCTURE_PARTS: ClassVar[List["StructurePart"]] = [
        HorizontalMinePart,
        VerticalMinePart,
        CornerNortWestMinePart
    ]
    MAX_PARTS: ClassVar[int] = 25

    def _str_to_part_class(self, part_name):
        return globals()[part_name]




