from abc import ABC, abstractmethod

import utility.utilities as util
import utility.constants as con
import inventories


class EdgeTaskQueue(util.Serializer):
    #one block of free distance
    FREE_DISTANCE = 10

    def __init__(self, max_requests, max_request_size, active_tasks=None, queued_tasks=None):
        self.active_tasks = active_tasks if active_tasks else []
        self.queued_tasks = queued_tasks if queued_tasks else []
        self.__max_requests = max_requests
        self.__max_request_size = max_request_size

    def to_dict(self):
        return{
            "max_requests": self.__max_requests,
            "max_request_size": self.__max_request_size,
            "active_tasks": [task.to_dict() for task in self.active_tasks],
            "queued_tasks": [task.to_dict() for task in self.queued_tasks]
        }

    def add_task(self, type, node, distance, **kwargs):
        time = self.__distance_to_time(distance)
        if type == "Deliver":
            self.__split_request(NetworkDeliverTask, node, time, **kwargs)
        elif type == "Request":
            self.__split_request(NetworkRequestTask, node, time, **kwargs)
        else:
            raise Exception("Invalid type for network task {}".format(type))

    def __split_request(self, task_class, node, time, **kwargs):
        #split a taks into smaller tasks when to big for the piping.
        item = kwargs.pop("item")
        nr_requests = int(item.quantity / self.__max_request_size) + 1
        for _ in range(1, nr_requests):
            reduced_item = inventories.Item(item.material, self.__max_request_size)
            task = task_class(node, time, item=reduced_item, **kwargs)
            self.__add_to_task_queue(task)
        if item.quantity % self.__max_request_size != 0:
            reduced_item = inventories.Item(item.material, item.quantity % self.__max_request_size)
            task = task_class(node, time, item=reduced_item, **kwargs)
            self.__add_to_task_queue(task)

    def __add_to_task_queue(self, task):
        if len(self.active_tasks) <= self.__max_requests:
            self.active_tasks.append(task)
        else:
            self.queued_tasks.append(task)

    def __distance_to_time(self, distance):
        #1 mili second per pixel --> 10 per block
        return distance - self.FREE_DISTANCE

    def add_queue(self, task_queue):
        for task in task_queue.active_tasks + task_queue.queued_tasks:
            self.__add_to_task_queue(task)

    def work_tasks(self):
        for index in range(len(self.active_tasks) -1, -1, -1):
            self.active_tasks[index].work()
            if self.active_tasks[index].finished:
                del self.active_tasks[index]
                if len(self.queued_tasks) > 0:
                    self.active_tasks.append(self.queued_tasks.pop(0))


class NetworkTask(util.Serializer, ABC):
    def __init__(self, node, time, start_time=0):
        self.originating_node = node
        self.progress = [start_time, time]

    def to_dict(self):
        return {
            "time": self.progress[0],
            "start_time": self.progress[1],
            "originating_node_id": self.originating_node.id
        }

    @classmethod
    def from_dict(cls, buildings=None, **arguments):
        # TODO make node
        id = arguments.pop("originating_node_id")
        raise NotImplementedError
        return super().from_dict(**arguments)

    def work(self):
        if self.finished:
            return
        self.progress[0] += con.GAME_TIME.get_time()
        if self.finished:
            self._hand_in()

    @property
    def finished(self):
        return self.progress[1] < self.progress[0]

    @abstractmethod
    def _hand_in(self):
        pass

    def cancel(self):
        # make sure the task is finished
        self.progress[0] = self.progress[1] + 1


class NetworkDeliverTask(NetworkTask):
    def __init__(self, node, time, target_node, item):
        super().__init__(node, time)
        # inventory the item is delivered to
        self.__target_node = target_node
        # make sure to remove the items at the start
        self.deliver_item = item

    def to_dict(self):
        return super().to_dict().update({
            "item": self.deliver_item.to_dict()
        })

    def work(self):
        super().work()
        if self.__target_node.destroyed:
            self.cancel()

    def cancel(self):
        super().cancel()
        self.originating_node.inventory.add_items(self.deliver_item)

    def _hand_in(self):
        if self.__target_node.destroyed:
            self.cancel()
        else:
            self.__target_node.inventory.add_items(self.deliver_item)


class NetworkRequestTask(NetworkTask):
    def __init__(self, node, time, target_node, item):
        super().__init__(node, time)
        self.__target_node = target_node
        self.request_item = item

    def to_dict(self):
        return super().to_dict().update({
            "target_node_id": self.__target_node.id,
            "item": self.request_item.to_dict()
        })

    @classmethod
    def from_dict(cls, buildings=None, **arguments):
        id = arguments["target_node_id"]
        raise NotImplementedError
        return super().from_dict(buildings=buildings, **arguments)

    def work(self):
        super().work()
        if self.originating_node.destroyed:
            self.cancel()

    def cancel(self):
        super().cancel()
        self.__target_node.inventory.add_items(self.request_item)

    def _hand_in(self):
        if self.originating_node.destroyed:
            self.cancel()
        else:
            self.originating_node.inventory.add_items(self.request_item)
