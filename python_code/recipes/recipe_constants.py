import sys, inspect

import recipes.factory_recipes as factory_r
import recipes.furnace_recipes as furnace_r
from recipes.base_recipes import CancelRecipe, BaseRecipe

recipe_books = {}

def create_recipe_book():
    global recipe_books
    recipe_books = {"factory": RecipeBook(factory_r), "furnace": RecipeBook(furnace_r)}


class RecipeBook:

    def __init__(self, recipe_module):
        self.recipes = self.__initiate_recipes(recipe_module)

    def __initiate_recipes(self, recipe_module):
        """
        Innitiate all the recipes defined in this file based on subclassing
        from BaseRecipe
        :return: a list of all recipes
        """
        #filter out all the recipes.
        recipes = [CancelRecipe()]
        for name, obj in inspect.getmembers(recipe_module, inspect.isclass):
            if issubclass(obj, BaseRecipe):
                recipes.append(obj())

        return recipes

    def __iter__(self):
        return iter(self.recipes)
