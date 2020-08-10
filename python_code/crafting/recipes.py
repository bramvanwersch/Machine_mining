import sys, inspect
from abc import abstractmethod, ABC

from python_code.board import materials
from python_code.utility.utilities import Size
from python_code.board.buildings import *


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


class RecipeGrid:
    """
    A grid that each recipe has that tracks what a recipe looks like
    """
    def __init__(self, total_size, core_size):
        """
        :param total_size: a Size object that defines the maximum size of the
        recipe
        :param core_size: a Size object that is the minum size of a recipe
        """
        self.size = total_size
        self.core_size = core_size
        #grid that saves all materials
        self.material_grid = [[[materials.Air] for _ in range(self.size.width)] for _ in range(self.size.height)]

        #grid that saves all the groups of each material
        self.group_grid = [[[0] for _ in range(self.size.width)] for _ in range(self.size.height)]

        #saves the sizes of the graphs to allow for checking
        self.group_sizes = {}


    def check_complete_groups(self, g_size, col_i, row_i):
        """
        Check if a selection of the group grid only contains full groups.

        :param g_size: a Size object that is as big or smaller then the
        self.group_grid
        :param col_i: the starting column of the matrix
        :param row_i: the starting row of the matrix
        :return: a boolean that tells if that is the case or not.
        """
        group_counts = {}
        for row in self.group_grid[row_i:row_i + g_size.height]:
            for value in row[col_i:col_i + g_size.width]:
                if value in group_counts:
                    group_counts[value] += 1
                else:
                    group_counts[value] = 1
        for key in group_counts:
            if group_counts[key] != self.group_sizes[key]:
                return False
        return True

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
        Add a value to the material matrix and the group matrix aswell as a
        count for a certain group

        :param value: a RMat object
        :param column_i: the column to add the value to
        :param row_i: the row to add the value to
        """
        self.material_grid[row_i][column_i] = value
        self.group_grid[row_i][column_i] = value.group
        if value.group in self.group_sizes:
            self.group_sizes[value.group] += 1
        else:
            self.group_sizes[value.group] = 1

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


class RMat:
    """
    Recipe material class. This saves a material type that can be part of a
    recipe
    """
    def __init__(self, name, group):
        """
        :param name: String name of the material. Material should be defined in
        materials file
        :param group: the group the material should be in
        """
        self._material_type = getattr(materials, name)
        self.name = name
        #add the materials to groups that tell what group is required. Group 0
        #is always required
        self.group = group

    @property
    def required(self):
        """
        All materials in group 0 are required for the recipe
        :return: a Boolean
        """
        return self.group == 0

    def __getattr__(self, item):
        """
        Give all attributes of the material to the recipe material
        """
        return getattr(self._material_type, item)

    def __eq__(self, other):
        return self.name == other

    def __str__(self):
        return self.name


class CraftableRecipe:
    """
    Defines a crafting grid and items that can be used to create the item
    defined by a concept recipe
    """
    def __init__(self, material_grid, recipe):
        self.block_type = recipe.BLOCK_TYPE
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
        self.material = material
        self.quantity = 1

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe material_grid

        :return: a RecipeGrid object
        """
        return None

    @property
    @abstractmethod
    def BLOCK_TYPE(self):
        return None

    def get_size(self):
        """
        A copy of the total recipe size

        :return: a Size object
        """
        return self.__recipe_grid.size.copy()

    def get_core_size(self):
        """
        A copy of the core size

        :return: a Size object
        """
        return self.__recipe_grid.core_size.copy()

    def compare(self, material_grid):
        """
        Compare a grid of material types to the recipe. This goes in a couple
        of steps;

        :param material_grid: a matrix of material types that are in the
        crafting grid.
        :return: a boolean telling if the recipe (or valid part) matches the
        material_grid

        1. Check if the size of the material_grid is smaller then the total
        recipe and bigger then the core.
        2. Check if the first material from the material_grid is the same as a
        material from the recipe.
        3. Check if the groups are complete for a certain possible match. If not
        go back to step 2
        4. Check if the material_grid matches part of the recipe. If not go
        back to step 2
        """
        #make a basic check for the size
        r_size = self.__recipe_grid.size
        c_size = self.__recipe_grid.core_size
        g_size = Size(len(material_grid[0]), len(material_grid))

        #Step 1:
        if not (r_size.width >= g_size.width and c_size.width <= g_size.width and \
                r_size.height >= g_size.height and c_size.height <= g_size.height):
            return False
        for row_i, row in enumerate(self.__recipe_grid[:r_size.height - g_size.height + 1 ]):
            for col_i, material in enumerate(row[:r_size.width - g_size.width + 1]):

                #Step 2: check if the material material_grid can match the recipe here
                if issubclass(material_grid[0][0], material._material_type):
                    if not self.__recipe_grid.check_complete_groups(g_size, col_i, row_i):
                        continue
                    #now check if the submatrix can match with the material grid
                    sub_matching_matrix = [row[col_i:col_i + g_size.width] for row in self.__recipe_grid[row_i:row_i + g_size.height]]
                    if self.__check_complete_recipe(material_grid, sub_matching_matrix):
                        return True
        return False

    def __check_complete_recipe(self, matrix, recipe_matrix):
        """
        Check if the matrix matches the recipe_matrix, use subclasses to check
        if iron matches ore for instance

        :param matrix: a matrix of material types that are in the
        crafting grid.
        :param recipe_matrix: part of the recipe_grid that is the same size as
        matrix
        :return: a boolean
        """
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[0])):
                if not issubclass(matrix[row_i][col_i], recipe_matrix[row_i][col_i]._material_type):
                    return False
        return True


