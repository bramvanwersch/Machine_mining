import sys, inspect
from abc import ABC, abstractmethod

from python_code import materials
from python_code.utilities import Size


class RecipeBook:
    def __init__(self):
        self.recipes = self.__initiate_recipes()

    def __initiate_recipes(self):
        #filter out all the recipes.
        recipes = []
        for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if issubclass(obj, BaseRecipe) and obj != BaseRecipe:
                #add an instance of the recipe
                recipes.append(obj())
        return recipes

class RecipeGrid:
    def __init__(self, rows, columns):
        self.size = Size(columns, rows)
        self.grid = [[[None] for _ in range(columns)] for _ in range(rows)]

    def add_all_rows(self, *values):
        for index, row in enumerate(values):
            self.add_row(row, index)

    def add_row(self, value, row_i):
        self.grid[row_i] = value

    def add_value(self, value, column_i, row_i):
        self.grid[row_i][column_i] = value

    def __getitem__(self, item):
        return self.grid[item]

    def __len__(self):
        return len(self.grid)

    def print(self, attribute):
        for row in self.grid:
            attr_values = [getattr(value, attribute) for value in row]
            str_values = list(map(str, attr_values))
            value_format = "{:" + str(self.__longest_string(str_values) + 2) + "}"
            s = (value_format * self.size.width)
            str_row = s.format(*str_values)
            print(str_row)

    def __longest_string(self, strings):
        longest = 0
        for string in strings:
            if len(string) > longest:
                longest = len(string)
        return longest


class RMat:
    def __init__(self, name, group):
        self._material_type = getattr(materials, name)
        self.name = name
        #add the materials to groups that tell what group is required. Group 0
        #is always required
        self.group = group

    @property
    def required(self):
        return self.group == 0

    def __getattr__(self, item):
        return getattr(self.__material, item)


class BaseRecipe:
    def __init__(self):
        self.recipe_grid = self._create_recipe_grid()

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe grid
        :return: a RecipeGrid object
        """
        return None

    def size(self):
        return Size(len(self.recipe_grid[0]),len(self.recipe_grid))


class FurnaceRecipe(BaseRecipe):
    def __init__(self):
        BaseRecipe.__init__(self)

    def _create_recipe_grid(self):
        grid = RecipeGrid(7,7)

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
