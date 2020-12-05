from abc import abstractmethod
from random import randint, choices
from typing import Set, Tuple, ClassVar, List

from utility.constants import SHOW_BLOCK_BORDER, MINING_SPEED_PER_HARDNESS, INVISIBLE_COLOR
from utility.image_handling import image_sheets
from block_classes.blocks import *


class BaseMaterial(ABC):
    """
    Base material class that defines the behaviour of a block
    """
    HARDNESS: ClassVar[int] = 1
    WHEIGHT: ClassVar[int] = 1

    # all task types that are allowed for a block with this material
    _ALLOWED_TASKS: ClassVar[Set] = {"Mining", "Building", "Cancel", "Selecting",
                                     "Empty inventory", "Fetch", "Request", "Deliver"}

    # used by widgets for display TODO see if this can maybe move
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (0, 0, 0)
    # group 0 are not transparant
    TRANSPARANT_GROUP: ClassVar[int] = 0

    _BLOCK_TYPE: ClassVar[BaseBlock] = Block
    BUILDABLE: ClassVar[bool] = True

    def __init__(self, image=None, **kwargs):
        self._surface = self._configure_surface(image=image)
        self.transparant_group = self.TRANSPARANT_GROUP

    @property
    def hardness(self) -> int:
        return self.HARDNESS

    @property
    def wheight(self) -> int:
        return self.WHEIGHT

    @property
    def allowed_tasks(self) -> Set:
        return self._ALLOWED_TASKS

    @property
    def buildable(self) -> bool:
        return self.BUILDABLE

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @property
    def surface(self) -> pygame.Surface:
        # allow inheriting classes to push muliple surfaces or a choice
        return self._surface

    def to_block(self, pos, **kwargs):
        """Convert a material into the appropriate block

        Args:
            pos (list): lenght 2 list of the block position
            **kwargs: optional arguments for the block class
        Returns:
            an instance of a Block class
        """
        return self._BLOCK_TYPE(pos, self, **kwargs)

    @abstractmethod
    def _configure_surface(self, image: pygame.Surface = None) -> pygame.Surface:
        """Configure the surface if the material on instantiation"""
        pass

    @property
    def mining_speed(self) -> float:
        """Mili seconds needed to mine a block with this material"""
        return self.HARDNESS * MINING_SPEED_PER_HARDNESS


class MaterialCollection(ABC):
    # class that holds a collection of items that are randomly returned based on wheights
    # this is mainly meant for board generation purposes

    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self):
        return None

    @classmethod
    def name(cls) -> str:
        """Choose a name at random from the collection using wheight defined in this collection"""
        return choices([k.name() for k in cls.MATERIAL_PROBABILITIES.keys()],
                       cls.MATERIAL_PROBABILITIES.values(), k=1)[0]

    def __getattr__(self, item):
        return getattr(list(self.MATERIAL_PROBABILITIES.keys())[0], item)

    def __contains__(self, item):
        return item in self.MATERIAL_PROBABILITIES


class ColorMaterial(BaseMaterial, ABC):
    """
    Materials can inherit this when they simply are one color
    """
    MIN_COLOR = (20, 20, 20)

    def __init__(self, **kwargs):
        self.__color = self._configure_color()
        super().__init__(**kwargs)

    @property
    @abstractmethod
    def BASE_COLOR(self) -> Tuple[int, int, int]:
        return 0, 0, 0

    def _configure_surface(self, image: pygame.Surface = None) -> pygame.Surface:
        """Create a surface that is of a single color based on the self.__color"""
        surface = pygame.Surface(BLOCK_SIZE)
        surface.fill(self.__color)
        if SHOW_BLOCK_BORDER:
            pygame.draw.rect(surface, self._configure_border_color(), (0, 0, BLOCK_SIZE.width, BLOCK_SIZE.height), 1)
        return surface.convert()

    def _configure_color(self) -> List:
        """Create a color that becomes darker when the depth becomes bigger and with some random change in color.

        Returns:
             a list of lenght 3 with a r, g and b value as integers
        """
        new_color = list(self.BASE_COLOR)
        random_change = randint(-10, 10)
        # dont change the alpha channel if present
        for index, color_component in enumerate(self.BASE_COLOR):
            # make the color darker with depth and add a random component to it
            color_component = max(self.MIN_COLOR[index], color_component + random_change)
            new_color[index] = int(color_component)
        return new_color

    def _configure_border_color(self) -> List:
        """The color of the border that is slightly darker then the base color

        Returns:
             a list of lenght 3 with a r, g and b value as integers
        """
        new_color = list(self.BASE_COLOR)
        for index, color_component in enumerate(self.BASE_COLOR):
            color_component = max(0, color_component - 30)
            new_color[index] = color_component
        return new_color


class Air(ColorMaterial):
    _ALLOWED_TASKS: ClassVar[Set] = {task for task in BaseMaterial._ALLOWED_TASKS if task not in ["Mining"]}
    HARDNESS: ClassVar[int] = 0
    TRANSPARANT_GROUP: ClassVar[int] = 1
    _BLOCK_TYPE: ClassVar[BaseBlock] = AirBlock
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = INVISIBLE_COLOR[:-1]

    def _configure_color(self):
        return self.BASE_COLOR

    def _configure_border_color(self):
        return self.BASE_COLOR


class BorderMaterial(ColorMaterial):
    """Blocks at the borader of the board"""
    _ALLOWED_TASKS = set()
    BASE_COLOR = (0, 0, 0)
    MIN_COLOR = (0, 0, 0)


class ImageMaterial(BaseMaterial, ABC):
    """
    Materials can inherit from this when displaying an image
    """

    def _configure_surface(self, image):
        """
        Show an image as a surface instead of a single color

        :param image: optional pre defines pygame Surface object
        :return: a python Surface object
        """
        if image != None:
            return image
        #if an image is provided return that otherwise a color
        else:
            surface = pygame.Surface(BLOCK_SIZE)
            surface.fill((0, 255, 13))
            return surface


class CancelMaterial(ImageMaterial):

    def _configure_surface(self, image):
        image = image_sheets["materials"].image_at((20, 20), color_key=(255, 255, 255))
        return image


class UnbuildableMaterial(ImageMaterial):
    _ALLOWED_TASKS = ["Fetch", "Request", "Deliver"]
    BUILDABLE = False

