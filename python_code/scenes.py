import os
import warnings
from abc import ABC

import pygame

import board.board
import entities
import tasks
from board import sprite_groups as sprite_groups, chunks as chunks
from interfaces import widgets as widgets, interface_utility as interface_util, small_interfaces as small_interfaces, \
    managers as window_managers
from utility import constants as con, utilities as util


scenes = None


def create_scene_manager():
    global scenes
    scenes = SceneManager()


class SceneManager:
    def __init__(self):
        # the drawing destination surface
        self.scenes = {}
        self.active_scene = None

    def set_active_scene(self, name):
        if self.active_scene:
            self.active_scene.exit()
        self.active_scene = self.scenes[name]

    def __getitem__(self, item):
        return self.scenes[item]

    def __setitem__(self, key, value):
        self.scenes[key] = value

    def __delitem__(self, key):
        del self.scenes[key]

    def is_scene_alive(self):
        return self.active_scene.going


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
        if len(pygame.event.get(con.QUIT)) > 0:
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
        sprite_group = sprite_groups.ShowToggleLayerUpdates()
        super().__init__(screen, sprite_group)

        # all the available menu frames
        self.main_menu_frame = None
        self.__init_widgets()

    def __init_widgets(self):
        self.main_menu_frame = widgets.Frame((0, 0), util.Size(*self.rect.size), self.sprite_group,
                                     color=(173, 94, 29), static=False)

        button_size = util.Size(100, 40)
        y_coord = 200
        play_button = widgets.Button(button_size, color=(100, 100, 100), text="START", font_size=30)
        play_button.set_action(1, self.__start_game, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), play_button)

        y_coord += 50
        load_button = widgets.Button(button_size, color=(100, 100, 100), text="LOAD", font_size=30)
        load_button.set_action(1, self.__load_game, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), load_button)

        y_coord += 50
        settings_button = widgets.Button(button_size, color=(100, 100, 100), text="SETTINGS", font_size=30)
        settings_button.set_action(1, self.__open_settings, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), settings_button)

        y_coord += 50
        quit_button = widgets.Button(button_size, color=(100, 100, 100), text="QUIT", font_size=30)
        quit_button.set_action(1, self.__quit, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), quit_button)

    def handle_events(self):
        events = super().handle_events()
        self.main_menu_frame.handle_events(events)

    def __start_game(self):
        game = Game(self.screen)
        executor = interface_util.ThreadPoolExecutorStackTraced()
        future = executor.submit(game.start)
        util.scenes[LoadingScreen.name()] = LoadingScreen(self.screen, future, game, executor)
        util.scenes.set_active_scene(LoadingScreen.name())

    def __load_game(self):
        warnings.warn("Game loading is not avaialable yet", util.NotImplementedWarning)
        with open(f"{con.SAVE_DIR}{os.sep}test_save.json", "r") as fp:
            game = Game.from_json(fp)
        util.scenes[Game.name()] = game

    def __open_settings(self):
        warnings.warn("No settings available yet", util.NotImplementedWarning)

    def __quit(self):
        self.going = False


class LoadingScreen(Scene):
    def __init__(self, screen, future, loading_scene, executor):
        sprite_group = sprite_groups.ShowToggleLayerUpdates()
        super().__init__(screen, sprite_group)
        self.loading_scene = loading_scene
        self.executor = executor
        self.future = future
        self.__loading_frame = None
        self.__progress_label = None
        self.__init_widgets()
        self.__finished_loading = False

    def __init_widgets(self):
        self.__loading_frame = widgets.Frame((0, 0), util.Size(*self.rect.size), self.sprite_group,
                                     color=(173, 94, 29), static=False)
        self.__progress_label = widgets.Label((500, 20), (173, 94, 29))
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
            util.scenes[self.loading_scene.name()] = self.loading_scene
            util.scenes.set_active_scene(self.loading_scene.name())
            self.__finished_loading = True

    def draw(self):
        if self.__finished_loading:
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
        else:
            super().draw()


