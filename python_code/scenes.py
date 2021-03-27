#!/usr/bin/python3

# library imports
import os
import warnings
from abc import ABC
import pygame
from typing import Union

# own imports
import board.board
import entities
import tasks
from board import sprite_groups as sprite_groups, chunks as chunks
from interfaces import widgets as widgets, interface_utility as interface_util, other_interfaces as small_interfaces, \
    managers as window_managers, console
from utility import constants as con, utilities as util, event_handling
import board_generation.generation as generation
import user
from utility import game_timing


# defined below SceneManager
scenes: "SceneManager"


class SceneManager:
    def __init__(self):
        # the drawing destination surface
        self.__scenes = {}
        self.active_scene = None

    def set_active_scene(self, name):
        if self.active_scene:
            self.active_scene.exit()
        self.active_scene = self.__scenes[name]

    def __contains__(
        self,
        item: str
    ) -> bool:
        return item in self.__scenes

    def __getitem__(self, item):
        return self.__scenes[item]

    def __setitem__(self, key, value):
        self.__scenes[key] = value

    def __delitem__(self, key):
        del self.__scenes[key]

    def is_scene_alive(self):
        return self.active_scene.going


scenes: "SceneManager" = SceneManager()


class Scene(event_handling.EventHandler, ABC):
    def __init__(self, screen, sprite_group, recordable_keys=None):
        event_handling.EventHandler.__init__(self, recordable_keys if recordable_keys else [])
        self.screen = screen
        self.rect = self.screen.get_rect()

        # value used for the main regulator to determine what rectangles of the screen to update
        self.board_update_rectangles = []
        self.sprite_group = sprite_group

        # signifies if the scene is still alive
        self.going = True
        self.__counter = 0

    def update(self):
        self.scene_updates()
        self.scene_event_handling()
        self.sprite_group.update()
        self.draw()
        self.__counter += 1
        if self.__counter == 500 and con.DEBUG.PRINT_TIMING_BREAKDOWN:
            self.__counter = 0
            print(game_timing.TIMINGS.get_time_summary())

    def get_events(self):
        """Starting point for event handling"""
        if len(pygame.event.get(con.QUIT)) > 0:
            self.going = False
            return []
        events = pygame.event.get()
        return events

    def scene_event_handling(self):
        return self.get_events()

    def set_update_rectangles(self):
        # default is the full screen least efficient
        self.board_update_rectangles = self.rect

    def scene_updates(self):
        # TODO make this how it was intended using the build in method
        for sprite in self.sprite_group.sprites():
            self.sprite_group.change_layer(sprite, sprite._layer)
        self.set_update_rectangles()

    @game_timing.time_function("scene drawing")
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
        new_button = widgets.Button(button_size, color=(100, 100, 100), text="NEW", font_size=30)
        new_button.add_key_event_listener(1, self.__open_game_settings, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), new_button)

        y_coord += 50
        load_button = widgets.Button(button_size, color=(100, 100, 100), text="LOAD", font_size=30)
        load_button.add_key_event_listener(1, self.__load_game, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), load_button)

        y_coord += 50
        settings_button = widgets.Button(button_size, color=(100, 100, 100), text="SETTINGS", font_size=30)
        settings_button.add_key_event_listener(1, self.__open_settings, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), settings_button)

        y_coord += 50
        quit_button = widgets.Button(button_size, color=(100, 100, 100), text="QUIT", font_size=30)
        quit_button.add_key_event_listener(1, self.__quit, types=["unpressed"])
        self.main_menu_frame.add_widget(("center", y_coord), quit_button)

    def scene_event_handling(self, consume=False):
        events = super().scene_event_handling()
        mouse_events = []
        other_events = []
        for event in events:
            if event.type in (con.MOUSEBUTTONDOWN, con.MOUSEBUTTONUP, con.MOUSEMOTION):
                mouse_events.append(event)
            else:
                other_events.append(event)
        self.main_menu_frame.handle_mouse_events(mouse_events, consume_events=consume)
        self.main_menu_frame.handle_other_events(other_events, consume_events=consume)

    def __open_game_settings(self):
        global scenes
        scenes[GameSettingsScene.name()] = GameSettingsScene(self.screen)
        scenes.set_active_scene(GameSettingsScene.name())

    def __load_game(self):
        global scenes
        warnings.warn("Game loading is not avaialable yet", util.NotImplementedWarning)
        with open(f"{con.SAVE_DIR}{os.sep}test_save.json", "r") as fp:
            game = Game.from_json(fp)
        scenes[Game.name()] = game

    def __open_settings(self):
        warnings.warn("No settings available yet", util.NotImplementedWarning)

    def __quit(self):
        self.going = False


