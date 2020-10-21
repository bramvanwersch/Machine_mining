
#own classes
from python_code.entities import Worker, CameraCentre
from python_code.board.camera import CameraAwareLayeredUpdates
from python_code.board.board import Board
from python_code.utility.constants import *
from python_code.tasks import TaskControl
from python_code.utility.image_handling import load_images
from python_code.recipes.base_recipes import create_recipe_book
from python_code.interfaces.building_interface import BuildingWindow
from python_code.interfaces.managers import create_window_manager
from python_code.board.materials import set_fuel_materials
import python_code.interfaces.managers as window_managers


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

        #load all recipes
        create_recipe_book()

        #load fuel materials
        set_fuel_materials()

        self.rect = self.screen.get_rect()
        self.camera_center = CameraCentre(self.START_POSITION, (5,5))
        self.main_sprite_group = CameraAwareLayeredUpdates(self.camera_center, BOARD_SIZE)
        self.board = Board(self.main_sprite_group)

        #load a window manager to manage window events
        create_window_manager(self.camera_center)

        self.user = User(self.camera_center, self.board, self.main_sprite_group)

        self.run()

    def run(self):
        # Main Loop
        while self.user.going:
            GAME_TIME.tick(200)
            pygame.display.update()
            self.user.update()
            self.screen.fill((255,255,255))

            self.main_sprite_group.update()
            self.main_sprite_group.draw(self.screen)
            if FPS:
                fps = FONTS[22].render(str(int(GAME_TIME.get_fps())), True,
                                    pygame.Color('black'))
                self.screen.blit(fps, (10, 10))
            # if AIR_RECTANGLES:
            #     self.draw_air_rectangles()
        #terminate thread to be sure
        self.board.pf.stop()
        pygame.quit()

    # def draw_air_rectangles(self):
    #     for rect in self.board.pf.calculation_thread.rectangles:
    #         pygame.draw.rect(self.board.foreground_image.image, (0,0,0), rect, 2)

class User:
    def __init__(self, camera_center, board, main_sprite_group):
        #import needs to happen here since the main first has to create the object
        self.window_manager= window_managers.window_manager

        self.camera_center = camera_center
        self.board = board
        self.main_sprite_group = main_sprite_group

        #varaible that controls the game loop
        self.going = True

        #zoom variables
        self._zoom = 1

        #tasks
        self.tasks = TaskControl(self.board)
        board.set_task_control(self.tasks)

        #for some more elaborate setting up of variables
        self.workers = []
        self.crafting_interface = None
        self.building_interface = None
        self.__setup_start()

    def __setup_start(self):
        for _ in range(10):
            #TODO find the start chink and spawn them there
            self.workers.append(Worker((600, 40), self.board, self.tasks, self.main_sprite_group))
        #add one of the imventories of the terminal
        self.building_interface = BuildingWindow(self.board.inventorie_blocks[0].inventory, self.main_sprite_group)

    def update(self):
        self.__handle_events()
        # allow to assign values to the _layer attribute instead of calling change_layer
        for sprite in self.main_sprite_group.sprites():
            self.main_sprite_group.change_layer(sprite, sprite._layer)
        self.board.pipe_network.update()

    def __handle_events(self):
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
            elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                if event.button == 4:
                    self.__zoom_entities(0.1)
                elif event.button == 5:
                    self.__zoom_entities(-0.1)
                else:
                    leftover_events.append(event)
            else:
                leftover_events.append(event)
        if cam_events:
            self.camera_center.handle_events(cam_events)
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
        if increase < 0:
            self._zoom = max(0.4, self._zoom + increase)
        elif increase > 0:
            self._zoom = min(2, self._zoom + increase)
        #prevent unnecesairy recalculations
        if prev_zoom_level != self._zoom:
            for sprite in self.main_sprite_group.sprites():
                if sprite.zoomable:
                    sprite.zoom(self._zoom)
            BOARD_SIZE.width = self._zoom * ORIGINAL_BOARD_SIZE.width
            BOARD_SIZE.height = self._zoom * ORIGINAL_BOARD_SIZE.height


if __name__ == "__main__":
    Main()