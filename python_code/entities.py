from abc import ABC, abstractmethod

from python_code.constants import *
from python_code.inventories import Inventory
from python_code.tasks import TaskQueue, Task
from python_code.event_handling import EventHandler


class Entity(pygame.sprite.Sprite, ABC):
    def __init__(self, pos, size, *groups, color = (255,255,255),
                 layer = FIRST_LAYER, **kwargs):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.image = self._create_image(size, color, **kwargs)
        self.orig_image = self.image
        self.orig_rect = self.image.get_rect(topleft=pos)
        self.visible = True
        self.zoomable = False
        # should the entity move with the camera or not
        self.static = True
        self._layer = layer

    def _create_image(self, size, color, **kwargs):
        """
        Create an image using a size and color

        :param size: a Size object or tuple of lenght 2
        :param color: a rgb color as tuple of lenght 2 or 3
        :param kwargs: additional named arguments
        :return: a pygame Surface object
        """
        if len(color) == 3:
            image = pygame.Surface(size).convert()
        #included alpha channel
        elif len(color) == 4:
            image = pygame.Surface(size).convert_alpha()
        image.fill(color)
        return image

    @property
    def rect(self):
        return self.orig_rect

    @rect.setter
    def rect(self, rect):
        self.orig_rect = rect


class ZoomableEntity(Entity):
    """
    Basic zoomable entity class
    """
    def __init__(self, pos, size, *groups, zoom = 1, **kwargs):
        Entity.__init__(self, pos, size, *groups, **kwargs)
        #zoom variables
        self._zoom = zoom
        self.zoomable = True
        #if an entity is created after zooming make sure it is zoomed to the
        #right proportions
        if self._zoom != 1:
            self.zoom(self._zoom)

    def zoom(self, zoom):
        """
        Safe a zoom value so distance measures know how to change, also change
        the image size to make sure that this is not done every request.

        :param increase: a small integer that tells how much bigger the zoom
        should be
        """
        self._zoom = zoom
        orig_rect = self.orig_rect
        new_width = orig_rect.width * zoom
        new_height = orig_rect.height * zoom
        self.image = pygame.transform.scale(self.orig_image, (int(new_width),
                                                              int(new_height)))
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
        orig_pos[0] *= self._zoom
        orig_pos[1] *= self._zoom
        rect = self.image.get_rect(center = orig_pos)
        return rect


class SelectionRectangle(ZoomableEntity):
    """
    Creates a rectangle by draging the mouse. To highlight certain areas.
    """
    def __init__(self, pos, size, mouse_pos, *groups, **kwargs):
        ZoomableEntity.__init__(self, pos, size, *groups, **kwargs)
        self.__start_pos = list(pos)
        self.__prev_screen_pos = list(mouse_pos)
        self.__size = Size(*size)
        self.__update_image()

    def __update_image(self):
        """
        Update the rectangle image tha represents a highlighted area.
        """
        pos = self.__start_pos.copy()
        size = self.__size.size
        if self.__size.width < 0:
            pos[0] += self.__size.width
            size[0] = -1 * self.__size.width
        if self.__size.height < 0:
            pos[1] += self.__size.height
            size[1] = -1 * self.__size.height
        self.image = pygame.Surface(size).convert_alpha()
        self.image.fill((255,255,255,100))
        self.orig_rect = self.image.get_rect(topleft = pos)

        self.orig_image = self.image
        #make sure to update the zoomed image aswell
        self.zoom(self._zoom)

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


class MovingEntity(ZoomableEntity):
    """
    Base class for moving entities
    """
    MAX_SPEED = 10
    def __init__(self, pos, size, *groups, max_speed = MAX_SPEED, **kwargs):
        ZoomableEntity.__init__(self, pos, size, *groups, **kwargs)
        self.max_speed = max_speed
        self.speed = pygame.Vector2(0, 0)

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
        self.orig_rect.centerx = self._x_collision_adjusted_value()

        self.orig_rect.centery = self._y_collision_adjusted_value()

    def _x_collision_adjusted_value(self):
        """
        Adjust the centerx value based on collison values established for the
        entity. The basic collsion rules are not outside the playing board.

        :return: a float that represents the new x center coordinate of the
        rectangle of the entity.
        """
        new_centerx = max(0.5 * self.orig_rect.width,
                          min(self.orig_rect.centerx + self.speed.x,
                          ORIGINAL_BOARD_SIZE.width - 0.5 * self.orig_rect.width))
        return new_centerx

    def _y_collision_adjusted_value(self):
        """
        Adjust the centery value based on collison values established for the
        entity. The basic collsion rules are not outside the playing board.

        :return: a float that represents the new y center coordinate of the
        rectangle of the entity.
        """
        new_centery = max(0.5 * self.orig_rect.height,
                          min(self.orig_rect.centery + self.speed.y,
                          ORIGINAL_BOARD_SIZE.height - 0.5 * self.orig_rect.height))
        return new_centery


class InputSaver:
    """
    Save input into a dictionary. This is an abstract class that cannot be 
    instantiated on its own
    """

    def __init__(self):
        if type(self) == InputSaver:
            raise Exception("Cannot instaniate abstract class {}".format(type(self)))
        self._pressed_keys = {key: False for key in KEYBOARD_KEYS}
        self.selected = False

    def handle_events(self, events):
        """
        Record what buttons are pressed in self.__pressed_keys dictionary

        :param events: a list of pygame events
        """
        for event in events:
            if event.type == KEYDOWN:
                self._pressed_keys[event.key] = True
            elif event.type == KEYUP:
                self._pressed_keys[event.key] = False