class GameSettingsScene(Scene):
    __game_name_textbox: Union[None, widgets.MultilineTextBox]
    __cave_length_selection_list: Union[None, widgets.SelectionList]
    __cave_width_selection_list: Union[None, widgets.SelectionList]
    __max_caves_selection_list: Union[None, widgets.SelectionList]
    __biome_size_selection_list: Union[None, widgets.SelectionList]
    __biome_blend_selection_list: Union[None, widgets.SelectionList]

    def __init__(self, screen):
        sprite_group = sprite_groups.ShowToggleLayerUpdates()
        super().__init__(screen, sprite_group)

        # all the available menu frames
        self.settings_menu_frame = None
        self.__game_name_textbox = None
        self.__cave_length_selection_list = None
        self.__cave_width_selection_list = None
        self.__max_caves_selection_list = None
        self.__biome_size_selection_list = None
        self.__biome_blend_selection_list = None
        self.__init_widgets()

    def __init_widgets(self):
        self.settings_menu_frame = widgets.Frame((0, 0), util.Size(*self.rect.size), self.sprite_group,
                                                 color=(173, 94, 29), static=False)
        frame_rect = self.settings_menu_frame.rect

        widget_size = util.Size(100, 40)
        color = (173, 94, 29)
        y_coord = 100

        # GENERAL OPTIONS
        generel_options_pane = widgets.Pane((frame_rect.width - 100, 100), border=True, border_width=4,
                                            color=color)
        self.settings_menu_frame.add_widget(("center", y_coord), generel_options_pane)
        local_y = 10
        local_x = int((generel_options_pane.rect.width / 2) + 5)
        self.__game_name_textbox = widgets.MultilineTextBox((200, con.FONTS[22].get_linesize() + 6), font_size=22,
                                                            lines=1)
        generel_options_pane.add_widget((local_x, local_y), self.__game_name_textbox)

        local_x = int((generel_options_pane.rect.width / 2) - 135)
        game_name_label = widgets.Label((140, con.FONTS[22].get_linesize()), color=color, text="Name:", font_size=22,
                                        text_pos=("W", "C"), selectable=False)
        generel_options_pane.add_widget((local_x, local_y), game_name_label)

        # GENERATION OPTIONS
        y_coord += generel_options_pane.rect.height + 10
        generation_values_pane = widgets.Pane((frame_rect.width - 100, 300), border=True, border_width=4,
                                              color=color)
        self.settings_menu_frame.add_widget(("center", y_coord), generation_values_pane)

        # Biome size selection
        local_y = 10
        local_x = int((generation_values_pane.rect.width / 2) + 5)
        self.__biome_size_selection_list =\
            widgets.SelectionList(self.sprite_group, color=(150, 150, 150),
                                  options=list(generation.BoardGenerator.BIOME_SIZES.keys()))
        self.__biome_size_selection_list.select_option("normal")
        generation_values_pane.add_widget((local_x, local_y), self.__biome_size_selection_list)

        biome_size_label = widgets.Label((100, self.__biome_size_selection_list.LINE_HEIGHT), color=color,
                                         text="Biome Size:", font_size=22, text_pos=("W", "C"), selectable=False)
        biome_size_tooltip = widgets.Tooltip(self.sprite_group, color=(150, 150, 150), text="Average size of biomes")
        biome_size_label.add_tooltip(biome_size_tooltip)
        local_x = int((generation_values_pane.rect.width / 2) - 135)
        generation_values_pane.add_widget((local_x, local_y), biome_size_label)

        # Biome blend selection
        local_y += self.__biome_size_selection_list.LINE_HEIGHT + 10
        local_x = int((generation_values_pane.rect.width / 2) + 5)
        self.__biome_blend_selection_list = \
            widgets.SelectionList(self.sprite_group, color=(150, 150, 150),
                                  options=list(generation.BoardGenerator.BIOME_BLEND.keys()))
        self.__biome_blend_selection_list.select_option("normal")
        generation_values_pane.add_widget((local_x, local_y), self.__biome_blend_selection_list)

        biome_blend_label = widgets.Label((100, self.__biome_blend_selection_list.LINE_HEIGHT), color=color,
                                          text="Biome Blend:", font_size=22, text_pos=("W", "C"), selectable=False)
        biome_blend_tooltip = widgets.Tooltip(self.sprite_group, color=(150, 150, 150),
                                              text="The level to which biomes\ncan blend trough one another")
        biome_blend_label.add_tooltip(biome_blend_tooltip)
        local_x = int((generation_values_pane.rect.width / 2) - 135)
        generation_values_pane.add_widget((local_x, local_y), biome_blend_label)

        # Max Caves selection
        local_y += self.__biome_blend_selection_list.LINE_HEIGHT + 10
        local_x = int((generation_values_pane.rect.width / 2) + 5)
        self.__max_caves_selection_list = \
            widgets.SelectionList(self.sprite_group, color=(150, 150, 150),
                                  options=list(generation.BoardGenerator.MAX_CAVES.keys()))
        self.__max_caves_selection_list.select_option("normal")
        generation_values_pane.add_widget((local_x, local_y), self.__max_caves_selection_list)

        max_caves_label = widgets.Label((140, self.__max_caves_selection_list.LINE_HEIGHT), color=color,
                                        text="Number of Caves:", font_size=22, text_pos=("W", "C"), selectable=False)
        max_caves_tooltip = widgets.Tooltip(self.sprite_group, color=(150, 150, 150),
                                            text="The amount of caves present on the map")
        max_caves_label.add_tooltip(max_caves_tooltip)
        local_x = int((generation_values_pane.rect.width / 2) - 135)
        generation_values_pane.add_widget((local_x, local_y), max_caves_label)

        # Cave length selection
        local_y += self.__max_caves_selection_list.LINE_HEIGHT + 10
        local_x = int((generation_values_pane.rect.width / 2) + 5)
        self.__cave_length_selection_list =\
            widgets.SelectionList(self.sprite_group, color=(150, 150, 150),
                                  options=list(generation.BoardGenerator.CAVE_LENGTH.keys()))
        self.__cave_length_selection_list.select_option("normal")
        generation_values_pane.add_widget((local_x, local_y), self.__cave_length_selection_list)

        cave_length_label = widgets.Label((140, self.__cave_length_selection_list.LINE_HEIGHT), color=color,
                                          text="Length of Caves:", font_size=22, text_pos=("W", "C"), selectable=False)
        cave_length_tooltip = widgets.Tooltip(self.sprite_group, color=(150, 150, 150),
                                              text="The lenght of the caves")
        cave_length_label.add_tooltip(cave_length_tooltip)
        local_x = int((generation_values_pane.rect.width / 2) - 135)
        generation_values_pane.add_widget((local_x, local_y), cave_length_label)

        # Cave width selection
        local_y += self.__max_caves_selection_list.LINE_HEIGHT + 10
        local_x = int((generation_values_pane.rect.width / 2) + 5)
        self.__cave_width_selection_list = \
            widgets.SelectionList(self.sprite_group, color=(150, 150, 150),
                                  options=list(generation.BoardGenerator.CAVE_STOP_SPREAD_CHANCE.keys()))
        self.__cave_width_selection_list.select_option("normal")
        generation_values_pane.add_widget((local_x, local_y), self.__cave_width_selection_list)

        cave_width_label = widgets.Label((140, self.__cave_width_selection_list.LINE_HEIGHT), color=color,
                                         text="Width of Caves:", font_size=22, text_pos=("W", "C"), selectable=False)
        cave_width_tooltip = widgets.Tooltip(self.sprite_group, color=(150, 150, 150),
                                             text="How wide a cave is")
        cave_width_label.add_tooltip(cave_width_tooltip)
        local_x = int((generation_values_pane.rect.width / 2) - 135)
        generation_values_pane.add_widget((local_x, local_y), cave_width_label)

        # general buttons
        y_coord += generation_values_pane.rect.height + 20
        x_coord = (frame_rect.width / 2) - widget_size.width - 5
        start_game_btn = widgets.Button(widget_size, color=(100, 100, 100), text="START", font_size=30)
        start_game_btn.add_key_event_listener(1, self.__start_game)
        self.settings_menu_frame.add_widget((x_coord, y_coord), start_game_btn)

        x_coord = (frame_rect.width / 2) + 5
        back_btn = widgets.Button(widget_size, color=(100, 100, 100), text="BACK", font_size=30)
        back_btn.add_key_event_listener(1, self.__back_to_main)
        self.settings_menu_frame.add_widget((x_coord, y_coord), back_btn)

    def get_options(self) -> dict:
        options = dict(
            name=self.__game_name_textbox.get_text(),
            cave_length=self.__cave_length_selection_list.get_selected_text(),
            cave_width=self.__cave_width_selection_list.get_selected_text(),
            max_caves=self.__max_caves_selection_list.get_selected_text(),
            biome_size=self.__biome_size_selection_list.get_selected_text(),
            biome_blend=self.__biome_blend_selection_list.get_selected_text(),
        )
        return options

    def __start_game(self):
        global scenes
        game = Game(self.screen, self.get_options())
        executor = interface_util.ThreadPoolExecutorStackTraced()
        future = executor.submit(game.start)
        scenes[LoadingScreen.name()] = LoadingScreen(self.screen, future, game, executor)
        scenes.set_active_scene(LoadingScreen.name())

    def __back_to_main(self):
        global scenes
        if MainMenu.name() not in scenes:
            scenes[MainMenu.name()] = MainMenu(self.screen)
        scenes.set_active_scene(MainMenu.name())

    def scene_event_handling(self, consume=False):
        events = super().scene_event_handling()
        mouse_events = []
        other_events = []
        for event in events:
            if event.type in (con.MOUSEBUTTONDOWN, con.MOUSEBUTTONUP):
                mouse_events.append(event)
            else:
                other_events.append(event)
        self.settings_menu_frame.handle_mouse_events(mouse_events, consume_events=consume)
        self.settings_menu_frame.handle_other_events(other_events, consume_events=consume)


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
        global scenes
        super().scene_updates()
        if hasattr(self.loading_scene, "progress_var"):
            self.__progress_label.set_text(self.loading_scene.progress_var[0], ("center", "center"), font_size=30)
        if self.future.done():
            if self.future.exception():
                print(self.future.exception())
                # if an exception was raised make sure to exit
                exit(-1)
            self.executor.shutdown()
            scenes[self.loading_scene.name()] = self.loading_scene
            scenes.set_active_scene(self.loading_scene.name())
            self.__finished_loading = True

    def draw(self):
        if self.__finished_loading:
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
        else:
            super().draw()


