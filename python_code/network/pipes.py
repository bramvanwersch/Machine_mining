from python_code.utility.image_handling import image_sheets
from python_code.board.blocks import ContainerBlock

class Network:
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_NAMES = ["2_13", "2_02", "2_23", "2_03", "2_12", "2_01", "3_013", "3_012", "3_023", "3_123", "4_0123",
                   "1_3", "1_0", "1_1", "1_2", "0_"]
    def __init__(self):
        #connections between them
        self.edges = []
        #furnaces chests etc.
        self.nodes = []
        self.__pipe_images = self.__get_pipe_images()

    def __get_pipe_images(self):
        images = image_sheets["materials"].images_at_rectangle((10, 0, 90, 10), color_key=(255,255,255))[0]
        images.extend(image_sheets["materials"].images_at_rectangle((0, 10, 70, 10), color_key=(255,255,255))[0])
        return {self.IMAGE_NAMES[i] : images[i] for i in range(len(images))}

    def configure_block(self, block, surrounding_blocks, update=False):
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
        added = False
        for edge in self.edges:
            if edge.can_add(block):
                edge.add_segment(block)
                added = True
                break
        if not added:
            self.edges.append(NetworkEdge(block))

    def remove(self, block):
        pass


class NetworkNode:
    def __init__(self):
        self.connected_edges = []


class NetworkEdge:
    def __init__(self, block):
        loc = self.get_location(block)
        self.segments = {loc}
        self.network_group = block.network_group

    def can_add(self, block):
        if self.network_group != block.network_group:
            return False
        loc = self.get_location(block)
        surrounding_locations = self.__surrounding_locations(loc)
        for l in surrounding_locations:
            if l in self.segments:
                return True
        return False

    def add_segment(self, block):
        loc = self.get_location(block)
        self.segments.add(loc)

    def __contains__(self, item):
        return item in self.segments

    def remove_segment(self, block):
        loc = self.get_location(block)
        self.segments.remove(loc)
        sur_locs = self.__surrounding_locations(loc)
        if len(locations) <= 1:
            return []
        else:
            new_edges = self.check_connected(sur_locs)
            self.segments = new_edges.pop()
            return new_edges

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
                        used_segments.add(unused_segments.pop(sur_loc))
                        check_locations.append(sur_loc)
                        #max 3 comparissons
                        if sur_loc in locations:
                            locations.remove(sur_loc)
                            if len(locations) == 0:
                                break
                if len(locations) == 0:
                    break

            new_edges.append(used_segments)
        return new_edges

    def __surrounding_locations(self, location):
        locations = []
        for offset in [[-1,0],[0,1],[1,0],[0,-1]]:
            locations.append([location[0] - offset[0], locationp[1] - offset[1]])
        return location

    def get_location(self, block):
        return [int(block.rect.left / 10), int(block.rect.top / 10)]