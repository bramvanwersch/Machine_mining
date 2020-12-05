
import warnings

# own classes
import board.board
from board.chunks import BoardImage
import utility.utilities as utilities
from entities import Worker, CameraCentre
from board.sprite_groups import *
from tasks import TaskControl
from utility.image_handling import load_images
from recipes.recipe_constants import create_recipe_book
import interfaces.small_interfaces as small_interfaces
from interfaces.managers import create_window_managers
from block_classes.block_utility import configure_material_collections
from interfaces.interface_utility import ThreadPoolExecutorStackTraced
from interfaces.widgets import *


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

        # load the scenes
        utilities.create_scene_manager()

        # pre loaded scenes
        utilities.scenes[MainMenu.name()] = MainMenu(self.screen)
        utilities.scenes.set_active_scene(MainMenu.name())

        self.run()

    def run(self):
        # Main Loop
        while utilities.scenes.is_scene_alive():
            self.screen.fill((0, 0, 0))
            active_scene = utilities.scenes.active_scene
            active_scene.update()
            pygame.display.update(active_scene.board_update_rectangles)
            GAME_TIME.tick(200)

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


class Scene(ABC):
    def __init__(self, screen, sprite_group):
        self.screen = screen
        self.rect = self.screen.get_rect()

        #value used for the main regulator to determine what rectangles of the screen to update
        self.board_update_rectangles = []
        self.sprite_group = sprite_group

        # signifies if the scene is still alive
        self.going = True

    def update(self):
        self.scene_updates()
        self.handle_events()
        self.sprite_group.update()
        self.draw()

    def handle_events(self):
        if len(pygame.event.get(QUIT)) > 0:
            self.going = False
            return []
        events = pygame.event.get()
        return events

    def set_update_rectangles(self):
        # default is the full screen least efficient
        self.board_update_rectangles = self.rect

    def scene_updates(self):
        for sprite in self.sprite_group.sprites():
            self.sprite_group.change_layer(sprite, sprite._layer)
        self.set_update_rectangles()

    def draw(self):
        self.sprite_group.draw(self.screen)

    def exit(self):
        pass

    @classmethod
    def name(cls):
        return cls.__name__


class MainMenu(Scene):
    def __init__(self, screen):
        sprite_group = ShowToggleLayerUpdates()
        super().__init__(screen, sprite_group)

        # all the available menu frames
        self.main_menu_frame = None
        self.__init_widgets()

    def __init_widgets(self):
        self.main_menu_frame = Frame((0, 0), Size(*self.rect.size), self.sprite_group,
                                     color=(173, 94, 29), static=False)

        button_size = Size(100, 40)
        y_coord = 200
        play_button = Button(button_size, color=(100, 100, 100), text="START", font_size=30)
        play_button.set_action(1, self.__start_game, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), play_button)

        y_coord += 50
        load_button = Button(button_size, color=(100, 100, 100), text="LOAD", font_size=30)
        load_button.set_action(1, self.__load_game, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), load_button)

        y_coord += 50
        settings_button = Button(button_size, color=(100, 100, 100), text="SETTINGS", font_size=30)
        settings_button.set_action(1, self.__open_settings, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), settings_button)

        y_coord += 50
        quit_button = Button(button_size, color=(100, 100, 100), text="QUIT", font_size=30)
        quit_button.set_action(1, self.__quit, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), quit_button)

    def handle_events(self):
        events = super().handle_events()
        self.main_menu_frame.handle_events(events)

    def __start_game(self):
        game = Game(self.screen)
        executor = ThreadPoolExecutorStackTraced()
        future = executor.submit(game.start)
        utilities.scenes[LoadingScreen.name()] = LoadingScreen(self.screen, future, game, executor)
        utilities.scenes.set_active_scene(LoadingScreen.name())

    def __load_game(self):
        warnings.warn("Game loading is not avaialable yet", utilities.NotImplementedWarning)
        with open(f"{SAVE_DIR}{os.sep}test_save.json", "r") as fp:
            game = Game.from_json(fp)
        utilities.scenes[Game.name()] = game

    def __open_settings(self):
        warnings.warn("No settings available yet", utilities.NotImplementedWarning)

    def __quit(self):
        self.going = False


class LoadingScreen(Scene):
    def __init__(self, screen, future, loading_scene, executor):
        sprite_group = ShowToggleLayerUpdates()
        super().__init__(screen, sprite_group)
        self.loading_scene = loading_scene
        self.executor = executor
        self.future = future
        self.__loading_frame = None
        self.__progress_label = None
        self.__init_widgets()
        self.__finished_loading = False

    def __init_widgets(self):
        self.__loading_frame = Frame((0, 0), Size(*self.rect.size), self.sprite_group,
                                     color=(173, 94, 29), static=False)
        self.__progress_label = Label((500, 20), (173, 94, 29))
        self.__loading_frame.add_widget(("center", "center"), self.__progress_label)

    def scene_updates(self):
        super().scene_updates()
        if hasattr(self.loading_scene, "progress"):
            self.__progress_label.set_text(self.loading_scene.progress, "center", font_size=30)
        if self.future.done():
            if self.future.exception():
                print(self.future.exception())
                # if an exception was raised make sure to exit
                exit(-1)
            self.executor.shutdown()
            utilities.scenes[self.loading_scene.name()] = self.loading_scene
            utilities.scenes.set_active_scene(self.loading_scene.name())
            self.__finished_loading = True

    def draw(self):
        if self.__finished_loading:
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
        else:
            super().draw()


