import sys, inspect
from abc import abstractmethod, ABC

from python_code.board import materials
from python_code.utility.utilities import Size
from python_code.board import buildings
from python_code.inventories import Item


class RecipeBook:
    """
    Holds and loads all recipes as well as determines a possible recipe from a
    certain crafting configuration
    """
    def __init__(self):
        self.recipes = self.__initiate_recipes()

    def __initiate_recipes(self):
        """
        Innitiate all the recipes defined in this file based on subclassing
        from BaseRecipe
        :return: a list of all recipes
        """
        #filter out all the recipes.
        recipes = []
        for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if issubclass(obj, BaseRecipe) and obj != BaseRecipe:
                #add an instance of the recipe
                recipes.append(obj())
        return recipes

    def __iter__(self):
        return iter(self.recipes)


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
        self.needed_materials = self.__count_grid()
        self.quantity = 1

    def __count_grid(self):
        counts = {}
        for row in self.__recipe_grid:
            for value in row:
                if value.name() != "Air":
                    if value.name() not in counts:
                        counts[value.name()] = 1
                    else:
                        counts[value.name()] += 1
        items = [Item(getattr(materials, name)(), value) for name, value in counts.items()]
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
        if issubclass(self._material, materials.BuildingMaterial):
            return buildings.building_type_from_material(self._material).full_image()
        return self._material().surface

    def get_image_grid(self):
        image_grid = []
        for row in self.__recipe_grid:
            image_row = []
            for material_type in row:
                if issubclass(material_type, materials.BuildingMaterial):
                    image_row.append(buildings.building_type_from_material(material_type).full_image())
                else:
                    image_row.append(material_type().surface)
            image_grid.append(image_row)
        return image_grid


class FurnaceRecipe(BaseRecipe):
    CRAFTING_TIME = 1000
    def __init__(self):
        mat = materials.FurnaceMaterial
        BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(3, 3))

        row1 = [materials.Stone, materials.Stone, materials.Stone]
        row2 = [materials.Stone, materials.Coal, materials.Stone]

        grid.add_all_rows(row1, row2, row1)
        return grid

class CompactStoneRecipe(BaseRecipe):
    CRAFTING_TIME = 100
    def __init__(self):
        mat = materials.StoneBrickMaterial
        BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(2, 2))

        row = [materials.Stone, materials.Stone]
        grid.add_all_rows(row, row)
        return grid

class StonePipe(BaseRecipe):
    CRAFTING_TIME = 1000
    def __init__(self):
        mat = materials.StonePipeMaterial
        BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(3, 3))
        top = [materials.Stone, materials.Stone, materials.Stone]
        middle = [materials.Air, materials.Air, materials.Air]
        grid.add_all_rows(top, middle, top)
        return grid