from abc import ABC
from typing import Dict, Any

from utility import utilities as util, constants as con, loading_saving
from block_classes import blocks as block_classes


class TaskControl(loading_saving.Savable, loading_saving.Loadable):
    """
    Holds a list of block_classes that contain tasks that the workers can accept
    """
    def __init__(self, board):
        # variable to track tasks by name and allow for fast search and destroy
        self.reachable_block_tasks = {}
        self.unreachable_block_tasks = {}
        self.board = board
        self.__terminal_inv = board.terminal.inventory

    def __init_load__(self, reachable_block_tasks=None, unreachable_block_tasks=None, board=None):
        # variable to track tasks by name and allow for fast search and destroy
        self.reachable_block_tasks = reachable_block_tasks
        self.unreachable_block_tasks = unreachable_block_tasks
        self.board = board
        self.__terminal_inv = board.terminal.inventory

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reachable_block_tasks": {block_id: {task_name: task.to_dict() for task_name, task in task_dict.items()}
                                      for block_id, task_dict in self.reachable_block_tasks.items()},
            "unreachable_block_tasks": {block_id: {task_name: task.to_dict() for task_name, task in task_dict.items()}
                                        for block_id, task_dict in self.unreachable_block_tasks.items()}
        }

    @classmethod
    def from_dict(cls, dct, board=None):
        reachable_block_tasks = {block_id: {task_name: MultipleTaskList.from_dict(d)
                                            for task_name, d in outer_d.items()}
                                 for block_id, outer_d in dct["reachable_block_tasks"].items()}
        unreachable_block_tasks = {block_id: {task_name: MultipleTaskList.from_dict(d)
                                              for task_name, d in outer_d.items()}
                                   for block_id, outer_d in dct["unreachable_block_tasks"].items()}
        return cls.load(reachable_block_tasks=reachable_block_tasks, unreachable_block_tasks=unreachable_block_tasks,
                        board=board)

    def add(self, type, *blocks, priority = 1, **kwargs):
        """
        Add a task to the total list of tasks. This functions as a smart way of
        storing what tasks can likely be performed and which ones not.
        """
        for block in blocks:
            if isinstance(block, util.BlockPointer):
                block = block.block
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
            if len([b for b in surrounding_blocks if b is not None and b.transparant_group != 0]) > 0:
                if block.id not in self.reachable_block_tasks:
                    self.reachable_block_tasks[block.id] = {}
                if task.name() in self.reachable_block_tasks[block.id] and con.MULTI_TASKS[type].multi:
                    self.reachable_block_tasks[block.id][task.name()].append(task)
                else:
                    self.reachable_block_tasks[block.id][task.name()] = MultipleTaskList(task)
            else:
                if block.id not in self.unreachable_block_tasks:
                    self.unreachable_block_tasks[block.id] = {}
                if task.name() in self.unreachable_block_tasks[block.id] and con.MULTI_TASKS[type].multi:
                    self.unreachable_block_tasks[block.id][task.name()].append(task)
                else:
                    self.unreachable_block_tasks[block.id][task.name()] = MultipleTaskList(task)

    def remove_tasks(self, *tasks):
        for task in tasks:
            # a block can be none for tasks not added to the task control
            if task.block.id not in self.reachable_block_tasks or\
                    task.name() not in self.reachable_block_tasks[task.block.id]:
                continue
            self.reachable_block_tasks[task.block.id][task.name()].remove(task)

            if len(self.reachable_block_tasks[task.block.id][task.name()]) == 0:
                del self.reachable_block_tasks[task.block.id][task.name()]
            if len(self.reachable_block_tasks[task.block.id]) == 0:
                del self.reachable_block_tasks[task.block.id]

            if isinstance(task, MiningTask):
                self.__check_surrounding_tasks(task.block)
            elif isinstance(task, BuildTask) and task.finish_block.transparant_group != 0:
                self.__check_surrounding_tasks(task.block)
        return

    def cancel_tasks(self, *blocks, remove=False):
        """
        Remove a task from a block and consider other things if needed

        :param blocks: a list of block_classes for which tasks need to be removed
        """
        for block in blocks:
            removed_tasks = self.reachable_block_tasks.pop(block.id, None)
            if removed_tasks != None:
                for tasks in removed_tasks.values():
                    for task in tasks:
                        if remove == True:
                            self.remove_tasks(task)
                        #make sure that entitties still performing the task stop
                        task.cancel()
            else:
                removed_tasks = self.unreachable_block_tasks.pop(block.id, None)
            if removed_tasks != None:
                for tasks in removed_tasks.values():
                    for task in tasks:
                        if isinstance(task, BuildTask):
                            block.transparant_group = task.original_group

    def __check_surrounding_tasks(self, block):
        surrounding_task_blocks = [tb for tb in self.board.surrounding_blocks(block) if tb]
        for block in surrounding_task_blocks:
            block = block.block
            b = self.unreachable_block_tasks.pop(block.id, None)
            if b:
                self.reachable_block_tasks[block.id] = b

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
            distance = util.manhattan_distance(task.block.rect.topleft, worker_pos)
            task_tuples.append((task.selected, -1 * task.priority, distance))
        return sorted(task_tuples)


