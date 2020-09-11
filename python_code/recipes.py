import sys, inspect
from abc import abstractmethod, ABC

from python_code.board import materials
from python_code.utility.utilities import Size
from python_code.board import buildings


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
            if issubclass(obj, BaseConceptRecipe) and obj != BaseConceptRecipe:
                #add an instance of the recipe
                recipes.append(obj())
        return recipes

    def get_recipe(self, material_grid):
        """
        Check if a certain grid of varaibles corresponds to a recipe.

        :param material_grid: a matrix containing material types for the
        materials presnet in the crafting grid
        :return: TBD
        """
        for recipe in self.recipes:
            if recipe.compare(material_grid):
                return CraftableRecipe(material_grid, recipe)
        return None

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


class CraftableRecipe:
    """
    Defines a crafting grid and items that can be used to create the item
    defined by a concept recipe
    """
    def __init__(self, material_grid, recipe):
        self.material = recipe.material
        self.quantity = recipe.quantity

        # saves the amount of the materials in the grid
        self.required_materials = self.__count_grid(material_grid)

    def __count_grid(self, grid):
        counts = {}
        for row in grid:
            for value in row:
                if value.name() != "Air":
                    if value.name() not in counts:
                        counts[value.name()] = 1
                    else:
                        counts[value.name()] += 1
        return counts


class BaseConceptRecipe(ABC):
    """
    Base class for all recipe concepts. It saves a recipe a grid that is a
    potential of all recipes that can be.
    """
    def __init__(self, material):
        self.__recipe_grid = self._create_recipe_grid()
        self._material = material
        self.quantity = 1

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe material_grid

        :return: a RecipeGrid object
        """
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


class FurnaceRecipe(BaseConceptRecipe):
    def __init__(self):
        mat = materials.FurnaceMaterial
        BaseConceptRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(3, 3))

        row1 = [materials.Stone, materials.Stone, materials.Stone]
        row2 = [materials.Stone, materials.Coal, materials.Stone]

        grid.add_all_rows(row1, row2, row1)
        return grid

class CompactStoneRecipe(BaseConceptRecipe):
    def __init__(self):
        mat = materials.StoneBrickMaterial
        BaseConceptRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(2, 2))

        row = [materials.Stone, materials.Stone]
        grid.add_all_rows(row, row)
        return grid

class StonePipe(BaseConceptRecipe):
    def __init__(self):
        mat = materials.StonePipeMaterial
        BaseConceptRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(3, 3))
        top = [materials.Stone, materials.Stone, materials.Stone]
        middle = [materials.Air, materials.Air, materials.Air]
        grid.add_all_rows(top, middle, top)
        return grid