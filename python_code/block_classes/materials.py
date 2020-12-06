from abc import abstractmethod
from random import randint, choices
from typing import Set, Tuple, ClassVar, List, Dict

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
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 0

    _BLOCK_TYPE: ClassVar[BaseBlock] = Block
    BUILDABLE: ClassVar[bool] = True

    def __init__(self, image: pygame.Surface = None, **kwargs):
        self._surface = self._configure_surface(image=image)

        # allow transparant groups to be changed
        self.__transparant_group = self._BASE_TRANSPARANT_GROUP

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
    def transparant_group(self) -> int:
        return self.__transparant_group

    @transparant_group.setter
    def transparant_group(self, value: int) -> None:
        self.__transparant_group = value

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

    def to_block(self, pos: Tuple[int, int], **kwargs):
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
    """class that holds a collection of items that are randomly returned based on wheights this is mainly meant for
     board generation purposes"""

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self) -> Dict[str, float]:
        pass

    @classmethod
    def name(cls) -> str:
        """Choose a name at random from the collection using wheight defined in this collection"""
        # noinspection PyUnresolvedReferences
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

    # noinspection PyPep8Naming
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
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 1
    _BLOCK_TYPE: ClassVar[BaseBlock] = AirBlock
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = INVISIBLE_COLOR[:-1]

    def _configure_color(self):
        return self.BASE_COLOR

    def _configure_border_color(self):
        return self.BASE_COLOR


class BorderMaterial(ColorMaterial):
    """Blocks at the border of the board"""
    _ALLOWED_TASKS: ClassVar[Set] = set()
    BASE_COLOR: ClassVar[Tuple[int, int, int]] = (0, 0, 0)
    MIN_COLOR: ClassVar[Tuple[int, int, int]] = (0, 0, 0)


class ImageMaterial(BaseMaterial, ABC):
    """Materials displaying an image"""

    def _configure_surface(self, image: pygame.Surface = None) -> pygame.Surface:
        """Show an image as a surface instead of a single color"""
        if image is not None:
            return image
        # if an image is provided return that otherwise a debugging color signifying the image is missing
        else:
            surface = pygame.Surface(BLOCK_SIZE)
            surface.fill((255, 0, 255))
            return surface


class CancelMaterial(ImageMaterial):
    """Material displaying a stop sign like image to be used to stop crafting"""
    _ALLOWED_TASKS: ClassVar[Set] = set()

    def _configure_surface(self, image: pygame.Surface = None) -> pygame.Surface:
        image = image_sheets["materials"].image_at((20, 20))
        return image


class UnbuildableMaterial(ImageMaterial):
    """Materials that are unplacable. Do not have to eb part of a block neccesairily"""
    _ALLOWED_TASKS: ClassVar[Set] = {"Fetch", "Request", "Deliver"}
    BUILDABLE: ClassVar[bool] = False