class CameraCentre(MovingEntity, EventHandler):
    """
    The camera center where the camera centers on
    """
    def __init__(self, pos, size, *groups, **kwargs):
        MovingEntity.__init__(self, pos, size, *groups, max_speed = 20, **kwargs)
        EventHandler.__init__(self, [RIGHT, LEFT, UP, DOWN])
        self.orig_rect = pygame.Rect(*pos, *size)

    def handle_events(self, events):
        """
        Handle events for moving the camera around the board
        """
        leftover_events = EventHandler.handle_events(self, events)
        if self.pressed(RIGHT, continious=True) and self.pressed(LEFT, continious=True):
            self.speed.x = 0
        else:
            if self.pressed(RIGHT, continious=True):
                self.speed.x = min(self.max_speed, self.speed.x + self.max_speed)
            if self.pressed(LEFT, continious=True):
                self.speed.x = max(-self.max_speed, self.speed.x - self.max_speed)
            if not self.pressed(LEFT, continious=True) and not self.pressed(RIGHT, continious=True):
                self.speed.x = 0
        if self.pressed(DOWN, continious=True) and self.pressed(UP, continious=True):
            self.speed.y = 0
        else:
            if self.pressed(UP, continious=True):
                self.speed.y = max(-self.max_speed, self.speed.y - self.max_speed)
            if self.pressed(DOWN, continious=True):
                self.speed.y = min(self.max_speed, self.speed.y + self.max_speed)
            if not self.pressed(UP, continious=True) and not self.pressed(DOWN, continious=True):
                self.speed.y = 0
        return leftover_events


class Worker(MovingEntity):
    """
    A worker class that can perform tasks
    """
    COLOR = (255, 0, 179)
    SIZE = (10,10)
    #in wheight
    INVENTORY_SIZE = 2
    def __init__(self, pos, board, tasks, *groups, **kwargs):
        MovingEntity.__init__(self, pos, self.SIZE, *groups, color=self.COLOR,
                              max_speed=5, **kwargs)
        self.board = board
        self.task_control = tasks

        #tasks
        self.task_queue = TaskQueue()
        self.path = []
        self.dest = None

        #inventory
        self.inventory = Inventory(self.INVENTORY_SIZE)

    def update(self, *args):
        """
        Perform a task when avaialable
        """
        MovingEntity.update(self, *args)
        self.__perform_commands()

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
            self.__perform_task()
        elif self.inventory.full:
            block = self.board.closest_inventory(self.orig_rect)
            task = Task("Empty inventory")
            if block:
                block.add_task(task)
                self.task_queue.add(task, block)
                self.__start_task()
        #request a new task from task control if there are no tasks left
        elif self.task_queue.empty():
            task, block = self.task_control.get_task(self.orig_rect.topleft)
            if task:
                self.task_queue.add(task, block)
                self.__start_task()

##task management functions:

    def __start_task(self):
        """
        Called to start up the current task in the task_queue
        """
        path = self.board.pf.get_path(self.orig_rect,
                                      self.task_queue.task_block.rect)
        if path != None:
            self.task_queue.task.start()
            self.path = path
        else:
            self.task_queue.next()

    def __next_task(self):
        """
        For progressing to the next task in the queue.

        It is made sure certain last things are handled for certain task types
        as well as starting a new task if one is available in the queue
        """
        f_task, f_block = self.task_queue.next()
        # make sure that the entity stops when the task is sudenly finshed
        self.speed.x = self.speed.y = 0
        #make sure to move the last step if needed, so the worker does not potentially stop in a block
        if len(self.path) > 0:
            self.path = self.path[-1]
        else:
            #handle last thing of last task
            if f_task.handed_in:
                pass
            elif f_task.task_type == "Mining":
                self.board.remove_blocks([[f_block]])
                self.task_control.remove(f_block)
                self.inventory.add_blocks(f_block)
            elif f_task.task_type == "Empty inventory":
                items = self.inventory.get_all_items()
                f_block.add(*items)
            f_task.handed_in = True
        if not self.task_queue.empty():
            path = self.board.pf.get_path(self.orig_rect, self.task_queue.task_block.rect)
            self.__start_task()

    def __perform_task(self):
        """
        Perform a given task and finish it if that is the case
        """
        self.task_queue.task.task_progress[0] += GAME_TIME.get_time()
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


class TextSprite(ZoomableEntity):
    COLOR = (255,0,0)
    #in ms
    TOTAL_LIFE_SPAN = 1000
    """
    Entity for drawing text on the screen
    """
    def __init__(self, pos, size, text, font, *groups, color = COLOR, **kwargs):
        #size has no information
        ZoomableEntity.__init__(self, pos, size, *groups, font = font,
                                text = text, **kwargs)
        self.lifespan = [0,self.TOTAL_LIFE_SPAN]

    def _create_image(self, size, color, **kwargs):
        """
        Create some tect using a string, font and color

        :param size: a Size object or tuple of lenght 2
        :param color: a rgb color as tuple of lenght 2 or 3
        :param args: additional arguments
        :return: a pygame Surface object
        """
        image = kwargs["font"].render(str(kwargs["text"]), True, color)
        return image

    def update(self,*args):
        """
        Decrease the lifespan of the text making sure that is dies after around
        a second.
        """
        super().update(*args)
        self.lifespan[0] += GAME_TIME.get_time()
        if self.lifespan[0] >= self.lifespan[1]:
            self.kill()
        self.orig_rect.y -= 2
