#!/usr/bin/python3
"""Base material methods"""

# library imports
import pygame
from abc import ABC, abstractmethod
from random import randint, choices, choice
from typing import Set, Tuple, ClassVar, List, Dict, Any

# own imports
import utility.constants as con
import utility.image_handling as image_handling
import block_classes.blocks as blocks
import utility.utilities as util


class BaseMaterial(ABC):
    """
    Base material class that defines the behaviour of a block
    """
    HARDNESS: ClassVar[int] = 1
    WHEIGHT: ClassVar[int] = 1

    # all task types that are allowed for a block with this material
    ALLOWED_TASKS: ClassVar[Set] = {"Mining", "Building", "Cancel", "Selecting", "Fetch", "Request", "Deliver"}

    # used by widgets for display TODO see if this can maybe move
    TEXT_COLOR: ClassVar[Tuple[int, int, int]] = (0, 0, 0)
    # group 0 are not transparant
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 0

    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.Block
    BUILDABLE: ClassVar[bool] = True
    __slots__ = "_surface", "__transparant_group"

    _surface: pygame.Surface
    __transparant_group: int

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
        return self.ALLOWED_TASKS

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

    @property
    def full_surface(self) -> pygame.Surface:
        return self._surface

    @property
    def block_type(self) -> type:
        return self._BLOCK_TYPE

    def to_block(self, pos: List[int], **kwargs) -> blocks.Block:
        """Convert a material into the appropriate block with that material

        Args:
            pos (list): lenght 2 list of the block position
            **kwargs: optional arguments for the block class
        Returns:
            an instance of a Block class
        """
        return self._BLOCK_TYPE(pos, self, **kwargs)

    def is_solid(self) -> bool:
        """test if a material is considered solid or not"""
        return self.__transparant_group == 0

    @abstractmethod
    def _configure_surface(self, image: pygame.Surface = None) -> pygame.Surface:
        """Configure the surface if the material on instantiation"""
        pass

    @property
    def mining_speed(self) -> float:
        """Mili seconds needed to mine a block with this material"""
        return self.HARDNESS * con.MINING_SPEED_PER_HARDNESS


class MaterialCollection(ABC):
    """class that holds a collection of items that are randomly returned based on wheights this is mainly meant for
     board generation purposes"""
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self) -> Dict[str, float]:
        """Dictionary linking material name to to a probability of returning that name when the name() metod is
         called"""
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


class ColorDefinition:
    """Defines a range of colors based on input parameters, is optimized on order to prevent repeated color image
    creation"""
    BORDER_DARKER: ClassVar[int] = 20
    __slots__ = "__colors", "__images", "__surface_size", "__border_allowed"

    __images: List[pygame.Surface]
    __colors: List[Tuple[int, int, int]]
    __surface_size: util.Size
    __border_allowed: bool

    def __init__(
        self,
        base_color: Tuple[int, int, int],
        *additional_colors: Tuple[int, int, int],
        more_colors: bool = True,
        border: bool = True,
        min_color: Tuple[int, int, int] = (20, 20, 20),
        nr_colors: int = 10,
        change_range: Tuple[int, int] = (-10, 10),
        size: util.Size = con.BLOCK_SIZE
    ):
        if len(additional_colors) > 0 or not more_colors:
            self.__colors = [base_color, *additional_colors]
        else:
            self.__colors = self.__configure_colors(base_color, min_color, nr_colors, change_range)
        self.__surface_size = size
        self.__border_allowed = border
        self.__images = []

    def __configure_colors(self, base_color, min_color, nr_colors, change_range) -> List[Tuple[int, int, int]]:
        """Create a range of colors around a base color"""
        new_colors = list([base_color])
        for _ in range(nr_colors):
            random_change = randint(change_range[0], change_range[1])
            # dont change the alpha channel if present
            new_color = [0, 0, 0]
            for index, color_component in enumerate(base_color):
                # make the color darker with depth and add a random component to it
                color_component = max(min_color[index], color_component + random_change)
                new_color[index] = int(color_component)
            new_colors.append(new_color)
        return new_colors

    def colors(self) -> List[pygame.Surface]:
        """Create surfaces of a single color for all colors in self.__colors"""
        if len(self.__images) == 0:
            for color in self.__colors:
                image = pygame.Surface(self.__surface_size.size)
                image.fill(color)
                if con.SHOW_BLOCK_BORDER and self.__border_allowed:
                    pygame.draw.rect(image, self.__configure_border_color(color),
                                     (0, 0, self.__surface_size.width, self.__surface_size.height), 1)
                self.__images.append(image)
        return self.__images

    def __configure_border_color(self, color) -> List[int]:
        """The color of the border that is slightly darker then the base color

        Returns:
             a list of lenght 3 with a r, g and b value as integers
        """
        new_color = list(color)
        for index, color_component in enumerate(color):
            color_component = max(0, color_component - self.BORDER_DARKER)
            new_color[index] = color_component
        return new_color


class ColorMaterial(BaseMaterial, ABC):
    """
    Materials can inherit this when they simply are one color
    """
    COLOR_DEFINITIONS: ClassVar[ColorDefinition]

    _surface: List[pygame.Surface]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def COLOR_DEFINITIONS(self) -> ColorDefinition:
        pass

    def _configure_surface(self, image: pygame.Surface = None) -> List[pygame.Surface]:
        """the self._surface attribute is set to this value. For colors this is a list of possible colors"""
        return self.COLOR_DEFINITIONS.colors()

    @property
    def surface(self) -> pygame.Surface:
        """Return one of the colors at random"""
        return choice(self._surface)

    @property
    def full_surface(self) -> pygame.Surface:
        # make sure it is consistent
        return self._surface[0]


