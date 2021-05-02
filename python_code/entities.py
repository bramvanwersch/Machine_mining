from abc import ABC
from itertools import count
import pygame
from typing import List, Tuple, Union, TYPE_CHECKING, Set, ClassVar

import utility.constants as con
import utility.utilities as util
from utility import image_handling
from utility import inventories
import tasks
import utility.event_handling as event_handling
if TYPE_CHECKING:
    from board.sprite_groups import CameraAwareLayeredUpdates
    import board.board
    from board.pathfinding import Path


class MySprite(pygame.sprite.Sprite, util.Serializer, ABC):
    """Surface tracked by a rectangle"""
    _layer: int
    surface: pygame.Surface
    orig_surface: pygame.Surface
    orig_rect: pygame.Rect
    _visible: bool
    zoomable: bool
    static: bool

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        size: Union[util.Size, List[int], Tuple[int, int]],
        *groups: "CameraAwareLayeredUpdates",
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (255, 255, 255),
        layer: int = con.HIGHLIGHT_LAYER,
        static: bool = True,
        visible: bool = True,
        **kwargs
    ):
        self._layer = layer
        pygame.sprite.Sprite.__init__(self, *groups)
        self.surface = self._create_surface(size, color)
        self.orig_surface = self.surface
        self.orig_rect = self.surface.get_rect(topleft=pos)
        self._visible = visible
        self.static = static  # if static do not move the entity when camera moves

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

    def show(
        self,
        value: bool
    ):
        """Toggle showing this sprite"""
        self._visible = value

    def is_showing(self) -> bool:
        """Is the sprite showing"""
        return self._visible

    def _create_surface(
        self,
        size: Union[util.Size, List[int], Tuple[int, int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]]
    ) -> pygame.Surface:
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
    def rect(self) -> pygame.Rect:
        """The original rectangle. This method is here to support zoomable entity method"""
        return self.orig_rect

    @rect.setter
    def rect(self, rect):
        """Set the orig_rect using the rect value. Support for zoomable entity"""
        self.orig_rect = rect


class ZoomableSprite(MySprite):
    """Sprite that is zoomed when the user zooms the game"""
    zoom: int

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        size: Union[util.Size, List[int], Tuple[int, int]],
        *groups: "CameraAwareLayeredUpdates",
        zoom: int = 1,
        **kwargs
    ):
        super().__init__(pos, size, *groups, **kwargs)
        self._zoom = zoom
        if self._zoom != 1:
            self.set_zoom(self._zoom)

    def set_zoom(
        self,
        zoom: int
    ):
        """Set the zoom value of this sprite"""
        self._zoom = zoom
        if self._zoom == 1:
            self.surface = self.orig_surface.copy()
        else:
            orig_rect = self.orig_rect
            new_width = round(orig_rect.width * zoom)
            new_height = round(orig_rect.height * zoom)
            self.surface = pygame.transform.scale(self.orig_surface, (int(new_width), int(new_height)))

    def set_surface(self, surface):
        self.orig_surface = surface
        self.set_zoom(self._zoom)

    @property
    def rect(self) -> pygame.Rect:
        """Returns a rectangle that represents the zoomed version of the self.orig_rect"""
        if self._zoom == 1:
            return self.orig_rect
        orig_pos = list(self.orig_rect.center)
        orig_pos[0] = round(orig_pos[0] * self._zoom)
        orig_pos[1] = round(orig_pos[1] * self._zoom)
        rect = self.surface.get_rect(center=orig_pos)
        return rect

    @rect.setter
    def rect(self, rect):
        self.orig_rect = rect


