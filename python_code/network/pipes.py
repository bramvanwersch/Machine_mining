from math import ceil

from block_classes.blocks import ContainerBlock, NetworkBlock
from utility.constants import BLOCK_SIZE
from utility.utilities import manhattan_distance, Serializer
from block_classes import block_constants
from network.network_tasks import EdgeTaskQueue


class Network(Serializer):

    def __init__(self, edges=None, task_control=None):
        #connections between them
        self.edges = [self.__add_edge(e) for e in edges] if edges else set()
        #furnaces chests etc.
        self.nodes = [self.__add]
        self.task_control = task_control

    def to_dict(self):
        # nodes are added when buildings are readded trough the board
        return{
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, **arguments):
        arguments["edges"] = [NetworkEdge.from_dict(**dct) for dct in arguments["edges"]]
        return super().from_dict(**arguments)

    def update(self):
        for node in self.nodes:
            if node.requested_fuel > 0:
                self.request_fuel(node)
            if len(node.requested_items) > 0:
                self.request_items(node)
            if len(node.pushed_items) > 0:
                self.push_items(node)
        for edge in self.edges:
            edge.task_queue.work_tasks()

    def request_items(self, node):
        storage_connections = self.check_storage_connections(node)
        for s_node, distance, edge in storage_connections:
            items = self.__retrieve_with_pipes(node, s_node)
            for item in items:
                if item != None:
                    edge.task_queue.add_task("Request", node, distance, item=item, target_node=s_node)
            if len(node.requested_items) == 0:
                return
        for a_node in self.nodes:
            if not hasattr(a_node, "inventory"):
                continue
            self.__retrieve_with_task(node, a_node)
            if len(node.requested_items) == 0:
                break

    def request_fuel(self, node):
        for a_node in self.nodes:
            if not hasattr(a_node, "inventory"):
                continue
            for name in [f.name() for f in block_constants.fuel_materials]:
                item_pointer = a_node.inventory.item_pointer(name)
                if item_pointer == None:
                    continue
                max_needed = ceil(node.requested_fuel / item_pointer.FUEL_VALUE)

                #refers to the quantity needed or present
                present_quantity = min(max_needed, item_pointer.quantity)
                if present_quantity > 0:
                    requested_item = item_pointer.copy()
                    requested_item.quantity = present_quantity
                    node.requested_fuel -= max(0, item_pointer.FUEL_VALUE * present_quantity)
                    node.requested_fuel = max(node.requested_fuel, 0)
                    node.requested_items.append(requested_item)
                    node.inventory.in_filter.add_whitelist(requested_item.name())
                    if node.requested_fuel <= 0:
                        break

    def __retrieve_with_pipes(self, destination_node, node):
        items = []
        tot_len = len(destination_node.requested_items) - 1
        for index, item in enumerate(destination_node.requested_items[::-1]):
            #check if at least one item is present
            if node.inventory.check_item_get(item.name()):
                fetched_item = node.inventory.get(item.name(), item.quantity)
                if destination_node.requested_items[tot_len - index].quantity == fetched_item.quantity:
                    del destination_node.requested_items[tot_len - index]
                else:
                    destination_node.requested_items[tot_len - index].quantity -= fetched_item.quantity
                items.append(fetched_item)
        return items

    def __retrieve_with_task(self, destination_node, node):
        tot_len = len(destination_node.requested_items) - 1
        for index, item in enumerate(destination_node.requested_items[::-1]):
            if node.inventory.check_item_get(item.name()):
                #take top left block as target
                self.task_control.add("Request", destination_node.blocks[0][0], req_item=item)
                #request all items at once
                del destination_node.requested_items[tot_len - index]

    def push_items(self, node):
        storage_connections = self.check_storage_connections(node)
        for s_node, distance, edge in storage_connections:
            items = self.__push_with_pipe(s_node, node, distance)
            for item in items:
                if item != None:
                    edge.task_queue.add_task("Deliver", node, distance, item=item, target_node=s_node)
            if len(node.pushed_items) == 0:
                return
        for a_node in self.nodes:
            if not hasattr(a_node, "inventory"):
                continue
            self.__push_with_task(a_node, node)
            if len(node.pushed_items) == 0:
                break

    def __push_with_pipe(self, destination_node, node, distance):
        tot_len = len(node.pushed_items) - 1
        items = []
        for index, item in enumerate(node.pushed_items[::-1]):
            if destination_node.inventory.check_item_deposit(item.name()):
                get_item = node.inventory.get(item.name(), item.quantity)
                items.append(get_item)
                del node.pushed_items[tot_len - index]
        return items

    def __push_with_task(self, destination_node, node):
        tot_len = len(node.pushed_items) - 1
        for index, item in enumerate(node.pushed_items[::-1]):
            if destination_node.inventory.check_item_deposit(item.name()):
                del node.pushed_items[tot_len - index]
                self.task_control.add("Deliver", node.blocks[0][0], pushed_item = item)

    def check_storage_connections(self, node):
        storage_connections = []
        for edge in node.connected_edges:
            for c_node in edge.connected_nodes:
                if hasattr(c_node, "inventory") and c_node != node:
                    storage_connections.append([c_node, manhattan_distance(node.rect.center, c_node.rect.center), edge])
        storage_connections.sort(key=lambda x: x[1])
        return storage_connections

    def configure_block(self, block, surrounding_blocks, update=False, remove=False):
        """
        Configure the pipe image of a newly added pipe and return a list of surrounding pipes that
        need to be reevaluated if update is True

        :param block: a Block instance
        :param surrounding_blocks: a list of len 4 of surrounding block_classes of the current block
        :param update: A boolean that signifies if a list of surrounding block_classes need to be retuened to
        update
        :param remove: if the block is removed or not.
        :return: a list Blocks that need an update to theire surface
        """
        direction_indexes = [str(i) for i in range(len(surrounding_blocks)) if isinstance(surrounding_blocks[i], NetworkBlock)]
        direction_indexes = "".join(direction_indexes)
        image_name = "{}_{}".format(len(direction_indexes), direction_indexes)
        if not remove:
            block.material.image_key = image_name
        if update:
            return [surrounding_blocks[i] for i in range(len(surrounding_blocks)) if isinstance(surrounding_blocks[i], NetworkBlock)\
                    and not isinstance(surrounding_blocks[i], ContainerBlock)]
        return []

    def add_pipe(self, block):
        connected_edges = []
        for edge in self.edges:
            if edge.can_add(block):
                connected_edges.append(edge)
                #max possible connections
                if len(connected_edges) == 4:
                    break
        #if no edges are connected add a new edge
        if len(connected_edges) == 0:
            new_edge = NetworkEdge(block.network_group)
            new_edge.add_blocks(block)
            self.__add_edge(new_edge)
        #merge
        else:
            new_edge = connected_edges.pop()
            new_edge.add_blocks(block)
            #merge any remaining edges that are also connected
            for rem_edge in connected_edges:
                new_edge.add_edge(rem_edge)
                self.__remove_edge(rem_edge)
        #make sure that new pipes are potentially connected to nodes
        for node in self.nodes:
            if node not in new_edge.connected_nodes and new_edge.is_node_adjacent(node):
                node.add_edge(new_edge)

    def remove_pipe(self, block):
        for edge in self.edges:
            if block in edge:
                new_edges = edge.remove_segment(block)
                if len(edge.segments) == 0:
                    self.__remove_edge(edge)
                else:
                    for node in edge.connected_nodes.copy():
                        if not edge.is_node_adjacent(node):
                            node.remove_edge(edge)
                for n_edge in new_edges:
                    self.__add_edge(n_edge)
                break

    def __add_edge(self, new_edge):
        self.edges.add(new_edge)
        for node in self.nodes:
            if new_edge.is_node_adjacent(node):
                node.add_edge(new_edge)
        return new_edge

    def __remove_edge(self, edge):
        self.edges.remove(edge)
        for node in self.nodes:
            if edge in node:
                node.remove_edge(edge)

    def add_node(self, building):
        self.nodes.add(building)
        building.destroyed = False
        for edge in self.edges:
            if edge.is_node_adjacent(building):
                building.add_edge(edge)

    def remove_node(self, building):
        self.nodes.remove(building)
        building.destroyed = True
        for edge in building.connected_edges:
            edge.connected_nodes.remove(building)


