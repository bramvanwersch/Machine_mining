import pygame

from python_code.constants import SHOW_BLOCK_BORDER, MODES, WARNINGS

class BaseBlock:
    """
    Base class for the blocks in image matrices
    """
    #all tasks types are allowed
    def __init__(self, pos, size):
        if type(self) == BaseBlock:
            raise Exception("Cannot instantiate base class BaseBlock")
        self.size = size
        self.rect = pygame.Rect((*pos, *self.size))
        self.tasks = {}

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


class AirBlock(BaseBlock):
    """
    Special case of a block class that is an empty block with no surface
    """
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.material = "Air"


class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, size, material, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.material = material
        self.surface = self.material.surface
        self.rect = self.surface.get_rect(topleft=pos)

    def add_task(self, task):
        """
        Can hold a task from each type

        :param task: a Task object
        :return: a boolean signifying if the task was added or not
        """
        if task.task_type in self.material.ALLOWED_TASKS:
            self.tasks[task.task_type] = task
            task.task_progress = [0, self.material.task_time()]
            return True
        return False


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
