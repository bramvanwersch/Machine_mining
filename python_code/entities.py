from abc import ABC
from itertools import count
import pygame
from typing import List, Tuple, Union, TYPE_CHECKING, Set

import utility.constants as con
import utility.utilities as util
from utility import inventories
import tasks
import utility.event_handling as event_handling
if TYPE_CHECKING:
    from board.sprite_groups import CameraAwareLayeredUpdates


class MySprite(pygame.sprite.Sprite, util.Serializer, ABC):
    """
    Basic entity class is a sprite with an image.
    """
    COLOR = (255, 255, 255)

    def __init__(self, pos, size, *groups, color=COLOR, layer=con.HIGHLIGHT_LAYER, static=True, zoomable=False,
                 visible=True, **kwargs):
        self._layer = layer
        pygame.sprite.Sprite.__init__(self, *groups)
        self.surface = self._create_surface(size, color)
        self.orig_surface = self.surface
        self.orig_rect = self.surface.get_rect(topleft=pos)
        self._visible = visible
        self.zoomable = zoomable
        # should the entity move with the camera or not
        self.static = static

    def to_dict(self):
        return {
            "pos": self.orig_rect.topleft,
            "size": self.orig_rect.size,
            "layer": self._layer,
            "static": self.static,
            "zoomable": self.zoomable,
            "visible": self._visible
        }

    @classmethod
    def from_dict(cls, **arguments):
        return super().from_dict(
            type=cls.__name__,
            **arguments,
        )

    def show(self, value: bool):
        self._visible = value

    def is_showing(self):
        return self._visible

    def _create_surface(self, size, color):
        """Create the innitial surface forn this entity"""
        if len(color) == 3:
            image = pygame.Surface(size).convert()
        # included alpha channel
        elif len(color) == 4:
            image = pygame.Surface(size).convert_alpha()
        else:
            raise util.GameException(f"Invalid color argument of length {len(color)} supplied")
        image.fill(color)
        return image

    @property
    def rect(self):
        """
        The original rectangle. This method is here to support zoomable entity
        method

        :return pygame Rect object
        """
        return self.orig_rect

    @rect.setter
    def rect(self, rect):
        """
        Set the orig_rect using the rect value. Support for zoomable entity

        :param rect: a pygame Rect object
        """
        self.orig_rect = rect


class ZoomableSprite(MySprite):
    """
    Basic zoomable entity class
    """
    def __init__(self, pos, size, *groups, zoom=1, **kwargs):
        MySprite.__init__(self, pos, size, *groups, zoomable=True, **kwargs)
        # zoom variables
        self._zoom = zoom
        # if an entity is created after zooming make sure it is zoomed to the
        # right proportions
        if self._zoom != 1:
            self.set_zoom(self._zoom)

    def set_zoom(self, zoom):
        """
        Safe a zoom value so distance measures know how to change, also change
        the image size to make sure that this is not done every request.

        :param increase: a small integer that tells how much bigger the zoom
        should be
        """
        self._zoom = zoom
        if self._zoom == 1:
            self.surface = self.orig_surface.copy()
        else:
            orig_rect = self.orig_rect
            new_width = round(orig_rect.width * zoom)
            new_height = round(orig_rect.height * zoom)
            self.surface = pygame.transform.scale(self.orig_surface, (int(new_width), int(new_height)))

    @property
    def rect(self):
        """
        Returns a rectangle that represents the zoomed version of the
        self.orig_rect

        :return: a pygame Rect object
        """
        if self._zoom == 1:
            return self.orig_rect
        orig_pos = list(self.orig_rect.center)
        orig_pos[0] = round(orig_pos[0] * self._zoom)
        orig_pos[1] = round(orig_pos[1] * self._zoom)
        rect = self.surface.get_rect(center = orig_pos)
        return rect

    @rect.setter
    def rect(self, rect):
        self.orig_rect = rect


