#!/usr/bin/python3
"""Base material methods"""

# library imports
import pygame
from abc import ABC, abstractmethod
from random import randint, choices, choice
from typing import Set, Tuple, ClassVar, List, Dict, Any, Union

# own imports
import utility.constants as con
import block_classes.blocks as blocks
import utility.utilities as util
from utility.image_handling import ImageDefinition


class BaseMaterial(ABC):
    """
    Base material class that defines the behaviour of a block
    """
    __slots__ = "_surface", "_active_surface", "__transparant_group", "_active"
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

    _surface: pygame.Surface
    __transparant_group: int

    def __init__(self, **kwargs):
        self._surface = self._configure_surface()
        self._active_surface = self._configure_active_surface()

        # transparant groups are allowed to be changed
        self.__transparant_group = self._BASE_TRANSPARANT_GROUP

        # flag that controls if the active or the normal surfaces are returned. Surfaces have to actively be redrawn
        self._active = False

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

    def to_block(self, pos: Union[List[int], Tuple[int, int]], **kwargs) -> blocks.Block:
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

    def tooltip_text(self) -> str:
        return f"{self.name()} ({'solid' if self.is_solid() else 'transparant'})\n" \
               f"Wheight: {self.wheight}kg"

    @abstractmethod
    def _configure_surface(self) -> pygame.Surface:
        """Configure the surface of the material on instantiation"""
        pass

    @abstractmethod
    def _configure_active_surface(self) -> Union[List[pygame.Surface], None]:
        """A surface that can be used to display the active state of a block"""
        pass

    @property
    def mining_speed(self) -> float:
        """Mili seconds needed to mine a block with this material"""
        return self.HARDNESS * con.MINING_SPEED_PER_HARDNESS

    def copy(self, **kwargs):
        return type(self)(**kwargs)

    @property
    def active(self) -> bool:
        return self._active

    def set_active(
        self,
        value: bool
    ):
        if self._active_surface is None:
            raise util.GameException(f"Material {type(self)} has no ACTIVE_IMAGE_DEFINITION and as a result can not"
                                     f"be set active")
        self._active = value


class ColorDefinition:
    """Defines a range of colors based on input parameters, is optimized in order to prevent repeated color image
    creation"""
    BORDER_DARKER: ClassVar[int] = 20
    MAX_COLOR_COMPONENT: ClassVar[int] = 255
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
        image_size: util.Size = con.BLOCK_SIZE
    ):
        if len(additional_colors) > 0 or not more_colors:
            self.__colors = [base_color, *additional_colors]
        else:
            self.__colors = self.__configure_colors(base_color, min_color, nr_colors, change_range)
        self.__surface_size = image_size
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
                # make sure the color componenet is valid
                color_component = max(0, min(self.MAX_COLOR_COMPONENT, color_component))
                new_color[index] = int(color_component)
            new_colors.append(new_color)
        return new_colors

    def images(self) -> List[pygame.Surface]:
        """Create surfaces of a single color for all colors in self.__colors"""
        if len(self.__images) == 0:
            for color in self.__colors:
                if len(color) == 3:
                    image = pygame.Surface(self.__surface_size.size).convert()
                elif len(color) == 4:
                    image = pygame.Surface(self.__surface_size.size).convert_alpha()
                else:
                    raise util.GameException("Color argument {} is invalid should have lenght 3 or 4 not {}"
                                             .format(color, len(color)))
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
    ACTIVE_COLOR_DEFINITIONS: ClassVar[Union[ColorDefinition, None]] = None

    _surface: List[pygame.Surface]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def COLOR_DEFINITIONS(self) -> ColorDefinition:
        pass

    def _configure_surface(self) -> List[pygame.Surface]:
        """the self._surface attribute is set to this value. For colors this is a list of possible colors"""
        return self.COLOR_DEFINITIONS.images()

    def _configure_active_surface(self) -> List[pygame.Surface]:
        return self.ACTIVE_COLOR_DEFINITIONS.images() if self.ACTIVE_COLOR_DEFINITIONS else None

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
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition(con.INVISIBLE_COLOR, more_colors=False,
                                                                   border=False)


