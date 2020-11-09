from abc import abstractmethod, ABC

import block_classes.building_materials
from block_classes import materials
from block_classes import flora_materials
from block_classes import ground_materials
from utility.utilities import Size
from board import buildings
from inventories import Item


class RecipeGrid:
    """
    A grid that each recipe has that tracks what a recipe looks like
    """
    def __init__(self, size):
        """
        :param total_size: a Size object that defines the maximum size of the
        recipe
        :param core_size: a Size object that is the minum size of a recipe
        """
        self.size = size
        #grid that saves all materials
        self.material_grid = [[[materials.Air] for _ in range(self.size.width)] for _ in range(self.size.height)]

    def add_all_rows(self, *values):
        """
        Add all rows of the matrix at once

        :param values: a list of rows
        """
        for index, row in enumerate(values):
            self.add_row(row, index)

    def add_row(self, row, row_i):
        """
        Add a row at a time

        :param row: the row to add.
        :param row_i: the index where to insert the row
        """
        for column_i, value in enumerate(row):
            self.add_value(value, column_i, row_i)

    def add_value(self, value, column_i, row_i):
        """
        Add a value to the material matrix

        :param value: a RMat object
        :param column_i: the column to add the value to
        :param row_i: the row to add the value to
        """
        self.material_grid[row_i][column_i] = value

    def __getitem__(self, item):
        """
        Get a material from the grid

        :param item: index of row
        :return: the item at the index
        """
        return self.material_grid[item]

    def __len__(self):
        return len(self.material_grid)

    def print(self, attribute):
        """
        For printing a recipe and getting an idea of correctness

        :param attribute: the attribute of the material to show
        """
        for row in self.material_grid:
            attr_values = [getattr(value, attribute) for value in row]
            str_values = list(map(str, attr_values))
            value_format = "{:" + str(self.__longest_string(str_values) + 2) + "}"
            s = (value_format * self.size.width)
            str_row = s.format(*str_values)
            print(str_row)

    def __longest_string(self, strings):
        """
        Longest string in a list of strings

        :param strings: a list of strings
        :return: the lenght of the longest string
        """
        longest = 0
        for string in strings:
            if len(string) > longest:
                longest = len(string)
        return longest


class BaseRecipe(ABC):
    """
    Base class for all recipe concepts. It saves a recipe a grid that is a
    potential of all recipes that can be.
    """
    def __init__(self, material):
        self.__recipe_grid = self._create_recipe_grid()
        self._material = material
        # list of item objects
        self.needed_items = self.__count_grid()
        self.quantity = 1

    def __count_grid(self):
        counts = {}
        for row in self.__recipe_grid:
            for obj in row:
                if obj != materials.Air:
                    if obj not in counts:
                        counts[obj] = 1
                    else:
                        counts[obj] += 1
        items = [Item(obj(), value) for name, value in counts.items()]
        return items

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe material_grid

        :return: a RecipeGrid object
        """
        return None

    @property
    @abstractmethod
    def CRAFTING_TIME(self):
        return None

    def get_image(self):
        if issubclass(self._material, block_classes.building_materials.BuildingMaterial):
            return buildings.building_type_from_material(self._material).full_image()
        return self._material().surface

    def get_image_grid(self):
        image_grid = []
        for row in self.__recipe_grid:
            image_row = []
            for material_type in row:
                if issubclass(material_type, block_classes.building_materials.BuildingMaterial):
                    mat_type = buildings.building_type_from_material(material_type)
                    image_row.append([mat_type.name(), mat_type.full_image()])
                else:
                    image_row.append([material_type.name(), material_type().surface])
            image_grid.append(image_row)
        return image_grid

class CancelRecipe(BaseRecipe):
    CRAFTING_TIME = 0
    FUEL_CONSUMPTION = 0

    def __init__(self):
        mat = materials.CancelMaterial
        super().__init__(mat)
        self.quantity = 0
        self.needed_items = [Item(self._material, 20)]

    def _create_recipe_grid(self):
        return RecipeGrid(Size(0,0))