class SelectionRectangle(ZoomableSprite):
    """
    Creates a rectangle by draging the mouse. To highlight certain areas.
    """
    def __init__(self, pos, size, mouse_pos, *groups, **kwargs):
        ZoomableSprite.__init__(self, pos, size, *groups, **kwargs)
        self.__start_pos = list(pos)
        self.__prev_screen_pos = list(mouse_pos)
        self.__size = util.Size(*size)
        self.__update_image()

    def to_dict(self):
        return super().to_dict().update({
            "mouse_pos": self.__prev_screen_pos,
        })

    def __update_image(self):
        """
        Update the rectangle image that represents a highlighted area.
        """
        pos = self.__start_pos.copy()
        size = self.__size.size
        if self.__size.width < 0:
            pos[0] += self.__size.width
            size[0] = -1 * self.__size.width
        if self.__size.height < 0:
            pos[1] += self.__size.height
            size[1] = -1 * self.__size.height
        self.surface = pygame.Surface(size).convert_alpha()
        self.surface.fill((255,255,255,100))
        self.orig_rect = self.surface.get_rect(topleft = pos)

        self.orig_surface = self.surface
        # make sure to update the zoomed image aswell
        self.set_zoom(self._zoom)

    def update(self, *args):
        """
        Remake the rectangle that is being highlighted every update
        """
        super().update(*args)
        self.__remake_rectangle()

    def __remake_rectangle(self):
        """
        Every update recalculate if the size of the rectangle should change
        """
        #figure out the distance the mouse was moved compared to the previous
        #position
        x_move = pygame.mouse.get_pos()[0] - self.__prev_screen_pos[0]
        y_move = pygame.mouse.get_pos()[1] - self.__prev_screen_pos[1]
        self.__prev_screen_pos[0] += x_move
        self.__prev_screen_pos[1] += y_move

        #adjust the size to be of orig_board coordinate size sinze the mouse
        #screen position is in zoomed sizes.
        self.__size.width += x_move / self._zoom
        self.__size.height += y_move / self._zoom

        if not x_move == y_move == 0:
            self.__update_image()


class MovingEntity(ZoomableSprite):
    """
    Base class for moving entities
    """
    MAX_SPEED = 10  # pixels/s

    def __init__(self, pos, size, *groups, max_speed=MAX_SPEED, speed=None, **kwargs):
        ZoomableSprite.__init__(self, pos, size, *groups, **kwargs)
        self.max_speed = max_speed
        self.speed = pygame.Vector2(*speed) if speed else pygame.Vector2(0, 0)

    def to_dict(self):
        return super().to_dict().update({
            "max_speed": self.max_speed,
            "speed": (self.speed.x, self.speed.y)
        })

    def update(self, *args):
        """
        Move every update
        """
        super().update(*args)
        self.move()

    def move(self):
        """
        Method for moving something based on an x and y speed
        """
        x, y = self._collision_adjusted_values()
        self.orig_rect.centerx = x

        self.orig_rect.centery = y

    def _collision_adjusted_values(self):
        """
        Adjust the movement values to be inside the board when needed
        :return: new x and y
        """
        new_centerx = max(0.5 * self.orig_rect.width,
                          min(self.orig_rect.centerx + self.speed.x,
                              con.ORIGINAL_BOARD_SIZE.width - 0.5 * self.orig_rect.width))

        new_centery = max(0.5 * self.orig_rect.height,
                          min(self.orig_rect.centery + self.speed.y,
                              con.ORIGINAL_BOARD_SIZE.height - 0.5 * self.orig_rect.height))
        return new_centerx, new_centery


