import pygame
from abc import ABC

from python_code.utility.constants import BLOCK_SIZE


class BaseBlock(ABC):
    """
    Base class for the blocks in image matrices
    """
    #all tasks types are allowed
    def __init__(self, pos):
        self.size = BLOCK_SIZE
        self.rect = pygame.Rect((*pos, *self.size))
        self.task = None

    @property
    def coord(self):
        """
        Simplify getting the coordinate of a block

        :return: the topleft cooridnate of the block rectangle.
        """
        return self.rect.topleft

    @property
    def allowed_tasks(self):
        """
        Convenience method testing what tasks are allowed for a certain block

        :return: a list of strings of allowable tasks
        """
        return self.material.ALLOWED_TASKS

    def add_task(self, task):
        """
        Can hold a task from each type

        :param task: a Task object
        :return: a boolean signifying if the task was added or not
        """
        if task.task_type in self.material.ALLOWED_TASKS:
            self.task = task
            task.task_progress = [0, self.material.task_time()]
            return True
        return False

    def remove_task(self):
        """
        remove a task from a block

        :return: a list of task types that are removed.
        """
        if self.task != None:
            type = self.task.task_type
            self.task = None
            return type
        return None

    def __eq__(self, other):
        return other == self.material.name()

    def __hash__(self):
        return hash(str(self.rect.topleft))


class AirBlock(BaseBlock):
    """
    Special case of a block class that is an empty block with no surface
    """
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, **kwargs)
        self.material = material


class BuildingBlock(BaseBlock):
    def __init__(self, pos, material, finish_block, **kwargs):
        super().__init__(pos, **kwargs)
        self.material = material
        self.finish_block = finish_block


class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, **kwargs)
        self.material = material
        self.surface = self.material.surface
        self.rect = self.surface.get_rect(topleft=pos)


class ContainerBlock(Block):
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)
        #how full the terminal is does not matter
        self.inventory = None

    def add(self, *items):
        if self.inventory != None:
            self.inventory.add_items(*items)
