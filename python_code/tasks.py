from abc import ABC, abstractmethod

from python_code.utility.utilities import manhattan_distance
from python_code.board.blocks import AirBlock
from python_code.board.materials import Air
from python_code.utility.constants import MULTI_TASKS

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

    def add(self, type, *blocks, priority = 1, **kwargs):
        """
        Add a task to the total list of tasks. This functions as a smart way of
        storing what tasks can likely be performed and which ones not.
        """
        for block in blocks:
            if type == "Building":
                task = BuildTask(block, priority = priority, **kwargs)
            elif type == "Request":
                task = RequestTask(block, priority=priority, **kwargs)
            elif type == "Deliver":
                task = DeliverTask(block, priority=priority, **kwargs)
            elif type == "Mining":
                task = MiningTask(block, priority=priority, **kwargs)
            else:
                raise Exception("Invalid task name {}".format(type))

            surrounding_blocks = self.board.surrounding_blocks(block)
            if len([b for b in surrounding_blocks if b != None and b.transparant_group != 0]) > 0:
                if block not in self.reachable_block_tasks:
                    self.reachable_block_tasks[block] = {}
                if task.name() in self.reachable_block_tasks[block] and MULTI_TASKS[type]:
                    self.reachable_block_tasks[block][task.name()].append(task)
                else:
                    self.reachable_block_tasks[block][task.name()] = MultipleTaskList(task)
            else:
                if block not in self.unreachable_block_tasks:
                    self.unreachable_block_tasks[block] = {}
                if task.name() in self.unreachable_block_tasks[block] and MULTI_TASKS[type]:
                    self.unreachable_block_tasks[block][task.name()].append(task)
                else:
                    self.unreachable_block_tasks[block][task.name()] = MultipleTaskList(task)

    def remove_tasks(self, *tasks):
        for task in tasks:
            #a block can be none for tasks not added to the task control
            if task.block not in self.reachable_block_tasks or task.name() not in self.reachable_block_tasks[task.block]:
                continue
            self.reachable_block_tasks[task.block][task.name()].remove(task)

            if len(self.reachable_block_tasks[task.block][task.name()]) == 0:
                del self.reachable_block_tasks[task.block][task.name()]
            if len(self.reachable_block_tasks[task.block]) == 0:
                del self.reachable_block_tasks[task.block]

            if isinstance(task, MiningTask):
                self.__check_surrounding_tasks(task.block)
            elif isinstance(task, BuildTask) and task.finish_block.transparant_group != 0:
                self.__check_surrounding_tasks(task.block)
        return

    def cancel_tasks(self, *blocks, remove=False):
        """
        Remove a task from a block and consider other things if needed

        :param blocks: a list of blocks for which tasks need to be removed
        """
        for block in blocks:
            removed_tasks = self.reachable_block_tasks.pop(block, None)
            if removed_tasks != None:
                for tasks in removed_tasks.values():
                    for task in tasks:
                        if remove == True:
                            self.remove_tasks(task)
                        #make sure that entitties still performing the task stop
                        task.cancel()
            else:
                removed_tasks = self.unreachable_block_tasks.pop(block, None)
            if removed_tasks != None:
                for tasks in removed_tasks.values():
                    for task in tasks:
                        if isinstance(task, BuildTask):
                            block.transparant_group = task.original_group

    def __check_surrounding_tasks(self, block):
        surrounding_task_blocks = [tb for tb in self.board.surrounding_blocks(block) if tb]
        for block in surrounding_task_blocks:
            b = self.unreachable_block_tasks.pop(block, None)
            if b:
                self.reachable_block_tasks[block] = b

    def get_task(self, worker_pos):

        sorted_task_dicts = sorted(self.reachable_block_tasks.values(), key = lambda x: self.__best_task_sort_tuple(x, worker_pos)[0])

        for task_dict in sorted_task_dicts:
            for tasks in sorted(task_dict.values(), key=lambda x: self.__best_task_sort_tuple(task_dict, worker_pos)):
                task = None
                for t in tasks:
                    if not t.selected:
                        task = t
                        break
                if task == None:
                    continue
                if isinstance(task, BuildTask):
                    #TODO make this a total inventory of all inventories on the map
                    if not self.__terminal_inv.check_item_get(task.finish_block.name()):
                        continue
                elif isinstance(task, RequestTask):
                    #TODO make this a total inventory of all inventories on the map
                    if not self.__terminal_inv.check_item_get(task.req_item.name(), 1) and\
                            task.block.inventory.check_item_deposit(task.req_item.name()):
                        continue
                if task != None:
                    task.selected = True
                return task
        return None

    def __best_task_sort_tuple(self, task_dictionary, worker_pos):
        task_tuples = []
        for tasks in task_dictionary.values():
            task = tasks[0]
            distance = manhattan_distance(task.block.rect.topleft, worker_pos)
            task_tuples.append((task.selected, -1 * task.priority, distance))
        return sorted(task_tuples)