class MultipleTaskList(loading_saving.Savable, loading_saving.Loadable):
    """
    Object for tracking all tasks for a certain type and block
    """
    def __init__(self, task):
        self.tasks = [task]

    def __init_load__(self, tasks):
        self.tasks = tasks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, dct):
        print(dct)
        tasks = [Task.from_dict(d) for d in dct["tasks"]]
        return cls.load(tasks=tasks)

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


class TaskQueue(loading_saving.Savable, loading_saving.Loadable):
    """
    acts as a queue of tasks that are performed from last to first by a worker
    """
    def __init__(self):
        self.tasks = []

    def __init_load__(self, tasks):
        self.tasks = tasks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, dct):
        tasks = [Task.from_dict(d) for d in dct["tasks"]]
        return cls.load(tasks=tasks)

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

    def __len__(self):
        return len(self.tasks)


class Task(loading_saving.Savable, loading_saving.Loadable, ABC):
    """
    Object for storing a task and its progress
    """
    def __init__(self, block, priority=1, **kwargs):
        self.block = block
        self.priority = priority

        self.started_task = False
        self.selected = False
        # determined by material
        self.task_progress = [val for val in [0, 1000]]
        self.__handed_in = False
        self.__canceled = False

    def __init_load__(self, block=None, priority=None, started_task=None, selected=None, task_progress=None,
                      handed_in=None, canceled=None):
        self.block = block
        self.priority = priority

        self.started_task = started_task
        self.selected = selected
        # determined by material
        self.task_progress = task_progress
        self.__handed_in = handed_in
        self.__canceled = canceled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_name": type(self).__name__,
            "block": self.block.to_dict(),
            "priority": self.priority,
            "started_task": self.started_task,
            "selected": self.selected,
            "task_progress": self.task_progress,
            "handed_in": self.__handed_in,
            "canceled": self.__canceled
        }

    @classmethod
    def from_dict(cls, dct, first=True):
        # since the from_dict method is shared with inheriting classes
        if first:
            cls_type = globals()[dct["instance_name"]]
            return cls_type.from_dict(dct, first=False)
        else:
            block = cls.block_dict_to_block(dct["block"])
            return cls.load(block=block, priority=dct["priority"], started_task=dct["started_task"],
                            selected=dct["selected"], task_progress=dct["task_progress"],
                            handed_in=dct["handed_in"], canceled=dct["canceled"])

    @staticmethod
    def block_dict_to_block(dct):
        pos = dct["pos"]
        mcd = block_classes.Block.from_dict(dct)
        material = mcd.to_instance()
        block = material.to_block(pos)
        return block

    def start(self, entity, **kwargs):
        self.started_task = True
        #in case of canceled tasks
        self.__canceled = False
        self._set_task_progress(entity)

    def _set_task_progress(self, entity):
        self.task_progress = [0, self.block.mining_speed]

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
    def name(cls):
        return cls.__name__

    @property
    def finished(self):
        """
        If the task is finished

        :return: a boolean
        """
        return self.task_progress[0] >= self.task_progress[1] or self.__handed_in

    def __str__(self):
        return f"{self.name()}"
    

class MultiTask(Task, ABC):
    MAX_RETRIES = 5

    def __init__(self, block, **kwargs):
        Task.__init__(self, block, **kwargs)
        self._subtask_count = 0
        self.finished_subtasks = False
        self._max_retries = self._get_max_retries()

    def __init_load__(self, subtask_count=None, finished_subtasks=None, max_retries=None, **kwargs):
        super().__init_load__(**kwargs)
        self._subtask_count = subtask_count
        self.finished_subtasks = finished_subtasks
        self._max_retries = max_retries

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["subtask_count"] = self._subtask_count
        d["finished_subtasks"] = self.finished_subtasks
        d["max_retries"] = self._max_retries
        return d

    @classmethod
    def from_dict(cls, dct, first=True):
        block = cls.block_dict_to_block(dct["block"])
        return cls.load(block=block, priority=dct["priority"], started_task=dct["started_task"],
                        selected=dct["selected"], task_progress=dct["task_progress"], handed_in=dct["handed_in"],
                        canceled=dct["canceled"], subtask_count=dct["subtask_count"],
                        finished_subtasks=dct["finished_subtasks"], max_retries=dct["max_retries"])

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


