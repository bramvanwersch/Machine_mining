import inspect

import recipes.factory_recipes as factory_recipes
import recipes.furnace_recipes as furnace_recipes
import recipes.base_recipes as base_recipes

recipe_books = {}


def create_recipe_book():
    global recipe_books
    recipe_books = {"factory": RecipeBook(factory_recipes), "furnace": RecipeBook(furnace_recipes)}


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
        recipes = [base_recipes.CancelRecipe()]
        for name, obj in inspect.getmembers(recipe_module, inspect.isclass):
            if issubclass(obj, base_recipes.BaseRecipe):
                recipes.append(obj())

        return recipes

    def __iter__(self):
        return iter(self.recipes)
