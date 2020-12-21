#!/usr/bin/python3

# library imports
import pygame
import os

# own imports
import utility.constants as con
import utility.image_handling as image_handlers
import recipes.recipe_utility as recipe_constants
import block_classes.block_utility as block_util
import scenes


class Main:
    screen: pygame.Surface

    def __init__(self):
        # configure the display
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)

        self.screen = pygame.display.set_mode(con.SCREEN_SIZE, con.DOUBLEBUF)  # | FULLSCREEN)
        self.screen.set_alpha(None)

        pygame.display.set_caption("MINING!!")
        pygame.mouse.set_visible(True)

        self.__innitialize_game_varaibles()
        self.run()

    def __innitialize_game_varaibles(self):
        # load images
        image_handlers.load_images()

        # load fuel materials
        block_util.configure_material_collections()

        # load all recipes
        recipe_constants.create_recipe_book()

        # pre loaded scenes
        scenes.scenes[scenes.MainMenu.name()] = scenes.MainMenu(self.screen)
        scenes.scenes.set_active_scene(scenes.MainMenu.name())

    def run(self):
        # Main Loop
        while scenes.scenes.is_scene_alive():
            self.screen.fill((0, 0, 0))
            active_scene = scenes.scenes.active_scene
            active_scene.update()
            if con.NO_LIGHTING:
                pygame.display.flip()
            else:
                pygame.display.update(active_scene.board_update_rectangles)
            con.GAME_TIME.tick(200)

        pygame.quit()

    # def draw_air_rectangles(self):
    #     for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
    #         for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
    #             self.board.add_rectangle(rect, (0,0,0), layer=1, border=2)
    #
    # def remove_air_rectangles(self):
    #     for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
    #         for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
    #             self.board.add_rectangle(rect, INVISIBLE_COLOR, layer=1, border=2)


if __name__ == "__main__":
    Main()
