from python_code.utility.image_handling import image_sheets
from python_code.board.blocks import ContainerBlock
from python_code.utility.constants import BLOCK_SIZE
from python_code.utility.utilities import manhattan_distance
from python_code.board import materials

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
            if len(node.requested_items) > 0:
                self.request_items(node)
            if len(node.pushed_items) > 0:
                self.push_items(node)

    def request_items(self, node):
        storage_nodes = self.check_connected_storage_get(node)
        for s_node in storage_nodes:
            items = self.__retrieve_with_pipes(node, s_node)
            node.inventory.add_items(*items)
            if len(node.requested_items) == 0:
                return
        for a_node in self.nodes:
            if not hasattr(a_node, "inventory"):
                continue
            self.__retrieve_with_task(node, a_node)
            if len(node.requested_items) == 0:
                break

    def __retrieve_with_pipes(self, destination_node, node):
        items = []
        tot_len = len(destination_node.requested_items) - 1
        # TODO make a system to make this time dependant based on pipe lenght
        for index, item_name in enumerate(destination_node.requested_items[::-1]):
            #check if at least one item is present
            if node.inventory.check_item_get(item_name, 1):
                fetched_item = node.inventory.get(item_name, quantity)
                if destination_node.requested_items[tot_len - index].quantity == fetched_item.quantity:
                    del destination_node.requested_items[tot_len - index]
                else:
                    destination_node.requested_items[tot_len - index].quantity -= fetched_item.quantity
                items.append(fetched_item)
        return items

    def __retrieve_with_task(self, destination_node, node):
        tot_len = len(destination_node.requested_items) - 1
        for index, item in enumerate(destination_node.requested_items[::-1]):
            if node.inventory.check_item_get(item.name(), 1):
                #take top left block as target
                self.task_control.add("Request", destination_node.blocks[0][0], req_material=item)
                #request all items at once
                del destination_node.requested_items[tot_len - index]

    def push_items(self, node):
        storage_nodes = self.check_connected_storage_get(node)
        for s_node in storage_nodes:
            self.__push_items_with_pipe(s_node, node)
            if len(node.pushed_items) == 0:
                return
        for a_node in self.nodes:
            if not hasattr(a_node, "inventory"):
                continue
            self.__push_with_task(a_node, node)
            if len(node.pushed_items) == 0:
                break

    def __push_items_with_pipe(self, destination_node, node):
        tot_len = len(node.pushed_items) - 1
        for index, item in enumerate(node.pushed_items[::-1]):
            #TODO make this time dependant on pipe lenght
            if destination_node.inventory.check_item_deposit(item):
                destination_node.inventory.add_items(item)
                del node.pushed_items[tot_len - index]
                node.inventory.get(item.name(), item.quantity)

    def __push_with_task(self, destination_node, node):
        tot_len = len(node.pushed_items) - 1
        for index, item in enumerate(node.pushed_items[::-1]):
            print(item)
            if destination_node.inventory.check_item_deposit(item.name()):
                del node.pushed_items[tot_len - index]
                self.task_control.add("Deliver", node.blocks[0][0], pushed_item = item)

    def check_connected_storage_get(self, node):
        storage_nodes = []
        for c_nodes in node.connected_edges.values():
            for c_node in c_nodes:
                if hasattr(c_node, "inventory"):
                    storage_nodes.append(node)
        storage_nodes.sort(key=lambda x: manhattan_distance(node.rect.center, x.rect.center))
        return storage_nodes

    def __get_pipe_images(self):
        images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10), color_key=(255,255,255))[0]
        images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10), color_key=(255,255,255))[0])
        return {self.IMAGE_NAMES[i] : images[i] for i in range(len(images))}

    def configure_block(self, block, surrounding_blocks, update=False, add=False, remove=False):
        """
        Configure the pipe image of a newly added pipe and return a list of r=surrounding pipes that
        need to be reevaluated if update is True

        :param block: a Block instance
        :param surrounding_blocks: a list of len 4 of surrounding blocks of the current block
        :param update: A boolean that signifies if a list of surrounding blocks need to be retuened to
        update
        :return: None or a list Blocks that need an update to theire surface
        """
        direction_indexes = [str(i) for i in range(len(surrounding_blocks)) if surrounding_blocks[i] == block or \
                             isinstance(surrounding_blocks[i], ContainerBlock)]
        direction_indexes = "".join(direction_indexes)
        image_name = "{}_{}".format(len(direction_indexes), direction_indexes)
        block.surface = self.__pipe_images[image_name]
        if update:
            return [surrounding_blocks[i] for i in range(len(surrounding_blocks)) if surrounding_blocks[i] == block]
        return None

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
            new_edge = self.__add_edge(block)
        #merge
        else:
            new_edge = connected_edges.pop()
            new_edge.add_block(block)
            #merge any remaining edges that are also connected
            for rem_edge in connected_edges:
                new_edge.add_pipe(rem_edge)
                self.__remove_edge(edge)
        #make sure that new pipes are potentially connected to nodes
        for node in self.nodes:
            if new_edge.is_node_adjacent(node):
                node.add_edge(new_edge)

    def __remove_edge(self, edge):
        self.edges.remove(edge)
        for node in self.nodes:
            if edge in node:
                node.remove_edge(edge)

    def __add_edge(self, block):
        new_edge = NetworkEdge(block.network_group)
        new_edge.add_block(block)
        self.edges.add(new_edge)
        for node in self.nodes:
            if new_edge.is_node_adjacent(node):
                node.add_edge(new_edge)
        return new_edge

    def add_node(self, building):
        self.nodes.add(building)
        for edge in self.edges:
            if edge.is_node_adjacent(building):
                building.add_edge(edge)

    def remove(self, block):
        for edge in self.edges:
            if block in edge:
                new_location_lists = edge.remove_segment(block)
                if len(edge.segments) == 0:
                    self.__remove_edge(edge)
                for location_edge in new_location_lists:
                    self.__add_edge(block)
                break


class NetworkNode:
    def __init__(self):
        self.connected_edges = {}
        #a list of item objects that are requested to be delivered
        self.requested_items = []
        #items that are pushed to the be pushed away
        self.pushed_items = []

    def __contains__(self, edge):
        return edge in self.connected_edges

    def add_edge(self, edge):
        self.connected_edges[edge] = {}
        for node in edge.connected_nodes:
            self.connected_edges[edge][node] = manhattan_distance(self.rect.center, node.rect.center)
        edge.connected_nodes.add(self)

    def remove_edge(self, edge):
        del self.connected_edges[edge]
        edge.connected_nodes.remove(self)


class NetworkEdge:
    #the innitial blocks are assumed to be the same group and connected.
    def __init__(self, group):
        self.segments = set()
        self.network_group = group
        self.connected_nodes = set()

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
            for block in node:
                if self.can_add(block):
                    return True
        return False

    def add_block(self, *blocks):
        for block in blocks:
            loc = self.block_to_location_string(block)
            self.segments.add(loc)

    def add_string_location(self, *locations):
        for location in locations:
            self.segments.add(location)

    def add_edge(self, network_edge):
        for loc in network_edge.segments:
            self.segments.add(loc)

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
                self.segments = new_edges.pop()
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
            used_segments = set()
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
            if len(used_segments) > 0:
                new_edges.append(used_segments)
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