from abc import abstractmethod, ABC
from typing import Union, List, Tuple, Type, TYPE_CHECKING

import block_classes.materials as base_materials
import utility.utilities as util
from utility import inventories
if TYPE_CHECKING:
    import pygame


class RecipeGrid:
    """A grid that each recipe has that tracks what a recipe looks like"""
    size: Union[util.Size, Tuple[int, int], List[int]]
    material_grid: List[List[Type[base_materials.BaseMaterial]]]

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]]
    ):
        self.size = size
        self.material_grid = [[base_materials.Air for _ in range(self.size.width)] for _ in range(self.size.height)]

    def add_all_rows(
        self,
        *rows: List[Type[base_materials.BaseMaterial]]
    ):
        """Add all rows of the matrix at once"""
        for index, row in enumerate(rows):
            self.add_row(row, index)

    def add_row(
        self,
        row: List[Type[base_materials.BaseMaterial]],
        row_i: int
    ):
        """Add a row at a time"""
        for column_i, value in enumerate(row):
            self.add_value(value, column_i, row_i)

    def add_value(
        self,
        value: Type[base_materials.BaseMaterial],
        column_i: int,
        row_i: int
    ):
        """Add a value to the material matrix"""
        self.material_grid[row_i][column_i] = value

    def __getitem__(
        self,
        item: int
    ) -> List[Type[base_materials.BaseMaterial]]:
        """Get a material from the grid"""
        return self.material_grid[item]

    def __len__(self) -> int:
        return len(self.material_grid)


class BaseRecipe(ABC):
    """Base class for all recipe concepts. It saves a recipe a grid that is a potential of all recipes that can be."""

    __recipe_grid: RecipeGrid
    material: Type[base_materials.BaseMaterial]
    needed_items: List[inventories.Item]
    quantity: int

    def __init__(self, material):
        self.__recipe_grid = self._create_recipe_grid()
        self.material = material  # the resulting material
        # list of item objects
        self.needed_items = self.__count_grid()
        self.quantity = 1  # the amount of items resulting from making this recipe

    def __count_grid(self) -> List[inventories.Item]:
        """Count the items needed for this recipe"""
        counts = {}
        for row in self.__recipe_grid:
            for obj in row:
                if obj != base_materials.Air:
                    if obj not in counts:
                        counts[obj] = 1
                    else:
                        counts[obj] += 1
        items = [inventories.Item(obj(), value) for obj, value in counts.items()]
        return items

    @abstractmethod
    def _create_recipe_grid(self) -> RecipeGrid:
        """Method to define a recipe material_grid"""
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CRAFTING_TIME(self) -> float:
        pass

    def get_image(self) -> "pygame.Surface":
        return self.material().full_surface

    def get_tooltip_text(self) -> str:
        tooltip_str = f"{self.material.name()}\nRequires:\n"
        for item in self.needed_items:
            tooltip_str += f" -{item.name()}: {item.quantity}\n"
        return tooltip_str[:-1]

    def get_image_grid(self) -> List[List[List[Union[str, "pygame.Surface"]]]]:
        image_grid = []
        for row in self.__recipe_grid:
            image_row = []
            for material_type in row:
                image_row.append([material_type.name(), material_type().full_surface])
            image_grid.append(image_row)
        return image_grid


class CancelRecipe(BaseRecipe):
    """Recipe for when recetting the crafting grid into a blank format"""
    CRAFTING_TIME: int = 0
    FUEL_CONSUMPTION: int = 0

    def __init__(self):
        mat = base_materials.CancelMaterial
        super().__init__(mat)
        self.quantity = 0
        self.needed_items = [inventories.Item(self.material(), 20)]

    def _create_recipe_grid(self) -> RecipeGrid:
        return RecipeGrid(util.Size(0, 0))