class CameraCentre(MovingEntity, event_handling.EventHandler):
    """
    The camera center where the camera centers on
    """
    def __init__(self, pos, size, *groups, **kwargs):
        MovingEntity.__init__(self, pos, size, *groups, max_speed = 20, **kwargs)
        event_handling.EventHandler.__init__(self, [con.RIGHT, con.LEFT, con.UP, con.DOWN])
        self.orig_rect = pygame.Rect(*pos, *size)

    def handle_events(self, events):
        """
        Handle events for moving the camera around the board
        """
        leftover_events = event_handling.EventHandler.handle_events(self, events)
        if self.pressed(con.RIGHT, continious=True) and self.pressed(con.LEFT, continious=True):
            self.speed.x = 0
        else:
            if self.pressed(con.RIGHT, continious=True):
                self.speed.x = min(self.max_speed, self.speed.x + self.max_speed)
            if self.pressed(con.LEFT, continious=True):
                self.speed.x = max(-self.max_speed, self.speed.x - self.max_speed)
            if not self.pressed(con.LEFT, continious=True) and not self.pressed(con.RIGHT, continious=True):
                self.speed.x = 0
        if self.pressed(con.DOWN, continious=True) and self.pressed(con.UP, continious=True):
            self.speed.y = 0
        else:
            if self.pressed(con.UP, continious=True):
                self.speed.y = max(-self.max_speed, self.speed.y - self.max_speed)
            if self.pressed(con.DOWN, continious=True):
                self.speed.y = min(self.max_speed, self.speed.y + self.max_speed)
            if not self.pressed(con.UP, continious=True) and not self.pressed(con.DOWN, continious=True):
                self.speed.y = 0
        return leftover_events


class Worker(MovingEntity, util.ConsoleReadable):
    """
    A worker class that can perform tasks
    """
    COLOR = (255, 0, 0, 100)
    SIZE = (10, 10)
    # in wheight
    INVENTORY_SIZE = 2
    NUMBER = count(1, 1)
    VISON_RADIUS = 80
    EMITTED_LIGTH = 10

    def __init__(self, pos, *groups, board=None, task_control=None, **kwargs):
        MovingEntity.__init__(self, pos, self.SIZE, *groups, color=self.COLOR, max_speed=5, **kwargs)
        self.number = next(Worker.NUMBER)
        self.board = board
        self.task_control = task_control

        # tasks
        self.task_queue = tasks.TaskQueue()
        self.path = []
        self.dest = None

        # inventory
        self.inventory = inventories.Inventory(self.INVENTORY_SIZE)

        # for loading purposes
        if self.board:
            self.board.adjust_lighting(self.orig_rect.center, self.VISON_RADIUS, self.EMITTED_LIGTH)

    def printables(self) -> Set[str]:
        attributes = super().printables()
        attributes.remove("board")
        attributes.remove("task_control")
        attributes.remove("surface")
        attributes.remove("orig_surface")
        return attributes

    def update(self, *args):
        """
        Perform a task when avaialable
        """
        MovingEntity.update(self, *args)
        self.__perform_commands()

    def move(self):
        pre_move_loc = self.orig_rect.center
        super().move()
        if pre_move_loc != self.orig_rect.center:
            self.board.adjust_lighting(self.orig_rect.center, self.VISON_RADIUS, 10)

    def __perform_commands(self):
        """
        Perform commands issued by the user. This function shows the priority
        of certain commands.
        """
        #as long as there is a path or the entity is still moving keep moving
        if not len(self.path) == self.speed.x == self.speed.y == 0:
            self.__move_along_path()
        #perform a task if available
        elif not self.task_queue.empty():
            if self.task_queue.task.canceled():
                self.__next_task()
            elif not self.task_queue.task.started_task:
                self.__start_task()
            else:
                self.__perform_task()
        elif self.inventory.full:
            self.task_queue.add(tasks.EmptyInventoryTask(self))
        elif self.task_queue.empty():
            task = self.task_control.get_task(self.rect.center)
            if task != None:
                self.task_queue.add(task)
            elif not self.inventory.empty:
                self.task_queue.add(tasks.EmptyInventoryTask(self))

    def __start_task(self):
        self.task_queue.task.start(self)
        if self.task_queue.task.block == None:
            self.task_queue.task.cancel()
            self.__next_task()
        else:
            path = self.board.pathfinding.get_path(self.orig_rect, self.task_queue.task.block.rect)
            if path != None:
                self.path = path
            else:
                self.task_queue.task.cancel()
                self.__next_task()

    ##task management functions:
    def __next_task(self):

        f_task, f_block = self.task_queue.next()
        # make sure that the entity stops when the task is sudenly finshed
        self.speed.x = self.speed.y = 0
        #make sure to move the last step if needed, so the worker does not potentially stop in a block
        if len(self.path) > 0:
            self.path = self.path[-1]
        if f_task.canceled():
            f_task.uncancel()
        elif not f_task.handed_in():
            f_task.hand_in(self)
            self.task_control.remove_tasks(f_task)

    def __perform_task(self):
        """
        Perform a given task and finish it if that is the case
        """
        self.task_queue.task.task_progress[0] += con.GAME_TIME.get_time()
        if self.task_queue.task.finished:
            self.__next_task()

    def __move_along_path(self):
        """
        move along the self.path
        """
        if self.speed.x == self.speed.y == 0:
            self.dest = self.path.pop()

        #x move
        if self.orig_rect.x < self.dest[0]:
            self.speed.x = min(self.max_speed, self.dest[0] - self.orig_rect.x)
        elif self.orig_rect.x > self.dest[0]:
            self.speed.x = max(- self.max_speed, self.dest[0] - self.orig_rect.x)
        #destination achieved
        else:
            self.speed.x = 0

        #y move
        if self.orig_rect.y < self.dest[1]:
            self.speed.y = min(self.max_speed, self.dest[1] - self.orig_rect.y)
        elif self.orig_rect.y > self.dest[1]:
            self.speed.y = max(- self.max_speed, self.dest[1] - self.orig_rect.y)
        else:
            self.speed.y = 0

        #check for collision
        if not self.board.transparant_collide((self.orig_rect.centerx + self.speed.x, self.orig_rect.centery)):
            self.speed.x = 0
        if not self.board.transparant_collide((self.orig_rect.centerx, self.orig_rect.centery + self.speed.y)):
            self.speed.y = 0