class MultipleTaskList:
    """
    Object for tracking all tasks for a certain type and block
    """
    def __init__(self, task):
        self.tasks = [task]

    def task(self):
        return self.tasks[0]

    def append(self, task):
        self.tasks = list(sorted(self.tasks + [task], key=lambda x: (x.started_task, -1 * x.priority)))

    def pop(self, item):
        if isinstance(item, Task):
            for index, task in enumerate(self.tasks):
                if item == task:
                    popped_task = self.tasks.pop(index)
                    self.tasks = list(sorted(self.tasks, key=lambda x: (x.started_task, -1 * x.priority)))
                    return popped_task
            return None
        popped_task = self.tasks.pop(item)
        self.tasks = list(sorted(self.tasks, key=lambda x: (x.started_task, -1 * x.priority)))
        return popped_task

    def __getitem__(self, index):
        return self.tasks[index]

    def __iter__(self):
        return iter(self.tasks)

    def remove(self, task):
        for t in self.tasks:
            if t == task:
                self.tasks.remove(task)
                break
        if len(self.tasks) > 0:
            self.tasks = list(sorted(self.tasks, key=lambda x: (x.started_task, -1 * x.priority)))

    def __len__(self):
        return len(self.tasks)


class TaskQueue:
    """
    acts as a queue of tasks that are performed from last to first by a worker
    """
    def __init__(self):
        self.tasks = []

    def add(self, task):
        """
        Add a task to the queue

        :param task: a Task Object
        """
        self.tasks.append(task)

    @property
    def task(self):
        """
        The current task that is at the top of the stack

        :return: a Task object or None
        """
        if not self.empty():
            return self.tasks[-1]
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
        return finished_task, finished_task.block


class Task(ABC):
    """
    Object for storing a task and its progress
    """
    def __init__(self, block, priority = 1, **kwargs):
        self.block = block
        self.priority = priority

        self.started_task = False
        self.selected = False
        #determined by material
        self.task_progress = [val for val in [0, 1000]]
        self.__handed_in = False
        self.__canceled = False

    def start(self, entity, **kwargs):
        self.started_task = True
        #in case of canceled tasks
        self.__canceled = False
        self._set_task_progress()

    def _set_task_progress(self):
        self.task_progress = [0, self.block.material.task_time()]

    def cancel(self):
        self.started_task = False
        self.selected = False
        self.__canceled = True

    def uncancel(self):
        self.__canceled = False
        self.decrease_priority()

    def decrease_priority(self, amnt = -1):
        self.priority += amnt

    def hand_in(self, entity, **kwargs):
        self.__handed_in = True

    def handed_in(self):
        return self.__handed_in

    def canceled(self):
        return self.__canceled

    @classmethod
    def name(self):
        return self.__name__

    @property
    def finished(self):
        """
        If the task is finished

        :return: a boolean
        """
        return self.task_progress[0] >= self.task_progress[1] or self.__handed_in

    def __str__(self):
        return "Task object {}:\nBlock: {}\nPriority: {}\nSelected: {}\nStarted: {}\nProgress: {}\nFinished: {}\nCanceled: {}\n".\
            format(super().__str__(), self.block, self.priority, self.selected, self.started_task, self.task_progress, self.finished, self.__canceled)
    

class MultiTask(Task, ABC):
    MAX_RETRIES = 5
    def __init__(self, block, **kwargs):
        Task.__init__(self, block, **kwargs)
        self._subtask_count = 0
        self.finished_subtasks = False
        self._max_retries = self._get_max_retries()

    def start(self, entity, **kwargs):
        self._subtask_count += 1
        if self.finished_subtasks:
            super().start(entity, **kwargs)
        elif self._subtask_count > self._max_retries:
            #make sure to remove the task at the start of the task queue
            entity.task_queue.next()
            self.cancel()


    def start_subtask(self, task, entity):
        entity.task_queue.add(task)
        task.selected = True
        task.start(entity)

    def cancel(self):
        super().cancel()
        self.finished_subtasks = False
        self._subtask_count = 0

    def _get_max_retries(self):
        return self.MAX_RETRIES

    def __str__(self):
        return "{}Finished subtasks: {}\n".format(super().__str__(), self.finished_subtasks)


class MiningTask(Task):

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        if hasattr(self.block, "inventory"):
            items = self.block.inventory.get_all_items(ignore_filter=True)
            entity.inventory.add_items(*items)
        entity.board.remove_blocks(self.block)
        entity.inventory.add_blocks(self.block)


class BuildTask(MultiTask):
    #amount of times this task can retry the subtasks until it is
    def __init__(self, block, finish_block, original_group, removed_blocks, **kwargs):
        super().__init__(block, **kwargs)
        self.finish_block = finish_block
        self.original_group = original_group
        self.removed_blocks = [block for block in removed_blocks if block.name() != "Air"]

    def start(self, entity, **kwargs):
        if not entity.inventory.check_item_get(self.finish_block.name()):
            task = FetchTask(entity, self.finish_block.name(), **kwargs)
            self.start_subtask(task, entity)
        else:
            self.finished_subtasks = True
        super().start(entity, **kwargs)

    def _set_task_progress(self):
        self.task_progress = [0, self.finish_block.material.task_time() + sum(b.material.task_time() for b in self.removed_blocks)]

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        entity.board.add_blocks(self.finish_block, update=True)
        entity.inventory.get(self.finish_block.name(), 1)
        entity.inventory.add_blocks(*self.removed_blocks)


