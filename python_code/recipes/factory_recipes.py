from abc import ABC

import block_classes.building_materials
import block_classes.ground_materials
import recipes.base_recipes as br
from block_classes import materials
from utility.utilities import Size


class FactoryRecipeInterface(ABC):
    pass

class FurnaceRecipe(br.BaseRecipe, FactoryRecipeInterface):
    CRAFTING_TIME = 1000
    def __init__(self):
        mat = block_classes.building_materials.FurnaceMaterial
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(3, 3))

        row1 = [block_classes.ground_materials.Stone, block_classes.ground_materials.Stone, block_classes.ground_materials.Stone]
        row2 = [block_classes.ground_materials.Stone, block_classes.ground_materials.Coal, block_classes.ground_materials.Stone]

        grid.add_all_rows(row1, row2, row1)
        return grid

class CompactStoneRecipe(br.BaseRecipe, FactoryRecipeInterface):
    CRAFTING_TIME = 100
    def __init__(self):
        mat = block_classes.building_materials.StoneBrickMaterial
        br.BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row = [block_classes.ground_materials.Stone, block_classes.ground_materials.Stone]
        grid.add_all_rows(row, row)
        return grid

class StonePipe(br.BaseRecipe, FactoryRecipeInterface):
    CRAFTING_TIME = 1000
    def __init__(self):
        mat = block_classes.building_materials.StonePipeMaterial
        br.BaseRecipe.__init__(self, mat)
        self.quantity = 2

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(3, 3))
        top = [block_classes.ground_materials.Stone, block_classes.ground_materials.Stone, block_classes.ground_materials.Stone]
        middle = [materials.Air, materials.Air, materials.Air]
        grid.add_all_rows(top, middle, top)
        return grid