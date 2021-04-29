from abc import ABC

import block_classes.materials.building_materials
import block_classes.materials.ground_materials as ground_materials
import recipes.base_recipes as base_recipes
import block_classes.materials.materials as base_materials
import utility.utilities as util


class BaseFactoryRecipe(ABC):
    pass


class FurnaceRecipe(base_recipes.BaseRecipe, BaseFactoryRecipe):
    CRAFTING_TIME = 1000

    def __init__(self):
        mat = block_classes.materials.building_materials.FurnaceMaterial
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(3, 3))

        row1 = [ground_materials.Stone, ground_materials.Stone, ground_materials.Stone]
        row2 = [ground_materials.Stone, ground_materials.Coal, ground_materials.Stone]

        grid.add_all_rows(row1, row2, row1)
        return grid


class CompactStoneRecipe(base_recipes.BaseRecipe, BaseFactoryRecipe):
    CRAFTING_TIME = 100

    def __init__(self):
        mat = block_classes.materials.building_materials.StoneBrickMaterial
        base_recipes.BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row = [ground_materials.Stone, ground_materials.Stone]
        grid.add_all_rows(row, row)
        return grid


class StonePipe(base_recipes.BaseRecipe, BaseFactoryRecipe):
    CRAFTING_TIME = 1000

    def __init__(self):
        mat = block_classes.materials.building_materials.StonePipeMaterial
        base_recipes.BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(3, 3))
        top = [ground_materials.Stone, ground_materials.Stone, ground_materials.Stone]
        middle = [base_materials.Air, base_materials.Air, base_materials.Air]
        grid.add_all_rows(top, middle, top)
        return grid