class FetchTask(Task):
    def __init__(self, entity, req_block_name, inventory_block = None, quantity=1, ignore_filter=False, **kwargs):
        self.req_block_name = req_block_name
        self.quantity = quantity
        self.ignore_filter = ignore_filter
        if inventory_block != None:
            block = inventory_block
        else:
            block = entity.board.closest_inventory(entity.orig_rect, self.req_block_name, deposit=False)
        super().__init__(block, **kwargs)

    def start(self, entity, inventory_block=None, **kwargs):
        if self.block != None:
            super().start(entity, **kwargs)
        else:
            # cheat way to disregard the task
            super().hand_in(None)
            self.started_task = True
            self.task_progress = [0, -1]

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        if self.block:
            item = self.block.inventory.get(self.req_block_name, self.quantity, ignore_filter=self.ignore_filter)
            if item and item.quantity == self.quantity:
                if entity.inventory.check_item_deposit(item.name()):
                    entity.inventory.add_items(item)
                else:
                    self.block.inventory.add_items(item)


class EmptyInventoryTask(Task):
    def __init__(self, entity, **kwargs):
        block = entity.board.closest_inventory(entity.orig_rect, *entity.inventory.item_names, deposit=True)
        super().__init__(block, **kwargs)

    def start(self, entity, **kwargs):
        if self.block != None:
            super().start(entity, **kwargs)
        else:
            #cheat way to disregard the task
            super().hand_in(None)
            self.started_task = True
            self.task_progress = [0, -1]

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        if self.block != None:
            items = entity.inventory.get_all_items()
            for item in items:
                if self.block.inventory.check_item_deposit(item.name()):
                    self.block.inventory.add_items(item)
                else:
                    entity.inventory.add_items(item)


class RequestTask(MultiTask):
    def __init__(self, block, req_item, **kwargs):
        self.req_item = req_item
        super().__init__(block, **kwargs)

    def _get_max_retries(self):
        return self.MAX_RETRIES + self.req_item.quantity

    def start(self, entity, **kwargs):
        #TODO make this dependant on what the entity can cary
        if not self.finished_subtasks and not entity.inventory.check_item_get(self.req_item.name(), quantity=self.req_item.quantity):
            if entity.inventory.full and entity.inventory.check_item_get(self.req_item.name(), 1):
                self.__push_new_request(entity)
            #at least one item was retrieved
            elif self._subtask_count + 1 > self._max_retries and entity.inventory.check_item_get(self.req_item.name(), 1):
                self.__push_new_request(entity)
            else:
                task = FetchTask(entity, self.req_item.name(), **kwargs)
                self.start_subtask(task, entity)
        else:
            self.finished_subtasks = True
        super().start(entity, **kwargs)

    def __push_new_request(self, entity):
        self.finished_subtasks = True
        leftover = self.req_item.quantity - entity.inventory.item_pointer(self.req_item.name()).quantity
        if leftover > 0:
            new_item = self.req_item.copy()
            new_item.quantity = leftover
            entity.task_control.add("Request", self.block, req_item=new_item)

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        #grab the full amount or what is available
        item = entity.inventory.get(self.req_item.name(), self.req_item.quantity)
        if item != None:
            if self.block.inventory.check_item_deposit(item.name()):
                self.block.inventory.add_items(item)
            #add back item to not delete it
            else:
                entity.inventory.add_items(item)

    def __str__(self):
        return "{}Requested item: {}\n".format(super().__str__(), self.req_item)


class DeliverTask(MultiTask):
    MAX_RETRIES = 5
    def __init__(self, block, pushed_item, **kwargs):
        self.pushed_item = pushed_item
        super().__init__(block, **kwargs)
        self.__finished_get = False

    def _get_max_retries(self):
        return self.MAX_RETRIES + self.pushed_item.quantity

    def start(self, entity, **kwargs):
        # first start potentail other tasks
        if not self.__finished_get and not entity.inventory.check_item_get(self.pushed_item.name(), quantity=self.pushed_item.quantity):
            task = FetchTask(entity, self.pushed_item.name(), inventory_block=self.block, quantity=self.pushed_item.quantity, ignore_filter=True, **kwargs)
            self.start_subtask(task, entity)
        elif not entity.inventory.empty:
            self.__finished_get = True
            task = EmptyInventoryTask(entity, **kwargs)
            self.start_subtask(task, entity)
        else:
            self.finished_subtasks = True
        super().start(entity, **kwargs)

    def __str__(self):
        return "{}Deliver item: {}\n".format(super().__str__(), self.pushed_item)