class NetworkNode:
    def __init__(self):
        self.connected_edges = set()
        #a list of item objects that are requested to be delivered
        self.requested_items = []
        #items that are pushed to the be pushed away
        self.pushed_items = []
        #fuel that is needed, can be anything that act as fuel
        self.requested_fuel = 0
        #flag to let tasks know not to push items to this node
        self.destroyed = False

    def __contains__(self, edge):
        return edge in self.connected_edges

    def add_edge(self, edge):
        self.connected_edges.add(edge)
        edge.connected_nodes.add(self)

    def remove_edge(self, edge):
        self.connected_edges.remove(edge)
        edge.connected_nodes.remove(self)


class NetworkEdge(Serializer):
    #TODO make this cinfigure based on worst pipe. this is temporary
    MAX_REQUESTS = 10
    MAX_REQUEST_SIZE = 4
    # the innitial block_classes are assumed to be the same group and connected.

    def __init__(self, group, segments=None, task_queue=None):
        self.network_group = group
        self.segments = segments if segments else set()
        # will be done when adding the buildings back
        self.connected_nodes = set()
        self.task_queue = task_queue if task_queue else EdgeTaskQueue(self.MAX_REQUESTS, self.MAX_REQUEST_SIZE)

    def to_dict(self):
        return {
            "segments": [s.to_dict() for s in self.segments],
            "group": self.network_group,
            "task_queue": self.task_queue.to_dict()
        }

    @classmethod
    def from_dict(cls, **arguments):
        arguments["segments"] = [Segment.from_dict(**dct) for dct in arguments["segments"]]
        arguments["task_queue"] = EdgeTaskQueue.from_dict(**arguments["task_queue"])
        return super().from_dict(**arguments)

    def get_block_coordinates(self):
        return [segment.loc for segment in self.segments]

    def can_add(self, block):
        if self.network_group != block.network_group:
            return False
        segment = Segment(block.rect.topleft)
        surrounding_segments = segment.surrounding_segments()
        for segment in surrounding_segments:
            if segment in self.segments:
                return True
        return False

    def is_node_adjacent(self, node):
        for row in node.blocks:
            for block in row:
                if self.can_add(block):
                    return True
        return False

    def add_blocks(self, *blocks):
        for block in blocks:
            segment = Segment(block.rect.topleft)
            self.segments.add(segment)

    def add_segments(self, *segments):
        self.segments.update(segments)

    def add_edge(self, network_edge):
        for loc in network_edge.segments:
            self.segments.add(loc)
        # edge removal wiil be done
        for node in network_edge.connected_nodes:
            node.add_edge(self)
        self.task_queue.add_queue(network_edge.task_queue)

    def __contains__(self, block):
        segment = Segment(block.rect.topleft)
        return segment in self.segments

    def remove_segment(self, block):
        segment = Segment(block.rect.topleft)
        self.segments.remove(segment)
        surrounding_segments = [seg for seg in segment.surrounding_segments() if seg in self.segments]
        if len(surrounding_segments) <= 1:
            return []
        else:
            new_edges = self.check_connected(surrounding_segments)
            if len(new_edges) > 0:
                self.segments = new_edges.pop().segments
                return new_edges
            else:
                self.segments = set()
                return []

    def check_connected(self, segments):
        segments = set(segments)
        unused_segments = self.segments.copy()
        new_edges = []
        while len(segments) > 0:
            check_locations = [segments.pop()]
            used_segments = {check_locations[0]}
            while len(check_locations) > 0:
                segment = check_locations.pop()
                surrounding_segments = Segment(segment.loc).surrounding_segments()
                for segment in surrounding_segments:
                    if segment in unused_segments:
                        used_segments.add(segment)
                        unused_segments.remove(segment)
                        check_locations.append(segment)
                        if segment in segments:
                            segments.remove(segment)
            #create a new edge
            if len(used_segments) > 0:
                new_edge = NetworkEdge(self.network_group)
                new_edge.add_segments(*used_segments)
                new_edges.append(new_edge)
        return new_edges

    def __len__(self):
        return len(self.segments)


class Segment(Serializer):
    def __init__(self, loc):
        self.loc = tuple(loc)

    def to_dict(self):
        return{
            "loc": self.loc
        }

    def __hash__(self):
        return hash(self.loc)

    def __eq__(self, other):
        return self.loc == other.loc

    def surrounding_segments(self):
        segments = []
        for offset in [[-BLOCK_SIZE.width, 0], [0, BLOCK_SIZE.height], [BLOCK_SIZE.width, 0], [0, -BLOCK_SIZE.height]]:
            segments.append(Segment([self.loc[0] - offset[0], self.loc[1] - offset[1]]))
        return segments

    def __str__(self):
        return "{}_{}".format(*self.loc)