class Game(Scene, Serializer):
    def __init__(self, screen, camera_center=None, board=None, task_control=None):
        # camera center position is chnaged before starting the game
        # TODO make the size 0,0
        self.camera_center = camera_center if camera_center else CameraCentre((0, 0), (5, 5))
        sprite_group = CameraAwareLayeredUpdates(self.camera_center, BOARD_SIZE)
        super().__init__(screen, sprite_group)
        # update rectangles
        self.__vision_rectangles = []
        self.__debug_rectangle = (0, 0, 0, 0)

        self._visible_entities = 0

        # zoom variables
        self._zoom = 1.0
        self.progress = ""
        self.board = board
        self.task_control = task_control

        # ready made windows
        self.building_interface = small_interfaces.BuildingWindow(self.board.inventorie_blocks[0].inventory,
                                                                  self.sprite_group) if self.board else None
        self.pause_window = small_interfaces.PauseWindow(self.sprite_group)

    def start(self):
        # function for setting up a Game
        self.progress = "Started loading..."
        # load a window manager to manage window events
        self.progress = "Adding windows..."
        create_window_managers(self.camera_center)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.progress = "Generating board..."
        self.board = board.board.Board(self.sprite_group)
        self.board.setup_board()

        # tasks
        self.progress = "Making tasks..."
        self.task_control = TaskControl(self.board)
        self.board.set_task_control(self.task_control)

        # for some more elaborate setting up of variables
        self.progress = "Populating with miners..."
        start_chunk = self.board.get_start_chunk()
        appropriate_location = (int(start_chunk.START_RECTANGLE.centerx / BLOCK_SIZE.width) * BLOCK_SIZE.width + start_chunk.rect.left,
            + start_chunk.START_RECTANGLE.bottom - BLOCK_SIZE.height + start_chunk.rect.top)
        for _ in range(5):
            Worker(appropriate_location, self.sprite_group, board=self.board, task_control=self.task_control)
        # add one of the imventories of the terminal
        if self.building_interface is None:
            self.building_interface = small_interfaces.BuildingWindow(self.board.inventorie_blocks[0].inventory,
                                                                  self.sprite_group)
        self.camera_center.rect.center = start_chunk.rect.center

    def to_dict(self):
        return {
            "camera_center": self.camera_center.to_dict(),
            "entities": [sprite.to_dict() for sprite in self.sprite_group.sprites() if not isinstance(sprite, Frame) and not isinstance(sprite, BoardImage) and sprite is not self.camera_center],
            "board": self.board.to_dict()
        }

    @classmethod
    def from_dict(cls, screen=None, **arguments):
        arguments["camera_center"] = CameraCentre.from_dict(**arguments["camera_center"])
        board_dct = arguments.pop("board")
        ents = arguments.pop("entities")
        inst = super().from_dict(screen=screen, **arguments)
        entity_objects = [getattr(entities, dct["type"]).from_dict(**dct) for dct in ents]
        inst.sprite_group.add(entity_objects)
        inst.board = board.board.Board.from_dict(sprite_group=inst.sprite_group, **board_dct)
        return inst

    def save(self):
        with open(f"{SAVE_DIR}{os.sep}test_save.json", "w") as fp:
            self.to_json(fp)
        warnings.warn("Save is not implemented yet", utilities.NotImplementedWarning)

    def scene_updates(self):
        super().scene_updates()
        self.load_unload_sprites()

        self.board.update_board()

    def draw(self):
        super().draw()
        self.draw_debug_info()

    def handle_events(self):
        events = super().handle_events()
        cam_events = []
        leftover_events = []
        for event in events:
            if event.type == KEYDOWN and event.key in INTERFACE_KEYS:
                self.__handle_interface_selection_events(event)
                # allow these events to trigger after
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
                if event.type == KEYUP and event.key == K_ESCAPE:
                    self.window_manager.add(self.pause_window)
            self.board.handle_events(leftover_events)

    def set_update_rectangles(self):
        # get a number of rectangles that encompass the changed board state

        zoom = self._zoom

        relative_board_start = screen_to_board_coordinate((0, 0), self.sprite_group.target, zoom)

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
        c = self.sprite_group.target.rect.center
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
        for sprite in self.sprite_group.sprites():
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
            en = FONTS[18].render("e: {}/{}".format(self._visible_entities, len(self.sprite_group.sprites())),
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
            for sprite in self.sprite_group.sprites():
                if sprite.zoomable:
                    sprite.zoom(self._zoom)
            BOARD_SIZE.width = self._zoom * ORIGINAL_BOARD_SIZE.width
            BOARD_SIZE.height = self._zoom * ORIGINAL_BOARD_SIZE.height


if __name__ == "__main__":
    Main()