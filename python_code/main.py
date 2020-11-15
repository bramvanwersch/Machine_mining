
#own classes
from entities import Worker, CameraCentre
from board.camera import CameraAwareLayeredUpdates
from board.board import Board
from utility.constants import *
from tasks import TaskControl
from utility.image_handling import load_images
from recipes.recipe_constants import create_recipe_book
from interfaces.building_interface import BuildingWindow
from interfaces.managers import create_window_manager
from block_classes.block_constants import configure_material_collections
import interfaces.managers as window_managers
from interfaces.interface_utility import screen_to_board_coordinate


class Main:
    START_POSITION = (BOARD_SIZE.centerx, 50)
    def __init__(self):
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 40)

        self.screen = pygame.display.set_mode(SCREEN_SIZE, DOUBLEBUF)  # | FULLSCREEN)
        self.screen.set_alpha(None)
        self.screen.fill([0,0,0])

        pygame.display.set_caption("MINING!!")
        pygame.mouse.set_visible(True)

        #load all the images before running the game
        load_images()

        #load fuel materials
        configure_material_collections()

        #load all recipes
        create_recipe_book()

        self.rect = self.screen.get_rect()
        self.camera_center = CameraCentre(self.START_POSITION, (5,5))
        self.main_sprite_group = CameraAwareLayeredUpdates(self.camera_center, BOARD_SIZE)
        self.board = Board(self.main_sprite_group)

        #load a window manager to manage window events
        create_window_manager(self.camera_center)
        from interfaces.managers import window_manager
        self.__windows = window_manager.windows

        self.user = User(self.camera_center, self.board, self.main_sprite_group)

        self.updated_rectangles = []

        self.run()

    def run(self):
        # Main Loop
        while self.user.going:
            if AIR_RECTANGLES:
                self.remove_air_rectangles()
            self.screen.fill((0, 0, 0))

            self.set_update_rectangles()
            self.user.update()
            if AIR_RECTANGLES:
                self.draw_air_rectangles()
            self.main_sprite_group.update()
            self.main_sprite_group.draw(self.screen)

            self.draw_debug_info()
            pygame.display.update(self.updated_rectangles)
            GAME_TIME.tick(200)

        pygame.quit()

    def set_update_rectangles(self):
        #get a number of rectangles that encompass the changed board state

        relative_board_start = screen_to_board_coordinate((0,0), self.main_sprite_group.target, self.user._zoom)

        #if moving or zooming update whole board
        if self.user.zoomed or self.main_sprite_group.target.moved:
            self.updated_rectangles = [self.rect]
            self.user.updated_rectangles = [pygame.Rect((self.rect.left + relative_board_start[0],
                                                        self.rect.top + relative_board_start[1], *self.rect.size))]
            return
        board_u_rects = [(5,5,75,35)]
        user_u_rects = []
        # add rectangles of visible chunks that
        for row in self.board.chunk_matrix:
            for chunk in row:
                rect = chunk.layers[0].get_update_rect()
                if rect == None:
                    continue
                user_u_rects.append(rect)

                zoom = self.user._zoom
                adjusted_rect = pygame.Rect((round((rect[0] - relative_board_start[0]) * zoom),
                                             round((rect[1] - relative_board_start[1]) * zoom),
                                             round(rect.width * zoom), round(rect.height * zoom)))
                clipped_rect = adjusted_rect.clip(self.rect)
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    board_u_rects.append(clipped_rect)
        for window in self.__windows.values():
            rect = window.orig_rect
            if not window.static:
                board_u_rects.append(window.rect)
            else:
                adjusted_rect = pygame.Rect((round((rect[0] - relative_board_start[0]) * zoom),
                                                 round((rect[1] - relative_board_start[1]) * zoom),
                                                 round(rect.width), round(rect.height)))
                clipped_rect = adjusted_rect.clip(self.rect)
                if clipped_rect.width > 0 and clipped_rect.height > 0:
                    board_u_rects.append(clipped_rect)
            user_u_rects.append(window.orig_rect)

        self.updated_rectangles = board_u_rects
        self.user.updated_rectangles = user_u_rects

    def draw_debug_info(self):
        surf = pygame.Surface((70, 30)).convert()
        surf.fill((255,255,255))
        if FPS:
            fps = FONTS[18].render("fps: {}".format(int(GAME_TIME.get_fps())), True,
                                   pygame.Color('black'))
            surf.blit(fps, (5, 5))
        if ENTITY_NMBR:
            en = FONTS[18].render("e: {}/{}".format(self.user._visible_entities, len(self.main_sprite_group.sprites())),
                                   True, pygame.Color('black'))
            surf.blit(en, (5, 15))
        self.screen.blit(surf, (10, 10))


    def draw_air_rectangles(self):
        for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
            for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
                self.board.add_rectangle(rect, (0,0,0), layer=1, border=2)

    def remove_air_rectangles(self):
        for key in self.board.pf.pathfinding_tree.rectangle_network[0]:
            for rect in self.board.pf.pathfinding_tree.rectangle_network[0][key]:
                self.board.add_rectangle(rect, INVISIBLE_COLOR, layer=1, border=2)