class FurnaceRecipe(BaseConceptRecipe):
    BLOCK_TYPE = Furnace
    def __init__(self):
        mat = FurnaceMaterial(image=Furnace((0,0)).full_image())
        BaseConceptRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(7, 7), Size(3, 3))

        top_row = [RMat("Stone", 5), RMat("Stone", 5), RMat("Stone", 3), RMat("Stone", 3), RMat("Stone", 3), RMat("Stone", 5), RMat("Stone", 5)]
        second_row = [RMat("Stone", 5), RMat("Ore", 5), RMat("Ore", 3), RMat("Ore", 3), RMat("Ore", 3), RMat("Ore", 5), RMat("Stone", 5)]
        third_row = [RMat("Stone", 2),RMat("Ore", 2),RMat("Stone", 0),RMat("Stone", 0),RMat("Stone", 0),RMat("Ore", 1),RMat("Stone", 1)]
        fourth_row = [RMat("Stone", 2), RMat("Ore", 2), RMat("Stone", 0), RMat("Coal", 0), RMat("Stone", 0), RMat("Ore", 1), RMat("Stone", 1)]
        fifth_row = [RMat("Stone", 2),RMat("Ore", 2),RMat("Stone", 0),RMat("Stone", 0),RMat("Stone", 0),RMat("Ore", 1),RMat("Stone", 1)]
        sixt_row = [RMat("Stone", 5), RMat("Ore", 5), RMat("Ore", 4), RMat("Ore", 4), RMat("Ore", 4), RMat("Ore", 5), RMat("Stone", 5)]
        last_row = [RMat("Stone", 5), RMat("Stone", 5), RMat("Stone", 4), RMat("Stone", 4), RMat("Stone", 4), RMat("Stone", 5), RMat("Stone", 5)]

        grid.add_all_rows(top_row, second_row, third_row, fourth_row,
                          fifth_row, sixt_row, last_row)
        return grid

class CompactStoneRecipe(BaseConceptRecipe):
    BLOCK_TYPE = Block
    def __init__(self):
        mat = StoneBrickMaterial()
        BaseConceptRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(2, 2), Size(2, 2))

        row = [RMat("Stone", 0), RMat("Stone", 0)]
        grid.add_all_rows(row, row)
        return grid

class StonePipe(BaseConceptRecipe):
    BLOCK_TYPE = Block
    def __init__(self):
        mat = StonePipeMaterial()
        BaseConceptRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = RecipeGrid(Size(3, 5), Size(3, 3))
        top = [RMat("Stone", 1), RMat("Stone", 1), RMat("Stone", 1)]
        row = [RMat("Stone", 0), RMat("Stone", 0), RMat("Stone", 0)]
        middle = [RMat("Air", 0), RMat("Air", 0), RMat("Air", 0)]
        grid.add_all_rows(top, row, middle, row, top)
        return grid