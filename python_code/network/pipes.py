from math import ceil

from python_code.utility.image_handling import image_sheets
from python_code.board.blocks import ContainerBlock, NetworkBlock
from python_code.utility.constants import BLOCK_SIZE
from python_code.utility.utilities import manhattan_distance
from python_code.board import materials
from python_code.network.network_tasks import EdgeTaskQueue


class Network:
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_NAMES = ["2_13", "2_02", "2_23", "2_03", "2_12", "2_01", "3_013", "3_012", "3_023", "3_123", "4_0123",
                   "1_3", "1_0", "1_1", "1_2", "0_"]
    def __init__(self, task_control):
        #connections between them
        self.edges = set()
        #furnaces chests etc.
        self.nodes = set()
        self.__pipe_images = self.__get_pipe_images()
        self.task_control = task_control

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
            for name in [f.name() for f in materials.fuel_materials]:
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

    def __get_pipe_images(self):
        images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10), color_key=(255,255,255))[0]
        images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10), color_key=(255,255,255))[0])
        return {self.IMAGE_NAMES[i] : images[i] for i in range(len(images))}

    def configure_block(self, block, surrounding_blocks, update=False, remove=False):
        """
        Configure the pipe image of a newly added pipe and return a list of surrounding pipes that
        need to be reevaluated if update is True

        :param block: a Block instance
        :param surrounding_blocks: a list of len 4 of surrounding blocks of the current block
        :param update: A boolean that signifies if a list of surrounding blocks need to be retuened to
        update
        :param remove: if the block is removed or not.
        :return: a list Blocks that need an update to theire surface
        """
        direction_indexes = [str(i) for i in range(len(surrounding_blocks)) if isinstance(surrounding_blocks[i], NetworkBlock)]
        direction_indexes = "".join(direction_indexes)
        image_name = "{}_{}".format(len(direction_indexes), direction_indexes)
        if not remove:
            block.surface = self.__pipe_images[image_name]
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


class NetworkEdge:
    #TODO make this cinfigure based on worst pipe. this is temporary
    MAX_REQUESTS = 10
    MAX_REQUEST_SIZE = 4
    #the innitial blocks are assumed to be the same group and connected.
    def __init__(self, group):
        self.segments = set()
        self.network_group = group
        self.connected_nodes = set()
        self.task_queue = EdgeTaskQueue(self.MAX_REQUESTS, self.MAX_REQUEST_SIZE)

    def can_add(self, block):
        if self.network_group != block.network_group:
            return False
        loc = self.block_to_location_string(block)
        surrounding_locations = self.__surrounding_locations(loc)
        for l in surrounding_locations:
            if l in self.segments:
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
            loc = self.block_to_location_string(block)
            self.segments.add(loc)

    def add_string_location(self, *locations):
        for location in locations:
            self.segments.add(location)

    def add_edge(self, network_edge):
        for loc in network_edge.segments:
            self.segments.add(loc)
        #edge removal wiil be done
        for node in network_edge.connected_nodes:
            node.add_edge(self)
        self.task_queue.add_queue(network_edge.task_queue)

    def __contains__(self, block):
        loc  = self.block_to_location_string(block)
        return loc in self.segments

    def remove_segment(self, block):
        loc = self.block_to_location_string(block)
        self.segments.remove(loc)
        sur_locs = [loc for loc in self.__surrounding_locations(loc) if loc in self.segments]
        if len(sur_locs) <= 1:
            return []
        else:
            new_edges = self.check_connected(sur_locs)
            if len(new_edges) > 0:
                self.segments = new_edges.pop().segments
                return new_edges
            else:
                self.segments = set()
                return []

    def check_connected(self, locations):
        locations = set(locations)
        unused_segments = self.segments.copy()
        new_edges = []
        while len(locations) > 0:
            check_locations = [locations.pop()]
            used_segments = set([check_locations[0]])
            while len(check_locations) > 0:
                loc = check_locations.pop()
                sur_locs = self.__surrounding_locations(loc)
                for sur_loc in sur_locs:
                    if sur_loc in unused_segments:
                        used_segments.add(sur_loc)
                        unused_segments.remove(sur_loc)
                        check_locations.append(sur_loc)
                        if sur_loc in locations:
                            locations.remove(sur_loc)
            #create a new edge
            if len(used_segments) > 0:
                new_edge = NetworkEdge(self.network_group)
                new_edge.add_string_location(*used_segments)
                new_edges.append(new_edge)
        return new_edges

    def __surrounding_locations(self, location):
        locations = []
        number_location = self.location_string_to_number_location(location)
        for offset in [[-1,0],[0,1],[1,0],[0,-1]]:
            locations.append([number_location[0] - offset[0], number_location[1] - offset[1]])
        locations = [self.location_number_to_location_string(l) for l in locations]
        return locations

    def block_to_location_string(self, block):
        """
        Transform a location into a hashable string that can be created from
        a block

        :param block: a Block objects
        :return: a string
        """
        return str("{}_{}".format(int(block.rect.left / BLOCK_SIZE.width), int(block.rect.top / BLOCK_SIZE.height)))

    def location_string_to_number_location(self, location):
        return list(map(int, location.split("_")))

    def location_number_to_location_string(self, location):
        return "{}_{}".format(*location)

    def __len__(self):
        return len(self.segments)