class Game(Scene, util.Serializer):
    def __init__(self, screen, options, camera_center=None, board_=None, task_control=None):
        # camera center position is chnaged before starting the game
        # TODO make the size 0,0
        self.__selected_options = options
        self.camera_center = camera_center if camera_center else entities.CameraCentre((0, 0), (5, 5))
        sprite_group = sprite_groups.CameraAwareLayeredUpdates(self.camera_center, con.BOARD_SIZE)
        super().__init__(screen, sprite_group, recordable_keys=[4, 5, con.K_ESCAPE, con.K_b, con.K_COMMA])
        # update rectangles
        self.__vision_rectangles = []
        self.__debug_rectangle = (0, 0, 0, 0)

        self._visible_entities = 0

        # zoom variables
        self._zoom = 1.0
        self.progress_var = [""]
        self.board = board_
        self.task_control = task_control
        self.user = None
        self.pause_window = None
        self.console_window = None

        # ready made windows
        self.window_manager = None
        self.building_interface = small_interfaces.BuildingWindow(self.board.inventorie_blocks[0].inventory,
                                                                  self.sprite_group) if self.board else None

    def start(self):
        # function for setting up a Game
        self.progress_var[0] = "Started loading..."
        # load a window manager to manage window events
        self.progress_var[0] = "Adding windows..."
        window_managers.create_window_managers(self.camera_center)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.progress_var[0] = "configuring board generation..."
        board_generator = generation.BoardGenerator(
            cave_length=self.__selected_options["cave_length"],
            cave_broadness=self.__selected_options["cave_width"],
            nr_caves=self.__selected_options["max_caves"],
            biome_size=self.__selected_options["biome_size"],
            biome_blend=self.__selected_options["biome_blend"],
            progress_var=self.progress_var
        )

        self.progress_var[0] = "Generating board..."
        self.board = board.board.Board(board_generator, self.sprite_group, self.progress_var)
        self.progress_var[0] = "Running some innitial update cycles..."
        self.board.setup_board()

        self.user = user.User(self.board, self.progress_var, self.sprite_group)

        # add one of the imventories of the terminal
        if self.building_interface is None:
            self.building_interface = small_interfaces.BuildingWindow(self.board.inventorie_blocks[0].inventory,
                                                                      self.sprite_group)

        self.camera_center.rect.center = self.board.get_start_chunk().rect.center
        self.pause_window = small_interfaces.PauseWindow(self.sprite_group)
        self.console_window = console.ConsoleWindow(self.sprite_group, self.board, self.user)

    def to_dict(self):
        return {
            "camera_center": self.camera_center.to_dict(),
            "entities": [sprite.to_dict() for sprite in self.sprite_group.sprites()
                         if not isinstance(sprite, widgets.Frame) and not
                         isinstance(sprite, chunks.BoardImage) and sprite is not self.camera_center],
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

        # self.draw_air_rectangles()
        self.board.update_board()

    def draw_air_rectangles(self):
        for key in self.board.pathfinding.pathfinding_tree.rectangle_network[0]:
            for rect in self.board.pathfinding.pathfinding_tree.rectangle_network[0][key]:
                self.board.add_rectangle(rect, (0,0,0), layer=1, border=2)

    def draw(self):
        super().draw()
        self.draw_debug_info()

    @game_timing.time_function("scene event handling")
    def scene_event_handling(self, consume=False):
        events = super().scene_event_handling()
        self.__handle_interface_selection_events()

        leftover_events = self.window_manager.handle_events(events)
        leftover_events = self.camera_center.handle_events(leftover_events)
        super().handle_events(leftover_events, consume_events=consume)
        if self.pressed(4) or self.unpressed(4):
            self.__zoom_entities(0.1)
        if self.pressed(5) or self.unpressed(5):
            self.__zoom_entities(-0.1)
        if self.unpressed(con.K_ESCAPE):
            self.window_manager.add(self.pause_window)
        if self.unpressed(con.K_COMMA):
            self.window_manager.add(self.console_window)
        self.user.handle_events(leftover_events)

    def set_update_rectangles(self):
        # get a number of rectangles that encompass the changed board state

        zoom = self._zoom

        relative_board_start = interface_util.screen_to_board_coordinate((0, 0), self.sprite_group.target, zoom)

        # rectangles directly on the screen that need to be visually updated
        board_u_rects = [self.__debug_rectangle]

        # rectangles containing part or whole chunks that are visible due to vision
        vision_u_rects = []

        for chunk in self.board.loaded_chunks:
            rect = chunk.layers[0].get_update_rect()
            if rect is None:
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
                # TODO fix this kind of cheaty fix, right now the rectangle is made bigger to cover the full area, but
                #  this is a halfed as solution
                adjusted_rect = pygame.Rect((round(rect[0]) - 5,
                                             round(rect[1]) - 5,
                                             rect.width + 10, rect.height + 10))
                clipped_rect = adjusted_rect.clip(self.rect)
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    board_u_rects.append(clipped_rect)
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
        """Set which sprites are drawn to the board image. Also allow to force draw sprites by adding theire
         board rect"""
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
        visible_rect = pygame.Rect(0, 0, int(con.SCREEN_SIZE.width * x), int(con.SCREEN_SIZE.height * y))
        visible_rect.center = c

        self._visible_entities = 0
        for sprite in self.sprite_group.sprites():
            if con.DEBUG.NO_LIGHTING or not sprite.static or (sprite.rect.colliderect(visible_rect) and
                                                        sprite.orig_rect.collidelist(self.__vision_rectangles) != -1):
                sprite.show(True)
                if sprite.is_showing():
                    self._visible_entities += 1
                    if isinstance(sprite, widgets.Tooltip):
                        self.board_update_rectangles.append(sprite.orig_rect)
            else:
                sprite.show(False)

    def draw_debug_info(self):
        x_coord = 5
        line_distance = 12
        width = 70

        y_coord = 5
        debug_topleft = (x_coord, y_coord)
        if con.DEBUG.FPS:
            fps = con.FONTS[18].render("fps: {}".format(int(con.GAME_TIME.get_fps())), True, pygame.Color('white'))
            self.screen.blit(fps, (x_coord, y_coord))
            y_coord += line_distance
        if con.DEBUG.ENTITY_NMBR:
            en = con.FONTS[18].render("e: {}/{}".format(self._visible_entities, len(self.sprite_group.sprites())), True,
                                      pygame.Color('white'))
            self.screen.blit(en, (x_coord, y_coord))
            y_coord += line_distance
        if con.DEBUG.SHOW_ZOOM:
            z = con.FONTS[18].render("zoom: {}x".format(self._zoom), True, pygame.Color('white'))
            self.screen.blit(z, (x_coord, y_coord))
            y_coord += line_distance
        if con.DEBUG.SHOW_THREADS:
            st = con.FONTS[18].render("threads: {}".format(len(self.board._loading_chunks)),
                                      True, pygame.Color('white'))
            self.screen.blit(st, (x_coord, y_coord))
            y_coord += line_distance
        self.__debug_rectangle = (*debug_topleft, width, y_coord - debug_topleft[1])

    def __handle_interface_selection_events(self):
        if self.pressed(con.BOARD_KEYS.BUILDING):
            self.window_manager.add(self.building_interface)

    def __zoom_entities(self, increase):
        """
        Zoom all the entities with a certain amount of increase

        :param increase: a small number signifying the increase
        """
        prev_zoom_level = self._zoom
        self._zoom = round(min(max(0.4, self._zoom + increase), 2), 1)
        self.user.zoom = self._zoom
        # prevent unnecesairy recalculations
        if prev_zoom_level != self._zoom:
            for sprite in self.sprite_group.sprites():
                if sprite.zoomable:
                    sprite.set_zoom(self._zoom)
            con.BOARD_SIZE.width = self._zoom * con.ORIGINAL_BOARD_SIZE.width
            con.BOARD_SIZE.height = self._zoom * con.ORIGINAL_BOARD_SIZE.height