class Air(ColorMaterial):
    ALLOWED_TASKS: ClassVar[Set] = {task for task in BaseMaterial.ALLOWED_TASKS if task not in ["Mining"]}
    HARDNESS: ClassVar[int] = 0
    _BASE_TRANSPARANT_GROUP: ClassVar[int] = 1
    _BLOCK_TYPE: ClassVar[blocks.Block] = blocks.Block
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition(con.INVISIBLE_COLOR[:-1], more_colors=False,
                                                                   border=False)


class BorderMaterial(ColorMaterial):
    """Blocks at the border of the board"""
    ALLOWED_TASKS: ClassVar[Set] = set()
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((0, 0, 0), more_colors=False, border=False)


class ImageDefinition:
    """Define an image and make sure that image creation is not done repeatedly"""
    __slots__ = "__sheet_name", "__image_location", "__color_key", "__flip", "__size", "__image_size", "__images"

    __sheet_name: str
    __image_location: Tuple[int, int]
    __color_key: Tuple[int, int, int]
    __flip: bool
    # this varaible will save when get_images is called once before te prevent unnecesairy transform an image_at calls
    __images: List[pygame.Surface]
    __size: util.Size
    __image_size: util.Size

    def __init__(
        self,
        sheet_name: str,
        image_location: Tuple[int, int],
        color_key: Tuple[int, int, int] = None,
        flip: bool = False,
        image_size: util.Size = con.BLOCK_SIZE,
        size: util.Size = con.BLOCK_SIZE
    ):
        self.__sheet_name = sheet_name
        self.__image_location = image_location
        self.__color_key = color_key
        self.__flip = flip
        self.__size = size
        self.__image_size = image_size
        self.__images = []

    def images(self) -> List[pygame.Surface]:
        """Get/create all images defined by the image definition"""
        if len(self.__images) > 0:
            return self.__images
        return self.__create_images()

    def __create_images(self) -> List[pygame.Surface]:
        """Get defined images from image sheets and potentially scale and transform when neccesairy"""
        norm_image = image_handling.image_sheets[self.__sheet_name].image_at(
            self.__image_location, color_key=self.__color_key, size=self.__size)
        norm_size = norm_image.get_size()
        if norm_size[0] != self.__image_size[0] or norm_size[1] != self.__image_size[1]:
            norm_image = pygame.transform.scale(norm_image, self.__image_size.size)
        if self.__flip:
            flip_image = pygame.transform.flip(norm_image, True, False)
            self.__images = [norm_image, flip_image]
        else:
            self.__images = [norm_image]
        return self.__images


class ImageMaterial(BaseMaterial, ABC):
    """Materials displaying an image"""
    IMAGE_DEFINITIONS: ClassVar[ImageDefinition]

    _surface: List[pygame.Surface]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def IMAGE_DEFINITIONS(self) -> ImageDefinition:
        pass

    def _configure_surface(self, image: pygame.Surface = None) -> List[pygame.Surface]:
        """the self._surface attribute is set to this value. This is a list of possible images"""
        return self.IMAGE_DEFINITIONS.images()

    @property
    def surface(self) -> pygame.Surface:
        return choice(self._surface)

    @property
    def full_surface(self) -> pygame.Surface:
        # make sure it is consistent
        return self._surface[0]


class MultiImageMaterial(ImageMaterial, ABC):
    """Class for materials that have multiple images associated with them that can be bound to keys in a dictionary"""
    IMAGE_DEFINITIONS: ClassVar[Dict[Any, ImageDefinition]]
    __slots__ = "image_key"

    image_key: int
    _surface: Dict[Any, List[pygame.Surface]]

    def __init__(self, image_key: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.image_key = image_key if image_key else list(self.IMAGE_DEFINITIONS.keys())[0]

    def _configure_surface(self, image: pygame.Surface = None) -> Dict[Any, List[pygame.Surface]]:
        """the self._surface attribute is set to this value. This is dictionary of lists of possible images"""
        surfaces = dict()
        for name, image_defenition in self.IMAGE_DEFINITIONS.items():
            surfaces[name] = image_defenition.images()
        return surfaces

    @property
    def surface(self):
        return choice(self._surface[self.image_key])

    @property
    def full_surface(self) -> pygame.Surface:
        # make sure it is consistent
        return self._surface[self.image_key][0]


class CancelMaterial(ImageMaterial):
    """Material displaying a stop sign like image to be used to stop crafting"""
    ALLOWED_TASKS: ClassVar[Set] = set()
    IMAGE_DEFINITIONS: ClassVar[List[ImageDefinition]] = ImageDefinition("materials", (20, 20))


class Unbuildable(ABC):
    """Inherit material from this to make it unbuildable"""
    ALLOWED_TASKS: ClassVar[Set] = {"Fetch", "Request", "Deliver"}
    BUILDABLE: ClassVar[bool] = False


class DepthMaterial(ABC):
    """Abstract class for materials that are placed based on depth"""
    DISTRIBUTION: ClassVar[util.Gaussian]

    @classmethod
    def get_lh_at_depth(cls, depth: int) -> float:
        norm_depth = depth / con.MAX_DEPTH * 100
        # noinspection PyUnresolvedReferences
        lh = cls.DISTRIBUTION.probability(norm_depth)
        return lh

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def DISTRIBUTION(self) -> util.Gaussian:
        pass


class InventoryMaterial:
    ALLOWED_TASKS: ClassVar[Set] = BaseMaterial.ALLOWED_TASKS.union({"Empty inventory"})


class Indestructable:
    ALLOWED_TASKS: ClassVar[Set] = {task for task in BaseMaterial.ALLOWED_TASKS if task not in ["Building", "Mining"]}
