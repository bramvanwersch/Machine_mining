from python_code.utilities import manhattan_distance

class TaskControl:
    """
    Holds a list of blocks that contain tasks that the workers can accept
    """
    def __init__(self, board):
        #variable to track tasks by name and allow for fast search and destroy
        self.reachable_block_tasks = {}
        self.unreachable_block_tasks = {}
        self.board= board

    def add(self, type, blocks, priority = 1):
        """
        """
        for row in blocks:
            for block in row:
                if block == "Air":
                    continue
                task = Task(type, priority = priority)

                #if task is accepted
                if block.add_task(task):
                    if len([b for b in self.board.surrounding_blocks(block) if b == "Air"]) > 0:
                        self.reachable_block_tasks[block] = block
                    else:
                        self.unreachable_block_tasks[block] = block

    def remove(self, *blocks):
        """
        Remove a task from a block and consider other things if needed

        :param blocks: a list of blocks for which tasks need to be removed
        """
        for block in blocks:
            if block == None:
                continue
            removed_types = block.remove_finished_tasks()
            #if all the tasks are depleted
            if len(block.tasks) == 0:
                #pop a task if not already removed by another worker or not present in case of cancels
                self.reachable_block_tasks.pop(block, None)
                self.unreachable_block_tasks.pop(block, None)

            #if a task was completed that removes the block check if surrounding tasks can now be acceses
            if "Mining" in removed_types:
                surrounding_task_blocks = [tb for tb in self.board.surrounding_blocks(block) if tb and len(tb.tasks) > 0]
                for b in surrounding_task_blocks:
                    b = self.unreachable_block_tasks.pop(b, None)
                    if b:
                        self.reachable_block_tasks[b] = b

    def get_task(self, position):
        """

        """
        sorted_blocks = sorted(self.reachable_block_tasks.values(), key = lambda x: self.__block_sort_tuple(x, position))
        if len(sorted_blocks) > 0:
            best_task = sorted(sorted_blocks[0].tasks.values(), key = lambda x: (x.started_task, x.priority))[0]
            return best_task, sorted_blocks[0]
        return None, None

    def __block_sort_tuple(self, block, worker_pos):
        best_task = sorted(block.tasks.values(),
                           key=lambda x: (x.started_task, x.priority))[0]
        distance = manhattan_distance(block.rect.topleft, worker_pos)
        return (best_task.started_task, best_task.priority, distance)

class TaskQueue:
    def __init__(self):
        self.tasks = []
        self.blocks = []

    def add(self, task, block):
        self.tasks.append(task)
        self.blocks.append(block)

    @property
    def task(self):
        if not self.empty():
            return self.tasks[-1]
        return None

    @property
    def task_block(self):
        if not self.empty():
            return self.blocks[-1]
        return None

    def empty(self):
        return len(self.tasks) <= 0

    def next(self):
        finished_task = self.tasks.pop()
        finished_task_block = self.blocks.pop()
        return finished_task, finished_task_block

class Task:
    def __init__(self, task_type, priority = 1):
        self.task_type = task_type
        self.priority = priority
        #change priority of assigning tasks
        self.started_task = False
        self.task_progress = [0, 1]

    def start(self):
        self.started_task = True

    @property
    def finished(self):
        """
        If the task is finished

        :return: a boolean
        """
        return self.task_progress[0] >= self.task_progress[1]
