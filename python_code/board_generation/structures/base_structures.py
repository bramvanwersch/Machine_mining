from abc import ABC, abstractmethod
from typing import Dict, Any, ClassVar, Union, List, TYPE_CHECKING, Tuple, Type
from random import randint, choice
import pygame

import utility.utilities as util

if TYPE_CHECKING:
    from block_classes import materials


class Structure(ABC):
    STRUCTURE_START_PARTS: ClassVar[List["StructurePart"]]
    MAX_PARTS: ClassVar[int]

    def __init__(self):
        self.__total_parts = max(1, randint(int(self.MAX_PARTS * 0.66), self.MAX_PARTS))

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def STRUCTURE_START_PARTS(self) -> List[Type["StructurePart"]]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MAX_PARTS(self) -> int:
        pass

    def get_structure_matrix(self):
        start_class = choice(self.STRUCTURE_START_PARTS)
        start_instance = start_class((0, 0))
        extend_parts = {start_instance}
        rectangles = [start_instance.rect]
        all_parts = {start_instance}
        count = 0
        while count <= self.__total_parts and len(extend_parts) != 0:
            for part in extend_parts.copy():
                for index, connection_options in enumerate(part.CONNECTION_DIRECIONS):
                    if len(connection_options) == 0: #or part.connections[index] is not None:
                        continue
                    str_part, start_index = choice(connection_options)
                    part_class = self._str_to_part_class(str_part)
                    if index == 0:
                        pos = (start_index + part.rect.left, part.rect.top - part_class.size().height)
                    elif index == 1:
                        pos = (part.rect.right, start_index + part.rect.top)
                    elif index == 2:
                        pos = (start_index + part.rect.left, part.rect.bottom)
                    else:
                        pos = (part.rect.left - part_class.size().width, start_index + part.rect.top)
                    part_instance = part_class(pos)
                    if part_instance.rect.collidelist(rectangles) != -1:
                        count += 1
                        continue
                    extend_parts.add(part_instance)
                    all_parts.add(part_instance)
                    rectangles.append(part_instance.rect)
                    count += 1
                extend_parts.remove(part)
        full_rect = self.union_rect(rectangles)
        full_material_matrix = [[None for _ in range(full_rect.width)] for _ in range(full_rect.height)]
        for part in all_parts:
            matrix_coord = [part.rect.left - full_rect.left, part.rect.top - full_rect.top]
            material_matrix = part.get_material_matrix()
            for row in material_matrix:
                for material in row:
                    full_material_matrix[matrix_coord[1]][matrix_coord[0]] = material
                    matrix_coord[0] += 1
                matrix_coord[1] += 1
                matrix_coord[0] -= len(row)
        return full_material_matrix

    def union_rect(self, rectangles: List[pygame.Rect]):
        corner_coords: List[Union[None, int]] = [None for _ in range(4)]
        for rect in rectangles:
            if corner_coords[0] is None or rect.left < corner_coords[0]:
                corner_coords[0] = rect.left
            if corner_coords[1] is None or rect.top < corner_coords[1]:
                corner_coords[1] = rect.top
            if corner_coords[2] is None or rect.right > corner_coords[2]:
                corner_coords[2] = rect.right
            if corner_coords[3] is None or rect.bottom > corner_coords[3]:
                corner_coords[3] = rect.bottom
        return pygame.Rect((corner_coords[0], corner_coords[1], corner_coords[2] - corner_coords[0],
                            corner_coords[3] - corner_coords[1]))

    @abstractmethod
    def _str_to_part_class(self, part_name) -> Type["StructurePart"]:
        # return globals()[part_name]
        pass


class StructurePart(ABC):

    FORM_DEFINITION: ClassVar[List[List[Union["materials.MaterialCollection", str]]]]
    CONNECTION_DIRECIONS: ClassVar[Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                         List[Tuple[str, int]], List[Tuple[str, int]]]]

    def __init__(self, pos: Union[Tuple[int, int], List[int]]):
        self.connections = [None for _ in range(4)]
        self.rect = pygame.Rect((pos[0], pos[1], len(self.FORM_DEFINITION[0]), len(self.FORM_DEFINITION)))

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def FORM_DEFINITION(self) -> List[List[Union["materials.MaterialCollection", str]]]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CONNECTION_DIRECIONS(self) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]],
                                            List[Tuple[str, int]], List[Tuple[str, int]]]:
        """Define connections in the form:

        First tuple for the 4 directions containing lists with tuples of Structure names with a number that is the
        starting block direction
        """
        pass

    def get_material_matrix(self) -> List[List[str]]:
        final_matrix = []
        for row in self.FORM_DEFINITION:
            matrix_row = []
            for value in row:
                if isinstance(value, str):
                    matrix_row.append(value)
                else:
                    matrix_row.append(value.name())
            final_matrix.append(matrix_row)
        return final_matrix

    @classmethod
    def size(cls) -> util.Size:
        return util.Size(len(cls.FORM_DEFINITION[0]), len(cls.FORM_DEFINITION))
