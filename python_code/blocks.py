import pygame

from python_code.constants import SHOW_BLOCK_BORDER, MODES

class BaseBlock:
    """
    Base class for the blocks in image matrices
    """
    #all tasks types are allowed
    ALLOWED_TASKS = [mode.name for mode in MODES.values()]
    def __init__(self, pos, size):
        if type(self) == BaseBlock:
            raise Exception("Cannot instantiate base class BaseBlock")
        self.size = size
        self.rect = pygame.Rect((*pos, *self.size))
        self.tasks = {}

    def add_task(self, task):
        """
        Can hold a task from each type

        :param task: a Task object
        """
        if task.task_type in self.ALLOWED_TASKS:
            self.tasks[task.task_type] = task
        elif WARNINGS:
            print("WARNING: Task of type {} is not allowed for block type {}".format(task.task_type, type(self)))

    def remove_finished_tasks(self):
        """
        Check if tasks are finished or not.

        :return: a list of task types that are removed.
        """
        finished = []
        for key in list(self.tasks.keys()):
            task = self.tasks[key]
            if task.finished:
                del self.tasks[task.task_type]
                finished.append(task.task_type)
        return finished

    @property
    def coord(self):
        """
        Simplify getting the coordinate of a block

        :return: the topleft cooridnate of the block rectangle.
        """
        return self.rect.topleft

    def __eq__(self, other):
        return other == self.material

    def __hash__(self):
        return hash(str(self.rect.topleft))

class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, size, material):
        super().__init__(pos, size)
        self.material = material
        self.surface = self.__create_surface()
        self.rect = self.surface.get_rect(topleft=pos)

    def add_task(self, task):
        """
        Add an additional task progress for the task on a material block
        """
        super().add_task(task)
        task.task_progress = [0, self.material.task_time()]

    def __create_surface(self):
        """
        Create the surface of the block, this depends on the depth of the block
        and potential border

        :return: a pygame Surface object
        """
        surface = pygame.Surface(self.size)
        surface.fill(self.material.color)
        if SHOW_BLOCK_BORDER:
            pygame.draw.rect(surface, self.material.border_color,
                             (0, 0, self.size.width + 1,
                              self.size.height + 1), 1)
        return surface.convert()

class AirBlock(BaseBlock):
    """
    Special case of a block class that is an empty block with no surface
    """
    def __init__(self, pos, size):
        super().__init__(pos, size)
        self.material = "Air"
