from python_code.utility.image_handling import image_sheets

class Network:
    # made as follows:
    # first number for the amount of connections (0, 1, 2, 3, 4)
    # then 2 to 4 letters for n = 0, e = 1, s = 2, w = 3, with that order
    IMAGE_NAMES = ["2_13", "2_02", "2_23", "2_03", "2_12", "2_01", "3_013", "3_012", "3_023", "3_123", "4_0123",
                   "1_3", "1_0", "1_1", "1_2", "0_"]
    DIRECTION_NAMES = "NESW"
    def __init__(self):
        self.pipes = []
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
        direction_indexes = [str(i) for i in range(len(surrounding_blocks)) if surrounding_blocks[i] == block]
        direction_indexes = "".join(direction_indexes)
        image_name = "{}_{}".format(len(direction_indexes), direction_indexes)
        block.surface = self.__pipe_images[image_name]
        if update:
            return [surrounding_blocks[i] for i in range(len(surrounding_blocks)) if surrounding_blocks[i] == block]
        return None