class MiningTask(Task):

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        removed_items = entity.board.remove_blocks(self.block)
        entity.inventory.add_items(*removed_items, ignore_filter=True)


class BuildTask(MultiTask):
    BUILDING_SPEED = 100

    def __init__(self, block, finish_block, original_group, removed_blocks, **kwargs):
        super().__init__(block, **kwargs)
        self.finish_block = finish_block
        self.original_group = original_group
        self.removed_blocks = [block for block in removed_blocks if block.name() != "Air"]

    def __init_load__(self, finish_block=None, original_group=None, removed_blocks=None, **kwargs):
        super().__init_load__(**kwargs)
        self.finish_block = finish_block
        self.original_group = original_group
        self.removed_blocks = removed_blocks

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["finish_block"] = self.finish_block.to_dict()
        d["original_group"] = self.original_group
        d["removed_blocks"] = [block.to_dict() for block in self.removed_blocks]
        return d

    @classmethod
    def from_dict(cls, dct, first=True):
        block = cls.block_dict_to_block(dct["block"])
        finish_block = cls.block_dict_to_block(dct["finish_block"])
        removed_blocks = [cls.block_dict_to_block(d["blocks"]) for d in dct["removed_blocks"]]
        return cls.load(block=block, priority=dct["priority"], started_task=dct["started_task"],
                        selected=dct["selected"], task_progress=dct["task_progress"], handed_in=dct["handed_in"],
                        canceled=dct["canceled"], original_group=dct["original_group"],
                        finished_block=finish_block, removed_blocks=removed_blocks)

    def start(self, entity, **kwargs):
        if not entity.inventory.check_item_get(self.finish_block.name()):
            task = FetchTask(entity, self.finish_block.name(), **kwargs)
            self.start_subtask(task, entity)
        else:
            self.finished_subtasks = True
        super().start(entity, **kwargs)

    def _set_task_progress(self, entity):
        #TODO add mining tasks instead of remving and building at the same time. Low prio
        self.task_progress = [0, self.BUILDING_SPEED + sum(b.mining_speed for b in self.removed_blocks)]

    def hand_in(self, entity, **kwargs):
        super().hand_in(entity, **kwargs)
        entity.board.add_blocks(self.finish_block)
        entity.inventory.get(self.finish_block.name(), 1)
        entity.inventory.add_blocks(*self.removed_blocks)


class FetchTask(Task):
    FETCH_SPEED = 50

    def __init__(self, entity, req_block_name, inventory_block = None, quantity=1, ignore_filter=False, **kwargs):
        self.req_block_name = req_block_name
        self.quantity = quantity
        self.ignore_filter = ignore_filter
        if inventory_block is not None:
            block = inventory_block
        else:
            block = entity.board.closest_inventory(entity.orig_rect, self.req_block_name, deposit=False)
        super().__init__(block, **kwargs)

    def __init_load__(self, required_block_name=None, quantity=None, ignore_filter=None, **kwargs):
        super().__init_load__(**kwargs)
        self.req_block_name = required_block_name
        self.quantity = quantity
        self.ignore_filter = ignore_filter

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["req_block_name"] = self.req_block_name
        d["quantity"] = self.quantity
        d["ignore_filter"] = self.ignore_filter
        return d

    @classmethod
    def from_dict(cls, dct, first=True):
        block = cls.block_dict_to_block(dct["block"])

        return cls.load(block=block, priority=dct["priority"], started_task=dct["started_task"],
                        selected=dct["selected"], task_progress=dct["task_progress"], handed_in=dct["handed_in"],
                        canceled=dct["canceled"], required_block_name=dct["required_block_name"],
                        quantity=dct["quantity"], ignore_filter=dct["ignore_filter"])

    def start(self, entity, inventory_block=None, **kwargs):
        if self.block != None:
            super().start(entity, **kwargs)
        else:
            # cheat way to disregard the task
            super().hand_in(None)
            self.started_task = True
            self.task_progress = [0, -1]

    def _set_task_progress(self, entity):
        self.task_progress = [0, self.quantity * self.FETCH_SPEED]

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
    EMPTY_SPEED = 50

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

    def _set_task_progress(self, entity):
        self.task_progress = [0, entity.inventory.number_of_items * self.EMPTY_SPEED]

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

    def _set_task_progress(self, entity):
        #no task to perform
        self.task_progress = [0, 1]

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

    def _set_task_progress(self, entity):
        #no task to perform
        self.task_progress = [0, 1]