class TextSprite(ZoomableSprite):
    """
    Entity for drawing text on the screen
    """

    TOTAL_LIFE_SPAN = 1000  # in ms
    FONT = 30
    COLOR = (255, 18, 18, 150)

    text: str
    __font_size: int
    __color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]]
    lifespan: List[int]

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        text: str,
        *groups: "CameraAwareLayeredUpdates",
        font: int = FONT,
        color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]] = COLOR,
        lifespan: int = TOTAL_LIFE_SPAN,
        **kwargs
    ):
        self.text = text
        self.__font_size = font
        self.__color = color
        size = con.FONTS[self.__font_size].size(self.text)
        pos[0] -= int(size[0] / 2)
        pos[1] -= int(size[1] / 2)
        super().__init__(pos, size, *groups, layer=con.TOOLTIP_LAYER, **kwargs)
        self.lifespan = [0, lifespan]

    def _create_surface(
        self,
        size: Union[util.Size, List[int], Tuple[int, int]],
        color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]],
    ) -> pygame.Surface:
        """Create some tect using a string, font and color"""
        image = con.FONTS[self.__font_size].render(self.text, False, self.__color)

        # blit transparant text
        if len(self.__color) == 4:
            back_image = pygame.Surface(size)
            back_image.fill(con.INVISIBLE_COLOR)
            back_image.blit(image, (0, 0))
            back_image.set_colorkey(con.INVISIBLE_COLOR, pygame.RLEACCEL)
            back_image.set_alpha(self.__color[3])
            back_image = back_image.convert_alpha()
            image = back_image
        return image

    def update(self, *args):
        """
        Decrease the lifespan of the text making sure that is dies after around
        a second.
        """
        super().update(*args)
        self.lifespan[0] += con.GAME_TIME.get_time()
        if self.lifespan[0] >= self.lifespan[1]:
            self.kill()