class SelectionRectangle(ZoomableSprite):
    """Creates a rectangle by draging the mouse. To highlight certain areas."""
    __start_pos: List[int]
    __prev_screen_pos: List[int]
    __size: util.Size

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        size: Union[util.Size, List[int], Tuple[int, int]],
        mouse_pos: Union[Tuple[int, int], List[int]],
        *groups: "CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, size, *groups, **kwargs)
        self.__start_pos = list(pos)
        self.__prev_screen_pos = list(mouse_pos)
        self.__size = util.Size(*size)
        self.__update_image()

    def to_dict(self):
        return

    def __update_image(self):
        """Update the rectangle image that represents the highlighted area."""
        pos = self.__start_pos.copy()
        size = self.__size.size
        if self.__size.width < 0:
            pos[0] += self.__size.width
            size[0] = -1 * self.__size.width
        if self.__size.height < 0:
            pos[1] += self.__size.height
            size[1] = -1 * self.__size.height
        self.surface = pygame.Surface(size).convert_alpha()
        self.surface.fill((255, 255, 255, 100))
        self.orig_rect = self.surface.get_rect(topleft=pos)

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
        # figure out the distance the mouse was moved compared to the previous position
        x_move = pygame.mouse.get_pos()[0] - self.__prev_screen_pos[0]
        y_move = pygame.mouse.get_pos()[1] - self.__prev_screen_pos[1]
        self.__prev_screen_pos[0] += x_move
        self.__prev_screen_pos[1] += y_move

        # adjust the size to be of orig_board coordinate size sinze the mouse screen position is in zoomed sizes.
        self.__size.width += x_move / self._zoom
        self.__size.height += y_move / self._zoom

        if not x_move == y_move == 0:
            self.__update_image()


class MovingEntity(ZoomableSprite):
    """Base class for moving entities that have a move method to """
    max_speed: int
    speed: pygame.Vector2
    __exact_movement_values: List[float]

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        size: Union[util.Size, List[int], Tuple[int, int]],
        max_speed: int,
        *groups: "CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, size, *groups, **kwargs)
        self.max_speed = max_speed  # in pixels per second moved
        self.speed = pygame.Vector2(0, 0)
        self.__exact_movement_values = [0, 0]

    def to_dict(self):
        return super().to_dict().update({
            "max_speed": self.max_speed,
            "speed": (self.speed.x, self.speed.y)
        })

    def _max_frame_speed(self) -> float:
        """Return the maximum speed over this frame, depending on the max_speed and time spent on this frame

        This allows inheriting classes to define movement without collision checks
        """
        elapsed_time = con.GAME_TIME.get_time()
        return (elapsed_time / 1000) * self.max_speed

    def update(self, *args):
        """
        Move every update
        """
        super().update(*args)
        self.move()

    def move(self):
        """Move if the exact tracked movement is more than 1"""
        x, y = self._collision_adjusted_values()
        self.__exact_movement_values[0] += x - self.orig_rect.centerx
        self.__exact_movement_values[1] += y - self.orig_rect.centery
        while abs(self.__exact_movement_values[0]) > 1:
            if self.__exact_movement_values[0] > 0:
                self.orig_rect.centerx += 1
                self.__exact_movement_values[0] -= 1
            else:
                self.orig_rect.centerx -= 1
                self.__exact_movement_values[0] += 1
        while abs(self.__exact_movement_values[1]) > 1:
            if self.__exact_movement_values[1] > 0:
                self.orig_rect.centery += 1
                self.__exact_movement_values[1] -= 1
            else:
                self.orig_rect.centery -= 1
                self.__exact_movement_values[1] += 1

    def _collision_adjusted_values(self) -> Tuple[float, float]:
        """Get a new x an y value that are inside the board"""
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
    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        size: Union[util.Size, List[int], Tuple[int, int]],
        *groups: "CameraAwareLayeredUpdates",
        **kwargs
    ):
        MovingEntity.__init__(self, pos, size, 1000, *groups, **kwargs)
        event_handling.EventHandler.__init__(self, [con.RIGHT, con.LEFT, con.UP, con.DOWN])

    def handle_events(
        self,
        events: List["pygame.event.Event"],
        consume_events: bool = True
    ) -> List["pygame.event.Event"]:
        """Handle events for moving the camera around the board"""
        leftover_events = event_handling.EventHandler.handle_events(self, events)
        max_frame_speed = self._max_frame_speed()
        if self.pressed(con.RIGHT, continious=True) and self.pressed(con.LEFT, continious=True):
            self.speed.x = 0
        else:
            if self.pressed(con.RIGHT, continious=True):
                self.speed.x = min(max_frame_speed, self.speed.x + max_frame_speed)
            if self.pressed(con.LEFT, continious=True):
                self.speed.x = max(-max_frame_speed, self.speed.x - max_frame_speed)
            if not self.pressed(con.LEFT, continious=True) and not self.pressed(con.RIGHT, continious=True):
                self.speed.x = 0
        if self.pressed(con.DOWN, continious=True) and self.pressed(con.UP, continious=True):
            self.speed.y = 0
        else:
            if self.pressed(con.UP, continious=True):
                self.speed.y = max(-max_frame_speed, self.speed.y - max_frame_speed)
            if self.pressed(con.DOWN, continious=True):
                self.speed.y = min(max_frame_speed, self.speed.y + max_frame_speed)
            if not self.pressed(con.UP, continious=True) and not self.pressed(con.DOWN, continious=True):
                self.speed.y = 0
        return leftover_events


