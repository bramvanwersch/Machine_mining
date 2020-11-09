from abc import ABC, abstractmethod

import block_classes.ground_materials
import recipes.base_recipes as br
from block_classes import materials
from utility.utilities import Size


class FurnaceRecipesInterface(ABC):

    @property
    @abstractmethod
    def FUEL_CONSUMPTION(self):
        return 0


class IronBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 5
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = block_classes.ground_materials.IronIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [block_classes.ground_materials.Iron, block_classes.ground_materials.Iron]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid

class ZincBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 2
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = block_classes.ground_materials.ZincIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [block_classes.ground_materials.Zinc, block_classes.ground_materials.Zinc]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid

class GoldBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 4
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = block_classes.ground_materials.GoldIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [block_classes.ground_materials.Gold, block_classes.ground_materials.Gold]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid

class CopperBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 3
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = block_classes.ground_materials.CopperIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [block_classes.ground_materials.Copper, block_classes.ground_materials.Copper]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid

class TitaniumBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 10
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = block_classes.ground_materials.TitaniumIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [block_classes.ground_materials.Titanium, block_classes.ground_materials.Titanium]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid