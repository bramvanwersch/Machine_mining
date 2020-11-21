
from abc import ABC, abstractmethod


#own classes
from entities import Worker, CameraCentre
from board.camera import CameraAwareLayeredUpdates
from board.board import Board
from utility.constants import *
from tasks import TaskControl
from utility.image_handling import load_images
from recipes.recipe_constants import create_recipe_book
from interfaces.building_interface import BuildingWindow
from interfaces.managers import create_window_managers
from block_classes.block_constants import configure_material_collections
import interfaces.managers as window_managers
from interfaces.interface_utility import screen_to_board_coordinate


class Main:

    def __init__(self):
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)

        self.screen = pygame.display.set_mode(SCREEN_SIZE, DOUBLEBUF)  # | FULLSCREEN)
        self.screen.set_alpha(None)

        pygame.display.set_caption("MINING!!")
        pygame.mouse.set_visible(True)

        # setup general information when loading a game
        # load all the images before running the game
        load_images()

        #load fuel materials
        configure_material_collections()

        #load all recipes
        create_recipe_book()

        # pre loaded scenes
        # TODO: remove the game as default, add it when selected from the menu
        self.scenes = {"game": Game(self.screen)}
        self.active_scene = "game"

        self.run()

    def run(self):
        # Main Loop
        while self.going:
            # make sure to reset the screen in a cheap way
            self.screen.fill((0,0,0))
            active_scene = self.scenes[self.active_scene]
            active_scene.update()
            pygame.display.update(active_scene.board_update_rectangles)
            GAME_TIME.tick(200)

        pygame.quit()

    @property
    def going(self):
        return any(s.going for s in self.scenes.values())


    # def draw_air_rectangles(self):
    #     for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
    #         for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
    #             self.board.add_rectangle(rect, (0,0,0), layer=1, border=2)
    #
    # def remove_air_rectangles(self):
    #     for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
    #         for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
    #             self.board.add_rectangle(rect, INVISIBLE_COLOR, layer=1, border=2)


class Scene(ABC):
    def __init__(self, screen, sprite_group):
        self.screen = screen
        self.board_update_rectangles = []
        self.sprite_group = sprite_group

        # signifies if the scene is still alive
        self.going = True

    def update(self):
        self.scene_updates()
        self.handle_events()
        self.sprite_group.update()
        self.draw()

    @abstractmethod
    def handle_events(self):
        pass

    def scene_updates(self):
        for sprite in self.sprite_group.sprites():
            self.sprite_group.change_layer(sprite, sprite._layer)

    def draw(self):
        self.sprite_group.draw(self.screen)

    def exit(self):
        pass

