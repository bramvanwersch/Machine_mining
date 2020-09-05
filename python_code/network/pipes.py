from python_code.utility.image_handling import image_sheets
from python_code.board.blocks import ContainerBlock
from python_code.utility.constants import BLOCK_SIZE

class Network:
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_NAMES = ["2_13", "2_02", "2_23", "2_03", "2_12", "2_01", "3_013", "3_012", "3_023", "3_123", "4_0123",
                   "1_3", "1_0", "1_1", "1_2", "0_"]
    def __init__(self):
        #connections between them
        self.edges = set()
        #furnaces chests etc.
        self.nodes = set()
        self.__pipe_images = self.__get_pipe_images()

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

    def add(self, block):
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
            new_edge.add_block(block)
            self.edges.add(new_edge)
        #merge
        else:
            new_edge = connected_edges.pop()
            new_edge.add_block(block)
            #merge any remaining edges that are also connected
            for rem_edge in connected_edges:
                new_edge.add_edge(rem_edge)
                self.edges.remove(rem_edge)

    def remove(self, block):
        for edge in self.edges:
            if block in edge:
                new_location_lists = edge.remove_segment(block)
                if len(edge.segments) == 0:
                    self.edges.remove(edge)
                for location_edge in new_location_lists:
                    new_edge = NetworkEdge(block.network_group)
                    new_edge.add_string_location(*location_edge)
                    self.edges.add(new_edge)
                break


class NetworkNode:
    def __init__(self):
        self.connected_edges = []


class NetworkEdge:
    #the innitial blocks are assumed to be the same group and connected.
    def __init__(self, group):
        self.segments = set()
        self.network_group = group

    def can_add(self, block):
        if self.network_group != block.network_group:
            return False
        loc = self.block_to_location_string(block)
        surrounding_locations = self.__surrounding_locations(loc)
        for l in surrounding_locations:
            if l in self.segments:
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