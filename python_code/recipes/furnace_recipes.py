from abc import ABC, abstractmethod

import python_code.recipes.base_recipes as br
from python_code.board import materials
from python_code.utility.utilities import Size


class FurnaceRecipesInterface(ABC):

    @property
    @abstractmethod
    def FUEL_CONSUMPTION(self):
        return 0


class IronBarRecipe(br.BaseRecipe, FurnaceRecipesInterface):
    FUEL_CONSUMPTION = 5
    CRAFTING_TIME = 3000

    def __init__(self):
        mat = materials.IronIngot
        br.BaseRecipe.__init__(self, mat)

    def _create_recipe_grid(self):
        grid = br.RecipeGrid(Size(2, 2))

        row1 = [materials.Iron, materials.Iron]
        row2 = [materials.Air, materials.Air]

        grid.add_all_rows(row1, row2)
        return grid