class Game(Scene):
    def __init__(self, screen):
        self.screen = screen
        self.rect = self.screen.get_rect()
        # camera center position is chnaged before starting the game
        self.camera_center = CameraCentre((0,0), (5,5))
        self.main_sprite_group = CameraAwareLayeredUpdates(self.camera_center, BOARD_SIZE)
        super().__init__(self.screen, self.main_sprite_group)

        #load a window manager to manage window events
        create_window_managers(self.camera_center)
        from interfaces.managers import game_window_manager

        self.window_manager = game_window_manager
        self.board = Board(self.main_sprite_group)

        # update rectangles
        self.__vision_rectangles = []
        self.board_update_rectangles = []
        self.__debug_rectangle = (0,0,0,0)

        self._visible_entities = 0

        #zoom variables
        self._zoom = 1.0

        #tasks
        self.tasks = TaskControl(self.board)
        self.board.set_task_control(self.tasks)

        #for some more elaborate setting up of variables
        self.building_interface = None
        self.__setup_start()

    def __setup_start(self):
        start_chunk = self.board.get_start_chunk()
        appropriate_location = (int(start_chunk.START_RECTANGLE.centerx / BLOCK_SIZE.width) * BLOCK_SIZE.width + start_chunk.rect.left,
            + start_chunk.START_RECTANGLE.bottom - BLOCK_SIZE.height + start_chunk.rect.top)
        for _ in range(5):
            Worker((appropriate_location), self.board, self.tasks, self.main_sprite_group)
        #add one of the imventories of the terminal
        self.building_interface = BuildingWindow(self.board.inventorie_blocks[0].inventory, self.main_sprite_group)

        self.camera_center.rect.center = start_chunk.rect.center

    def scene_updates(self):
        super().scene_updates()
        self.set_update_rectangles()
        self.load_unload_sprites()

        self.board.update_board()

    def draw(self):
        super().draw()
        self.draw_debug_info()

    def handle_events(self):
        events = pygame.event.get()
        cam_events = []
        leftover_events = []
        for event in events:
            if event.type == QUIT:
                self.going = False
            elif event.type == KEYDOWN and event.key in INTERFACE_KEYS:
                self.__handle_interface_selection_events(event)
                #allow these events to trigger after
                leftover_events.append(event)

            elif (event.type == KEYDOWN or event.type == KEYUP) and \
                    event.key in CAMERA_KEYS:
                cam_events.append(event)
            else:
                leftover_events.append(event)
        if cam_events:
            self.camera_center.handle_events(cam_events)
        if leftover_events:
            leftover_events = self.window_manager.handle_events(leftover_events)
            for event in leftover_events:
                if event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                    if event.button == 4:
                        self.__zoom_entities(0.1)
                    elif event.button == 5:
                        self.__zoom_entities(-0.1)
            self.board.handle_events(leftover_events)

    def set_update_rectangles(self):
        # get a number of rectangles that encompass the changed board state

        zoom = self._zoom

        relative_board_start = screen_to_board_coordinate((0, 0), self.main_sprite_group.target, zoom)

        # rectangles directly on the screen that need to be visually updated
        board_u_rects = [self.__debug_rectangle]

        # rectangles containing part or whole chunks that are visible due to vision
        vision_u_rects = []

        for row in self.board.chunk_matrix:
            for chunk in row:
                rect = chunk.layers[0].get_update_rect()
                if rect == None:
                    continue
                vision_u_rects.append(rect)

                adjusted_rect = pygame.Rect((round((rect[0] - relative_board_start[0]) * zoom),
                                             round((rect[1] - relative_board_start[1]) * zoom),
                                             round(rect.width * zoom), round(rect.height * zoom)))
                clipped_rect = adjusted_rect.clip(self.rect)
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    board_u_rects.append(clipped_rect)
        for window in self.window_manager.windows.values():
            rect = window.orig_rect
            if not window.static:
                board_u_rects.append(window.orig_rect)
            else:
                # TODO fix this kind of cheaty fix, right now the rectangle is made bigger to cover the full area, but
                #  this is a halfed as solution
                adjusted_rect = pygame.Rect((round((rect[0] - relative_board_start[0]) * zoom) - 5,
                                             round((rect[1] - relative_board_start[1]) * zoom) - 5,
                                             rect.width + 10, rect.height + 10))
                clipped_rect = adjusted_rect.clip(self.rect)
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    board_u_rects.append(clipped_rect)
            vision_u_rects.append(window.orig_rect)

        self.board_update_rectangles = board_u_rects
        self.__vision_rectangles = vision_u_rects

    def load_unload_sprites(self):
        c = self.main_sprite_group.target.rect.center
        if c[0] + SCREEN_SIZE.width / 2 - BOARD_SIZE.width > 0:
            x = 1 + (c[0] + SCREEN_SIZE.width / 2 - BOARD_SIZE.width) / (SCREEN_SIZE.width / 2)
        elif SCREEN_SIZE.width / 2 - c[0] > 0:
            x = 1 + (SCREEN_SIZE.width / 2 - c[0]) / (SCREEN_SIZE.width / 2)
        else:
            x = 1
        if c[1] + SCREEN_SIZE.height / 2 - BOARD_SIZE.height > 0:
            y = 1 + (c[1] + SCREEN_SIZE.height / 2 - BOARD_SIZE.height) / (SCREEN_SIZE.height / 2)
        elif SCREEN_SIZE.height / 2 - c[1] > 0:
            y = 1 + (SCREEN_SIZE.height / 2 - c[1]) / (SCREEN_SIZE.height / 2)
        else:
            y = 1
        visible_rect = pygame.Rect(0, 0, int(SCREEN_SIZE.width * x ), int(SCREEN_SIZE.height * y ))
        visible_rect.center = c

        self._visible_entities = 0
        for sprite in self.main_sprite_group.sprites():
            if not sprite.static or (sprite.rect.colliderect(visible_rect) and
                                     sprite.orig_rect.collidelist(self.__vision_rectangles) != -1):
                sprite.show(True)
                if sprite.is_showing:
                    self._visible_entities += 1
            else:
                sprite.show(False)

    def draw_debug_info(self):
        x_coord = 5
        line_distance = 12
        #is big enough
        width = 70

        y_coord = 5
        debug_topleft = (x_coord, y_coord)
        if FPS:
            fps = FONTS[18].render("fps: {}".format(int(GAME_TIME.get_fps())), True, pygame.Color('white'))
            self.screen.blit(fps, (x_coord, y_coord))
            y_coord += line_distance
        if ENTITY_NMBR:
            en = FONTS[18].render("e: {}/{}".format(self._visible_entities, len(self.main_sprite_group.sprites())),
                                   True, pygame.Color('white'))
            self.screen.blit(en, (x_coord, y_coord))
            y_coord += line_distance
        if ZOOM:
            z = FONTS[18].render("zoom: {}x".format(self._zoom), True, pygame.Color('white'))
            self.screen.blit(z, (x_coord, y_coord))
            y_coord += line_distance
        self.__debug_rectangle = (*debug_topleft, width, y_coord - debug_topleft[1])

#handeling of events
    def __handle_interface_selection_events(self, event):
        if event.key == BUILDING:
            self.window_manager.add(self.building_interface)

    def __zoom_entities(self, increase):
        """
        Zoom all the entities with a certain amount of increase

        :param increase: a small number signifying the increase
        """
        prev_zoom_level = self._zoom
        self._zoom = round(min(max(0.4, self._zoom + increase), 2), 1)
        #prevent unnecesairy recalculations
        if prev_zoom_level != self._zoom:
            for sprite in self.main_sprite_group.sprites():
                if sprite.zoomable:
                    sprite.zoom(self._zoom)
            BOARD_SIZE.width = self._zoom * ORIGINAL_BOARD_SIZE.width
            BOARD_SIZE.height = self._zoom * ORIGINAL_BOARD_SIZE.height


if __name__ == "__main__":
    Main()