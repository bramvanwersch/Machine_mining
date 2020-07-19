import os, sys

#sys.path.append(dirname(__file__))

#own classes
from python_code.entities import Worker, CameraCentre, SelectionRectangle, InputSaver, TextSprite
from python_code.camera import CameraAwareLayeredUpdates
from python_code.board import Board
from python_code.utilities import rect_from_block_matrix
from python_code.constants import *
from python_code.tasks import TaskControl
from python_code.image_handling import load_images
from python_code.crafting import CraftingInterface


class Main:
    START_POSITION = (BOARD_SIZE.centerx, 50)
    def __init__(self):
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 40)

        self.screen = pygame.display.set_mode(SCREEN_SIZE, DOUBLEBUF)  # | FULLSCREEN)
        self.screen.set_alpha(None)
        self.screen.fill([0,0,0])
        self.font = pygame.font.SysFont("arial", 18)

        pygame.display.set_caption("MINING!!")
        pygame.mouse.set_visible(True)

        #load all the images before running the game
        load_images()

        self.rect = self.screen.get_rect()
        self.camera_center = CameraCentre(self.START_POSITION, (5,5))
        self.main_sprite_group = CameraAwareLayeredUpdates(self.camera_center, BOARD_SIZE)
        self.board = Board(self.main_sprite_group)

        # make sure to configure the layers so that the sprites are correctly made
        for sprite in self.main_sprite_group.sprites():
            self.main_sprite_group.change_layer(sprite, sprite._layer)

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
                fps = self.font.render(str(int(GAME_TIME.get_fps())), True,
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
        self.camera_center = camera_center
        self.board = board
        self.main_sprite_group = main_sprite_group

        #varaible that controls the game loop
        self.going = True

        #the entity that is selected and going to receive the left over events
        self.event_handler_entity = self.board

        #zoom variables
        self._zoom = 1

        #selecting rectangle variables
        self.__draging = False
        self.__selection_rectangle = None

        #hightlight rectange
        self.__highlight_rectangle = None

        #modes
        self.__mode = MODES[SELECTING]
        self.font = pygame.font.SysFont("arial", 18)

        #tasks
        self.tasks = TaskControl(self.board)

        #for some more elaborate setting up of variables
        self.workers = []
        self.crafting_interface = None
        self.__setup_start()

    def __setup_start(self):
        for _ in range(10):
            self.workers.append(Worker((1000, 40), self.board, self.tasks, self.main_sprite_group))
        self.crafting_interface = CraftingInterface(self.main_sprite_group)

    def update(self):
        self.__handle_events()

    def __handle_events(self):
        events = pygame.event.get()
        cam_events = []
        leftover_events = []
        for event in events:
            if event.type == QUIT:
                self.going = False
            elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                if self.__handle_mouse_events(event):
                    leftover_events.append(event)
            elif (event.type == KEYDOWN or event.type == KEYUP) and\
                    event.key in CAMERA_KEYS:
                cam_events.append(event)
            elif event.type == KEYDOWN and event.key in MODE_KEYS:
                #when the event was not processed add it to the leftovers
                if self.__handle_mode_events(event):
                    leftover_events.append(event)
            elif event.type == KEYDOWN and event.key in INTERFACE_KEYS:
                if self.__handle_interface_selection_events(event):
                    leftover_events.append(event)


        if cam_events:
            self.camera_center.handle_events(cam_events)
        if leftover_events:
            self.event_handler_entity.handle_events(leftover_events)

#handeling of events
    def __handle_mouse_events(self, event):
        """
        Handle mouse events issued by the user.

        :param event: a pygame event
        :return: an event when the event was not processed otherwise None
        """
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.__draging = True
            mouse_pos = self.__screen_to_board_coordinate(event.pos)
            #should the highlighted area stay when a new one is selected
            if not self.__mode.persistent_highlight and self.__highlight_rectangle != None:
                self.board.add_rectangle(INVISIBLE_COLOR, self.__highlight_rectangle, layer = 1)
            self.__selection_rectangle = SelectionRectangle(mouse_pos,
                                    (0, 0), event.pos, self.main_sprite_group,
                                     zoom=self._zoom)
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.__draging = False
            self.__process_selection(self.__selection_rectangle.orig_rect)
            self.__selection_rectangle.kill()
        elif event.button == 4:
            self.__zoom_entities(0.1)
        elif event.button == 5:
            self.__zoom_entities(-0.1)
        else:
            return event

    def __handle_mode_events(self, event):
        """
        Change the mode of the user and draw some text to notify the user.

        :param event: a pygame event
        """
        #make sure to clear the rectangle before switching if needed
        if not self.__mode.persistent_highlight and self.__highlight_rectangle != None:
            self.board.add_rectangle(INVISIBLE_COLOR, self.__highlight_rectangle, layer=1)

        self.__mode = MODES[event.key]

        text = "{} mode".format(self.__mode.name)
        size = self.font.size(text)

        pos = self.__screen_to_board_coordinate(SCREEN_SIZE.center)
        # center at the center of the screen
        pos[0] -=0.5 * size[0]

        TextSprite(pos, size, text, self.font, self.main_sprite_group,
                   zoom=self._zoom)

    def __handle_interface_selection_events(self, event):
        if event.key == CRAFTING:
            self.event_handler_entity = self.crafting_interface
            self.crafting_interface.show(True)
        elif event.key == K_ESCAPE:
            self.event_handler_entity = self.board
            self.crafting_interface.show(False)
        else:
            return event

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
                sprite.zoom(self._zoom)
            BOARD_SIZE.width = self._zoom * ORIGINAL_BOARD_SIZE.width
            BOARD_SIZE.height = self._zoom * ORIGINAL_BOARD_SIZE.height

    def __process_selection(self, rect):
        blocks = self.board.overlapping_blocks(rect)
        #the user is selecting blocks
        if len(blocks) > 0:
            self.__draw_selection(blocks)
            self.__add_tasks(blocks)
        # the user selected a selectable entity
        else:
            selected_sprit = None
            # select the first sprite clicked or otherwise select the board
            for sprite in self.main_sprite_group.sprites():
                if isinstance(sprite, InputSaver) and \
                        sprite.orig_rect.collidepoint(rect.center) \
                        and sprite != self.board:
                    selected_sprit = sprite
                    break
                else:
                    selected_sprit = self.board
            self.event_handler_entity.selected = False
            self.event_handler_entity = selected_sprit
            selected_sprit.selected = True

    def __draw_selection(self, blocks):
        """
        Draw the selection on the board highlight layer

        :param blocks: A matrix of blocks
        """
        #draw only over rectangles that are not air blocks
        if self.__mode.name == "Mining":
            self.board.highlight_taskable_blocks(self.__mode.color, blocks, "Mining")
        else:
            rect = rect_from_block_matrix(blocks)
            self.board.add_rectangle(self.__mode.color, rect, layer = 1)
            self.__highlight_rectangle = rect

    def __screen_to_board_coordinate(self, coord):
        """
        Calculate the screen to current board size coordinate. That is the
        zoomed in board. Then revert the coordinate back to the normal screen

        :param coord: a coordinate with x and y value within the screen region
        :return: a coordinate with x and y vale within the ORIGINAL_BOARD_SIZE.

        The value is scaled back to the original size after instead of
        being calculated as the original size on the spot because the screen
        coordinate can not be converted between zoom levels so easily.
        """
        c = self.main_sprite_group.target.rect.center
        #last half a screen of the board
        if BOARD_SIZE.width - c[0] - SCREEN_SIZE.width / 2 < 0:
            x = BOARD_SIZE.width - (SCREEN_SIZE.width - coord[0])
        #the rest of the board
        elif c[0] - SCREEN_SIZE.width / 2 > 0:
            x = coord[0] + (c[0] - SCREEN_SIZE.width / 2)
        #first half a screen of the board
        else:
            x = coord[0]
        if BOARD_SIZE.height - c[1] - SCREEN_SIZE.height / 2 < 0:
            y = BOARD_SIZE.height - (SCREEN_SIZE.height - coord[1])
        elif c[1] - SCREEN_SIZE.height / 2 > 0:
            y = coord[1] + (c[1] - SCREEN_SIZE.height / 2)
        else:
            y = coord[1]
        return [int(x / self._zoom), int(y / self._zoom)]

#task management

    def __add_tasks(self, blocks):
        if self.__mode.name == "Mining":
            self.tasks.add(self.__mode.name, blocks)
        elif self.__mode.name == "Cancel":
            rect = rect_from_block_matrix(blocks)
            #remove highlight
            self.board.add_rectangle(INVISIBLE_COLOR, rect, layer = 1)
            for row in blocks:
                for block in row:
                    block.tasks = {}
                self.tasks.remove(*row)


if __name__ == "__main__":
    Main()