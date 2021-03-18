from abc import ABC, abstractmethod

import block_classes.ground_materials as ground_materials
import recipes.base_recipes as base_recipes
import block_classes.materials as base_materials
import utility.utilities as util


class FurnaceRecipesInterface(ABC):

    @property
    @abstractmethod
    def FUEL_CONSUMPTION(self):
        return 0


class IronBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 5
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.IronIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Iron, ground_materials.Iron]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid


class ZincBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 2
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.ZincIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Zinc, ground_materials.Zinc]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid


class GoldBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 4
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.GoldIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Gold, ground_materials.Gold]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid


class CopperBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 3
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.CopperIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Copper, ground_materials.Copper]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid


class TitaniumBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 10
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.TitaniumIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Titanium, ground_materials.Titanium]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid


class OralchiumBarRecipe(base_recipes.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 10
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = ground_materials.OralchiumIngot
        base_recipes.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = base_recipes.RecipeGrid(util.Size(2, 2))

        row1 = [ground_materials.Oralchium, ground_materials.Oralchium]
        row2 = [base_materials.Air, base_materials.Air]

        grid.add_all_rows(row1, row2)
        return grid