class Worker(MovingEntity, util.ConsoleReadable):
    """
    A worker class that can perform tasks
    """
    SIZE: ClassVar[Union[Tuple[int, int], List[int], util.Size]] = (20, 20)
    INVENTORY_SIZE: ClassVar[int] = 2  # in wheight
    NUMBER: ClassVar[int] = count(1, 1)
    VISON_RADIUS: ClassVar[int] = 8 * con.BLOCK_SIZE.width
    EMITTED_LIGTH: ClassVar[int] = 10
    WORKER_IMAGES: ClassVar[List[image_handling.ImageDefinition]] = \
        [image_handling.ImageDefinition("general", (0, 40), size=util.Size(20, 20), image_size=util.Size(20, 20),
                                        flip=(True, False)),
         image_handling.ImageDefinition("general", (20, 40), size=util.Size(20, 20), image_size=util.Size(20, 20),
                                        flip=(True, False)),
         image_handling.ImageDefinition("general", (40, 40), size=util.Size(20, 20), image_size=util.Size(20, 20),
                                        flip=(True, False)),
         image_handling.ImageDefinition("general", (60, 40), size=util.Size(20, 20), image_size=util.Size(20, 20),
                                        flip=(True, False))
         ]

    number: int
    board: Union["board.board.Board", None]
    task_control: Union[tasks.TaskControl, None]
    task_queue: tasks.TaskQueue
    path: Union[List, "Path"]
    dest: Union[List[List[int]], None]
    inventory: inventories.Inventory
    __previous_x_direction: int
    __turn_rigth_animation: image_handling.Animation
    __turn_left_animation: image_handling.Animation

    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        *groups: "CameraAwareLayeredUpdates",
        board_: Union["board.board.Board", None] = None,
        task_control: Union["tasks.TaskControl", None] = None,
        **kwargs
    ):
        MovingEntity.__init__(self, pos, self.SIZE, 150, *groups, **kwargs)
        self.number = next(Worker.NUMBER)
        self.board = board_
        self.task_control = task_control

        # tasks
        self.task_queue = tasks.TaskQueue()
        self.path = []
        self.dest = None

        # inventory
        self.inventory = inventories.Inventory(self.INVENTORY_SIZE)
        self.__previous_x_direction = -1

        # for loading purposes
        if self.board:
            self.board.adjust_lighting(self.orig_rect.center, self.VISON_RADIUS, self.EMITTED_LIGTH)

        self.__turn_rigth_animation = image_handling.Animation([self.WORKER_IMAGES[0].images()[0],
                                                                self.WORKER_IMAGES[1].images()[0],
                                                                self.WORKER_IMAGES[2].images()[0],
                                                                self.WORKER_IMAGES[3].images()[0],
                                                                self.WORKER_IMAGES[2].images()[1],
                                                                self.WORKER_IMAGES[1].images()[1],
                                                                self.WORKER_IMAGES[0].images()[1]], 15)
        self.__turn_left_animation = image_handling.Animation([self.WORKER_IMAGES[0].images()[1],
                                                               self.WORKER_IMAGES[1].images()[1],
                                                               self.WORKER_IMAGES[2].images()[1],
                                                               self.WORKER_IMAGES[3].images()[1],
                                                               self.WORKER_IMAGES[2].images()[0],
                                                               self.WORKER_IMAGES[1].images()[0],
                                                               self.WORKER_IMAGES[0].images()[0]], 15)
        from interfaces import worker_interface
        from interfaces.managers import game_window_manager

        self.window_manager = game_window_manager
        self.interface = worker_interface.WorkerWindow(pygame.Rect(self.orig_rect.left, self.orig_rect.bottom, 300,
                                                                   400), self, *groups)

    def _create_surface(
        self,
        size: Union[util.Size, List[int], Tuple[int, int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]]
    ) -> pygame.Surface:
        return self.WORKER_IMAGES[0].images()[0]

    def open_interface(self):
        if self.window_manager is None:
            from interfaces.managers import game_window_manager
            self.window_manager = game_window_manager
        self.window_manager.add(self.interface)
        self.interface.set_location(self.orig_rect.bottomleft)

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
        # only move when a full block is moved
        if int(pre_move_loc[0] / con.BLOCK_SIZE.width) != int(self.orig_rect.centerx / con.BLOCK_SIZE.width) or \
                int(pre_move_loc[1] / con.BLOCK_SIZE.height) != int(self.orig_rect.centery / con.BLOCK_SIZE.height):
            self.board.adjust_lighting(self.orig_rect.center, self.VISON_RADIUS, 10)

    def __perform_commands(self):
        """Perform commands issued by the user"""
        # as long as there is a path or the entity is still moving keep moving
        if not len(self.path) == self.speed.x == self.speed.y == 0:
            self.__move_along_path()
        # perform a task if available
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
            if task is not None:
                self.task_queue.add(task)
            elif not self.inventory.empty:
                self.task_queue.add(tasks.EmptyInventoryTask(self))

    def __start_task(self):
        self.task_queue.task.start(self)
        if self.task_queue.task.block is None:
            self.task_queue.task.cancel()
            self.__next_task()
        else:
            path = self.board.pathfinding.get_path(self.orig_rect, self.task_queue.task.block.rect)
            if path is not None:
                self.path = path
            else:
                self.task_queue.task.cancel()
                self.__next_task()

    # task management functions:
    def __next_task(self):

        f_task, f_block = self.task_queue.next()
        # make sure that the entity stops when the task is sudenly finshed
        self.speed.x = self.speed.y = 0
        # make sure to move the last step if needed, so the worker does not potentially stop in a block
        if len(self.path) > 0:
            self.path = self.path[-1]
        if f_task.canceled():
            f_task.uncancel()
        elif not f_task.handed_in():
            f_task.hand_in(self)
            self.task_control.remove_tasks(f_task)

    def __perform_task(self):
        """Perform a given task and finish it if that is the case"""
        self.task_queue.task.task_progress[0] += con.GAME_TIME.get_time()
        if self.task_queue.task.finished:
            self.__next_task()

    def __move_along_path(self):
        """move along the self.path"""

        if self.__run_animation() is True:
            return

        if self.speed.x == self.speed.y == 0:
            self.dest = self.path.pop()

        # x move
        max_frame_speed = self._max_frame_speed()
        x_direction = self.__previous_x_direction
        if self.orig_rect.x < self.dest[0][0]:
            self.speed.x = min(max_frame_speed, self.dest[0][0] - self.orig_rect.x)
            x_direction = 1
        elif self.orig_rect.x > self.dest[0][1]:
            self.speed.x = max(- max_frame_speed, self.dest[0][1] - self.orig_rect.x)
            x_direction = -1
        else:
            self.speed.x = 0

        # y move
        if self.orig_rect.y < self.dest[1][0]:
            self.speed.y = min(max_frame_speed, self.dest[1][0] - self.orig_rect.y)
        elif self.orig_rect.y > self.dest[1][1]:
            self.speed.y = max(- max_frame_speed, self.dest[1][1] - self.orig_rect.y)
        else:
            self.speed.y = 0

        self.__check_animation_start(x_direction)

    def __check_animation_start(
        self,
        x_direction: int
    ):
        if x_direction != self.__previous_x_direction:
            self.__previous_x_direction = x_direction
            if x_direction == -1:
                self.__turn_left_animation.start()
            else:
                self.__turn_rigth_animation.start()
            self.path.append(self.dest)
            self.speed.x = self.speed.y = 0

    def __run_animation(self) -> bool:
        if self.__turn_left_animation.active:
            self.__turn_left_animation.update()
            if self.__turn_left_animation.new_frame_started:
                self.set_surface(self.__turn_left_animation.current_image())
            return True
        elif self.__turn_rigth_animation.active:
            self.__turn_rigth_animation.update()
            if self.__turn_rigth_animation.new_frame_started:
                self.set_surface(self.__turn_rigth_animation.current_image())
            return True
        return False


class TextSprite(ZoomableSprite):
    """
    Entity for drawing text on the screen
    """

    TOTAL_LIFE_SPAN: ClassVar[int] = 1000  # in ms
    FONT: ClassVar[int] = 30

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
        color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]] = (255, 18, 18, 150),
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
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]]
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