class User:
    def __init__(self, camera_center, board, main_sprite_group):
        #import needs to happen here since the main first has to create the object
        self.window_manager= window_managers.window_manager

        self.camera_center = camera_center
        self.board = board
        self.main_sprite_group = main_sprite_group

        self.updated_rectangles = []

        #varaible that controls the game loop
        self.going = True

        self._visible_entities = 0

        #zoom variables
        self._zoom = 1
        self.zoomed = False

        #tasks
        self.tasks = TaskControl(self.board)
        board.set_task_control(self.tasks)

        #for some more elaborate setting up of variables
        self.workers = []
        self.crafting_interface = None
        self.building_interface = None
        self.__setup_start()

    def __setup_start(self):
        start_chunk = self.board.get_start_chunk()
        appropriate_location = (int(start_chunk.START_RECTANGLE.centerx / BLOCK_SIZE.width) * BLOCK_SIZE.width + start_chunk.rect.left,
            + start_chunk.START_RECTANGLE.bottom - BLOCK_SIZE.height + + start_chunk.rect.top)
        for _ in range(5):
            self.workers.append(Worker((appropriate_location), self.board, self.tasks, self.main_sprite_group))
        #add one of the imventories of the terminal
        self.building_interface = BuildingWindow(self.board.inventorie_blocks[0].inventory, self.main_sprite_group)

        self.camera_center.rect.center = start_chunk.rect.center

    def update(self):
        self.__handle_events()
        # allow to assign values to the _layer attribute instead of calling change_layer
        for sprite in self.main_sprite_group.sprites():
            self.main_sprite_group.change_layer(sprite, sprite._layer)
        self.load_unload_sprites()

        self.board.update_board()

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
                                     sprite.orig_rect.collidelist(self.updated_rectangles ) != -1):
                sprite.show(True)
                if sprite.is_showing:
                    self._visible_entities += 1
            else:
                sprite.show(False)

    def __handle_events(self):
        events = pygame.event.get()
        cam_events = []
        leftover_events = []
        zoomed = False
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
            elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                if event.button == 4:
                    self.__zoom_entities(0.2)
                    zoomed = True
                elif event.button == 5:
                    self.__zoom_entities(-0.2)
                    zoomed = True
                else:
                    leftover_events.append(event)
            else:
                leftover_events.append(event)
        if cam_events:
            self.camera_center.handle_events(cam_events)
        self.zoomed = zoomed
        if leftover_events:
            leftover_events = self.window_manager.handle_events(leftover_events)
            self.board.handle_events(leftover_events)

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
        self._zoom = min(max(0.4, self._zoom + increase), 2)
        #prevent unnecesairy recalculations
        if prev_zoom_level != self._zoom:
            for sprite in self.main_sprite_group.sprites():
                if sprite.zoomable:
                    sprite.zoom(self._zoom)
            BOARD_SIZE.width = self._zoom * ORIGINAL_BOARD_SIZE.width
            BOARD_SIZE.height = self._zoom * ORIGINAL_BOARD_SIZE.height


if __name__ == "__main__":
    Main()