class BorderMaterial(ColorMaterial):
    """Blocks at the border of the board"""
    ALLOWED_TASKS: ClassVar[Set] = set()
    COLOR_DEFINITIONS: ClassVar[ColorDefinition] = ColorDefinition((0, 0, 0), more_colors=False, border=False)


class ImageMaterial(BaseMaterial, ABC):
    """Materials displaying an image"""
    __slots__ = "_active_surface", "_active"
    IMAGE_DEFINITIONS: ClassVar[ImageDefinition]
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Union[ImageDefinition, None]] = None

    _surface: List[pygame.Surface]
    _active_surface: List[pygame.Surface]
    _active: bool

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def IMAGE_DEFINITIONS(self) -> ImageDefinition:
        pass

    def _configure_surface(self) -> List[pygame.Surface]:
        """the self._surface attribute is set to this value. This is a list of possible images"""
        return self.IMAGE_DEFINITIONS.images()

    def _configure_active_surface(self) -> Union[List[pygame.Surface], None]:
        """the self._surface attribute is set to this value. This is a list of possible images"""
        return self.ACTIVE_IMAGE_DEFINITIONS.images() if self.ACTIVE_IMAGE_DEFINITIONS else None

    @property
    def surface(self) -> pygame.Surface:
        if not self._active:
            return choice(self._surface)
        return choice(self._active_surface)

    @property
    def full_surface(self) -> pygame.Surface:
        # make sure it is consistent
        return self._surface[0]


class MultiImageMaterial(ImageMaterial, ABC):
    """Class for materials that have multiple images associated with them that can be bound to keys in a dictionary"""
    __slots__ = "image_key"
    IMAGE_DEFINITIONS: ClassVar[Dict[Any, ImageDefinition]]
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Union[Dict[Any, ImageDefinition], None]] = None

    image_key: int
    _surface: Dict[Any, List[pygame.Surface]]
    _active_surface: Dict[Any, List[pygame.Surface]]

    def __init__(self, image_key: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.image_key = image_key if image_key else list(self.IMAGE_DEFINITIONS.keys())[0]

    def _configure_surface(self) -> Dict[Any, List[pygame.Surface]]:
        return self.__get_definition_surfaces(self.IMAGE_DEFINITIONS)

    def _configure_active_surface(self) -> Union[Dict[Any, List[pygame.Surface]], None]:
        return self.__get_definition_surfaces(self.ACTIVE_IMAGE_DEFINITIONS)

    def __get_definition_surfaces(
        self,
        definitions: Dict[Any, ImageDefinition]
    ) -> Union[Dict[Any, List[pygame.Surface]], None]:
        if definitions is None:
            return None
        surfaces = dict()
        for name, image_defenition in definitions.items():
            surfaces[name] = image_defenition.images()
        return surfaces

    @property
    def surface(self):
        if not self._active:
            return choice(self._surface[self.image_key])
        return choice(self._active_surface[self.image_key])

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


class MaterialCollection(DepthMaterial, ABC):
    """class that holds a collection of items that are randomly returned based on wheights this is mainly meant for
     board generation purposes"""
    MATERIAL_PROBABILITIES: ClassVar[Dict[str, float]]

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL_PROBABILITIES(self) -> Dict[DepthMaterial, float]:
        """Dictionary linking material type to to a probability of returning that name when the name() metod is
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


class InventoryMaterial:
    ALLOWED_TASKS: ClassVar[Set] = BaseMaterial.ALLOWED_TASKS.union({"Empty inventory"})


class Indestructable:
    ALLOWED_TASKS: ClassVar[Set] = {task for task in BaseMaterial.ALLOWED_TASKS if task not in ["Building", "Mining"]}


class TransportableMaterial(ABC):

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def TRANSPORT_IMAGE_DEFINITION(self) -> Union[ImageDefinition, ColorDefinition]:
        pass

    @property
    def transport_surface(self) -> pygame.Surface:
        return self.TRANSPORT_IMAGE_DEFINITION.images()[0]