class Game(Scene, util.Serializer):
    def __init__(self, screen, camera_center=None, board=None, task_control=None):
        # camera center position is chnaged before starting the game
        # TODO make the size 0,0
        self.camera_center = camera_center if camera_center else entities.CameraCentre((0, 0), (5, 5))
        sprite_group = sprite_groups.CameraAwareLayeredUpdates(self.camera_center, con.BOARD_SIZE)
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
        window_managers.create_window_managers(self.camera_center)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.progress = "Generating board..."
        self.board = board.board.Board(self.sprite_group)
        self.board.setup_board()

        # tasks
        self.progress = "Making tasks..."
        self.task_control = tasks.TaskControl(self.board)
        self.board.set_task_control(self.task_control)

        # for some more elaborate setting up of variables
        self.progress = "Populating with miners..."
        start_chunk = self.board.get_start_chunk()
        appropriate_location = (int(start_chunk.START_RECTANGLE.centerx / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width + start_chunk.rect.left,
            + start_chunk.START_RECTANGLE.bottom - con.BLOCK_SIZE.height + start_chunk.rect.top)
        for _ in range(5):
            entities.Worker(appropriate_location, self.sprite_group, board=self.board, task_control=self.task_control)
        # add one of the imventories of the terminal
        if self.building_interface is None:
            self.building_interface = small_interfaces.BuildingWindow(self.board.inventorie_blocks[0].inventory,
                                                                  self.sprite_group)
        self.camera_center.rect.center = start_chunk.rect.center

    def to_dict(self):
        return {
            "camera_center": self.camera_center.to_dict(),
            "entities": [sprite.to_dict() for sprite in self.sprite_group.sprites() if not isinstance(sprite, widgets.Frame) and not isinstance(sprite, chunks.BoardImage) and sprite is not self.camera_center],
            "board": self.board.to_dict()
        }

    @classmethod
    def from_dict(cls, screen=None, **arguments):
        arguments["camera_center"] = entities.CameraCentre.from_dict(**arguments["camera_center"])
        board_dct = arguments.pop("board")
        ents = arguments.pop("entities")
        inst = super().from_dict(screen=screen, **arguments)
        entity_objects = [getattr(entities, dct["type"]).from_dict(**dct) for dct in ents]
        inst.sprite_group.add(entity_objects)
        inst.board = board.board.Board.from_dict(sprite_group=inst.sprite_group, **board_dct)
        return inst

    def save(self):
        with open(f"{con.SAVE_DIR}{os.sep}test_save.json", "w") as fp:
            self.to_json(fp)
        warnings.warn("Save is not implemented yet", util.NotImplementedWarning)

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
            if event.type == con.KEYDOWN and event.key in con.INTERFACE_KEYS:
                self.__handle_interface_selection_events(event)
                # allow these events to trigger after
                leftover_events.append(event)

            elif (event.type == con.KEYDOWN or event.type == con.KEYUP) and \
                    event.key in con.CAMERA_KEYS:
                cam_events.append(event)
            else:
                leftover_events.append(event)
        if cam_events:
            self.camera_center.handle_events(cam_events)
        if leftover_events:
            leftover_events = self.window_manager.handle_events(leftover_events)
            for event in leftover_events:
                if event.type == con.MOUSEBUTTONDOWN or event.type == con.MOUSEBUTTONUP:
                    if event.button == 4:
                        self.__zoom_entities(0.1)
                    elif event.button == 5:
                        self.__zoom_entities(-0.1)
                if event.type == con.KEYUP and event.key == con.K_ESCAPE:
                    self.window_manager.add(self.pause_window)
            self.board.handle_events(leftover_events)

    def set_update_rectangles(self):
        # get a number of rectangles that encompass the changed board state

        zoom = self._zoom

        relative_board_start = interface_util.screen_to_board_coordinate((0, 0), self.sprite_group.target, zoom)

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
        if c[0] + con.SCREEN_SIZE.width / 2 - con.BOARD_SIZE.width > 0:
            x = 1 + (c[0] + con.SCREEN_SIZE.width / 2 - con.BOARD_SIZE.width) / (con.SCREEN_SIZE.width / 2)
        elif con.SCREEN_SIZE.width / 2 - c[0] > 0:
            x = 1 + (con.SCREEN_SIZE.width / 2 - c[0]) / (con.SCREEN_SIZE.width / 2)
        else:
            x = 1
        if c[1] + con.SCREEN_SIZE.height / 2 - con.BOARD_SIZE.height > 0:
            y = 1 + (c[1] + con.SCREEN_SIZE.height / 2 - con.BOARD_SIZE.height) / (con.SCREEN_SIZE.height / 2)
        elif con.SCREEN_SIZE.height / 2 - c[1] > 0:
            y = 1 + (con.SCREEN_SIZE.height / 2 - c[1]) / (con.SCREEN_SIZE.height / 2)
        else:
            y = 1
        visible_rect = pygame.Rect(0, 0, int(con.SCREEN_SIZE.width * x), int(con.SCREEN_SIZE.height * y ))
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
        if con.FPS:
            fps = con.FONTS[18].render("fps: {}".format(int(con.GAME_TIME.get_fps())), True, pygame.Color('white'))
            self.screen.blit(fps, (x_coord, y_coord))
            y_coord += line_distance
        if con.ENTITY_NMBR:
            en = con.FONTS[18].render("e: {}/{}".format(self._visible_entities, len(self.sprite_group.sprites())),
                                  True, pygame.Color('white'))
            self.screen.blit(en, (x_coord, y_coord))
            y_coord += line_distance
        if con.SHOW_ZOOM:
            z = con.FONTS[18].render("zoom: {}x".format(self._zoom), True, pygame.Color('white'))
            self.screen.blit(z, (x_coord, y_coord))
            y_coord += line_distance
        self.__debug_rectangle = (*debug_topleft, width, y_coord - debug_topleft[1])

#handeling of events
    def __handle_interface_selection_events(self, event):
        if event.key == con.BUILDING:
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
            con.BOARD_SIZE.width = self._zoom * con.ORIGINAL_BOARD_SIZE.width
            con.BOARD_SIZE.height = self._zoom * con.ORIGINAL_BOARD_SIZE.height