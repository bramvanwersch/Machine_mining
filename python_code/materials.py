from random import randint


class BaseMaterial:

    MIN_COLOR = (20, 20, 20)
    #time to perform a task on this material in ms
    TASK_TIME = 250
    WHEIGHT = 1
    def __init__(self, depth):
        if type(self) == BaseMaterial:
            raise Exception("Cannot instantiate abstract class BaseMaterial")
        self.__depth = depth
        self.color = self._configure_color()
        self.border_color = self._configure_border_color()

    def _configure_color(self):
        """
        Create a color that becomes darker when the depth becomes bigger and
        with some random change in color.

        :return: a tuple with a r, g and b value as integers
        """
        new_color = [0,0,0]
        random_change = randint(-10, 10)
        #dont change the alpha channel if present
        for index, color_component in enumerate(self.BASE_COLOR):
            #make the color darker with depth and add a random component to it
            color_component = max(self.MIN_COLOR[index], color_component - int(self.__depth / 2) + random_change)
            new_color[index] = color_component
        return new_color

    def _configure_border_color(self):
        """
        The color of the border that is slightly darker then the base color

        :return: a tuple with a r, g and b value as integers
        """
        new_color = [0,0,0]
        for index, color_component in enumerate(self.BASE_COLOR):
            color_component = max(0, color_component - int(self.__depth / 2) - 30)
            new_color[index] = color_component
        return new_color

    def task_time(self):
        """
        Return the task time plus a small random factor. To stagger the
        calculation times up to 10% of the task_time

        :return: the task time that the task will take in total
        """
        return self.TASK_TIME + randint(0, int(0.1 * self.TASK_TIME))


#filler materials
class Stone(BaseMaterial):

    BASE_COLOR = (155, 155, 155)
    NAME = "stone"
    def __init__(self, depth):
        super().__init__(depth)

class Dirt(BaseMaterial):

    BASE_COLOR = (107, 49, 13)
    NAME = "dirt"
    def __init__(self, depth):
        super().__init__(depth)


#ore materials
class Ore(BaseMaterial):
    """
    Abstract class for all ores. Contains a gaussian distribution for the
    likelyhood of a ore to be at certain percent depth
    """
    WHEIGHT = 2
    def __init__(self, depth):
        super().__init__(depth)
        if type(self) == Ore:
            raise Exception("Cannot instantiate abstract class Ore")

    def _configure_color(self):
        """
        Make sure the color is not changed

        :return: the base color
        """
        return self.BASE_COLOR

class Iron(Ore):

    MEAN_DEPTH = 50
    SD = 30
    CLUSTER_SIZE = (2, 10)
    BASE_COLOR = (184, 98, 92)
    NAME = "iron"
    WHEIGHT = 3
    def __init__(self, depth):
        super().__init__(depth)

class Gold(Ore):

    MEAN_DEPTH = 70
    SD = 3
    CLUSTER_SIZE = (2, 6)
    BASE_COLOR = (235, 173, 16)
    WHEIGHT = 5
    def __init__(self, depth):
        super().__init__(depth)

class Zinc(Ore):

    MEAN_DEPTH = 20
    SD = 5
    CLUSTER_SIZE = (2, 15)
    BASE_COLOR = (58, 90, 120)
    NAME = "zinc"
    def __init__(self, depth):
        super().__init__(depth)

class Copper(Ore):

    MEAN_DEPTH = 30
    SD = 5
    CLUSTER_SIZE = (5, 8)
    BASE_COLOR = (189, 99, 20)
    NAME = "copper"
    def __init__(self, depth):
        super().__init__(depth)

class Coal(Ore):

    MEAN_DEPTH = 10
    SD = 50
    CLUSTER_SIZE = (6, 12)
    BASE_COLOR = (10, 10, 10)
    NAME = "coal"
    def __init__(self, depth):
        super().__init__(depth)

class Titanium(Ore):

    MEAN_DEPTH = 100
    SD = 2
    CLUSTER_SIZE = (1, 2)
    BASE_COLOR = (152, 196, 237)
    NAME = "titanium"
    WHEIGHT = 10
    def __init__(self, depth):
        super().__init__(depth)
