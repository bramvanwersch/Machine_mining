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

    def get_recipe(self, material_grid):
        for recipe in self.recipes:
            if recipe.compare(material_grid):
                print(recipe)


class RecipeGrid:
    def __init__(self, total_size, core_size):
        self.size = total_size
        self.core_size = core_size
        self.material_grid = [[[materials.Air] for _ in range(self.size.width)] for _ in range(self.size.height)]
        self.group_grid = [[[0] for _ in range(self.size.width)] for _ in range(self.size.height)]
        self.group_sizes = {}

    def check_complete_groups(self, g_size, col_i, row_i):
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
        for index, row in enumerate(values):
            self.add_row(row, index)

    def add_row(self, row, row_i):
        for column_i, value in enumerate(row):
            self.add_value(value, column_i, row_i)

    def add_value(self, value, column_i, row_i):
        self.material_grid[row_i][column_i] = value
        self.group_grid[row_i][column_i] = value.group
        if value.group in self.group_sizes:
            self.group_sizes[value.group] += 1
        else:
            self.group_sizes[value.group] = 1

    def __getitem__(self, item):
        return self.material_grid[item]

    def __len__(self):
        return len(self.material_grid)

    def print(self, attribute):
        for row in self.material_grid:
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
        return getattr(self._material_type, item)

    def __instancecheck__(self, instance):
        return isinstance(self._material_type, instance)

    def __str__(self):
        return self.name


class BaseRecipe:
    def __init__(self):
        self.__recipe_grid = self._create_recipe_grid()

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe material_grid
        :return: a RecipeGrid object
        """
        return None

    def get_size(self):
        return self.__recipe_grid.size.copy()

    def get_core_size(self):
        return self.__recipe_grid.core_size.copy()

    def compare(self, material_grid):
        #make a basic check for the size
        r_size = self.__recipe_grid.size
        c_size = self.__recipe_grid.core_size
        g_size = Size(len(material_grid[0]), len(material_grid))
        if not (r_size.width >= g_size.width and c_size.width <= g_size.width and \
                r_size.height >= g_size.height and c_size.height <= g_size.height):
            return False
        for row_i, row in enumerate(self.__recipe_grid[:r_size.height - g_size.height + 1 ]):
            for col_i, material in enumerate(row[:r_size.width - g_size.width + 1]):
                #check if the material material_grid can match the recipe here
                if issubclass(material_grid[0][0], material._material_type):
                    sub_matching_matrix = [row[col_i:col_i + g_size.width] for row in self.__recipe_grid[row_i:row_i + g_size.height]]
                    if not self.__recipe_grid.check_complete_groups(g_size, col_i, row_i):
                        continue
                    #now check if the submatrix can match with the material grid
                    if self.__compare_matrixes(material_grid, sub_matching_matrix):
                        return True
        return False

    def __compare_matrixes(self, matrix, recipe_matrix):
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[0])):
                if not issubclass(matrix[row_i][col_i], recipe_matrix[row_i][col_i]._material_type):
                    return False
        return True


class FurnaceRecipe(BaseRecipe):
    def __init__(self):
        BaseRecipe.__init__(self)

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
