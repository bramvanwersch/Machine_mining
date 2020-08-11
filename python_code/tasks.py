from python_code.utility.utilities import manhattan_distance
from python_code.board.blocks import AirBlock
from python_code.board.materials import Air

class TaskControl:
    """
    Holds a list of blocks that contain tasks that the workers can accept
    """
    def __init__(self, board):
        #variable to track tasks by name and allow for fast search and destroy
        self.reachable_block_tasks = {}
        self.unreachable_block_tasks = {}
        self.board = board
        self.__terminal_inv = board.inventorie_blocks[0].inventory

    def add(self, type, blocks, priority = 1):
        """
        Add a task to the total list of tasks. This functions as a smart way of
        storing what tasks can likely be performed and which ones not.
        """
        for row in blocks:
            for block in row:
                if block  == None or block == "Air":
                    continue
                task = Task(type, priority = priority)

                #if task is accepted
                if block.add_task(task):
                    if len([b for b in self.board.surrounding_blocks(block) if b == "Air"]) > 0:
                        self.reachable_block_tasks[block] = block
                    else:
                        self.unreachable_block_tasks[block] = block

    def remove(self, *blocks, cancel = False):
        """
        Remove a task from a block and consider other things if needed

        :param blocks: a list of blocks for which tasks need to be removed
        """
        for block in blocks:
            if block == None or block == "Air":
                continue
            removed_type = block.remove_task()
            #if all the tasks are depleted
            if removed_type:
                #pop a task if not already removed by another worker or not present in case of cancels
                self.reachable_block_tasks.pop(block, None)
                self.unreachable_block_tasks.pop(block, None)

            #if a task was completed that removes the block check if surrounding tasks can now be acceses
            if removed_type == "Mining":
                surrounding_task_blocks = [tb for tb in self.board.surrounding_blocks(block) if tb]
                for b in surrounding_task_blocks:
                    b = self.unreachable_block_tasks.pop(b, None)
                    if b:
                        self.reachable_block_tasks[b] = b
            #make sure to add the original back
            elif removed_type == "Building" and cancel == True:
                if block.original_block != "Air":
                    self.board.add_block(block.original_block)
                else:
                    self.board.remove_blocks([[block]])

    def get_task(self, worker_pos):
        """
        Get a task from the reachable_block_tasks list based on position,
        priority of a task and if a task was started already by another worker

        :param worker_pos: The position of the worker requesting a new task
        :return a Task and Block object or double None
        """
        sorted_blocks = sorted(self.reachable_block_tasks.values(), key = lambda x: self.__block_sort_tuple(x, worker_pos))
        for block in sorted_blocks:
            #if no materials are avaialable skip the building task
            if block.task.task_type == "Building":
                if not self.__terminal_inv.check_item(block.finish_block.name(), 1):
                    continue
            return block.task, block
        return None, None

    def __block_sort_tuple(self, block, worker_pos):
        """
        create a tuple for sorting

        :param block: block of a task
        :param worker_pos: the position of the worker
        :return: a tuple (boolean, integer, float)
        """
        distance = manhattan_distance(block.rect.topleft, worker_pos)
        return (block.task.started_task, block.task.priority, distance)

class TaskQueue:
    """
    acts as a queue of tasks that are performed from last to first by a worker
    """
    def __init__(self):
        self.tasks = []
        self.blocks = []

    def add(self, task, block):
        """
        Add a task to the queue

        :param task: a Task Object
        :param block: a Block Object
        """
        self.tasks.append(task)
        self.blocks.append(block)

    @property
    def task(self):
        """
        The current task that is at the top of the stack

        :return: a Task object or None
        """
        if not self.empty():
            return self.tasks[-1]
        return None

    @property
    def task_block(self):
        """
        The block the current task is performed on

        :return: a Block Object or None
        """
        if not self.empty():
            return self.blocks[-1]
        return None

    def empty(self):
        """
        Check to see if the queue is empty

        :return: a boolean
        """
        return len(self.tasks) <= 0

    def next(self):
        """
        Go to the next task and return the current task and block for the last
        operations

        :return: a Task and a Block object in that order
        """
        finished_task = self.tasks.pop()
        finished_task_block = self.blocks.pop()
        return finished_task, finished_task_block

class Task:
    """
    Object for storing a task and its progress
    """
    def __init__(self, task_type, priority = 1, **kwargs):
        self.task_type = task_type
        self.priority = priority
        #change priority of assigning tasks
        self.started_task = False
        #determined by material
        self.task_progress = [0, 1]
        self.handed_in = False
        self.__additional_info = kwargs

    def start(self):
        """
        Signifies that the task is being worked on by a worker changes the
        priority of accepting this task
        """
        self.started_task = True

    @property
    def finished(self):
        """
        If the task is finished

        :return: a boolean
        """
        return self.task_progress[0] >= self.task_progress[1]

    def __getattr__(self, item):
        """
        Allow to add some custom attributes using the kwargs. This can be small
        things that allow to save some varaible

        :param item: the name of a variable]
        :return: the value of set variable as saved in the __additional_info
        """
        return self.__additional_info[item]
