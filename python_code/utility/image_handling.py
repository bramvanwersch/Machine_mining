from typing import Tuple, List, Union

import pygame
import os

# variable for all image sheets
from utility import utilities as util, constants as con

image_sheets = {}


def load_images():
    """
    Loads all the available image_sheets into memory and saves them by a descriptive name in a dictionary
    """
    global image_sheets
    image_sheets["buildings"] = Spritesheet("building_materials.bmp", util.Size(10, 10))
    image_sheets["general"] = Spritesheet("general.bmp", util.Size(10, 10))
    image_sheets["materials"] = Spritesheet("materials.bmp", util.Size(10, 10))


def _load_spritesheet(name, colorkey=None):
    fullname = os.path.join(con.IMAGE_DIR, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print("Cannot load image:", fullname)
        raise SystemExit(str(pygame.geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, con.RLEACCEL)
        image = image.convert_alpha()
    return image


def load_image(sprite_sheet_name, coord, size=None, color_key=con.INVISIBLE_COLOR):
    try:
        return image_sheets[sprite_sheet_name].image_at(coord, size, color_key)
    except KeyError:
        raise util.GameException(f"No sprite sheet with name {sprite_sheet_name}.")


class Spritesheet:
    def __init__(self, filename, size):
        self.sheet = _load_spritesheet(filename)
        self.image_size = size

    def image_at(self, coord, size=None, color_key=con.INVISIBLE_COLOR):
        if size is None:
            size = self.image_size
        rect = pygame.Rect(*coord, *size)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if color_key is not None:
            if color_key == -1:
                color_key = image.get_at((0, 0))
            image.set_colorkey(color_key, pygame.RLEACCEL)
            image = image.convert_alpha()
        return image

    def images_at(self, *coords, **kwargs):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(coord, **kwargs) for coord in coords]

    def images_at_rectangle(self, rect, **kwargs):
        """
        specify rectangles from where images need to be extracted. The rectangles need to be multiples of the size
        dimensions

        :param rects: tuple of lenght 4 or pygame.Rect objects
        :return: a list of images in the rectanges in the order of the specified rectangles aswell as
        """
        images = []
        for y in range(int(rect[3] / self.image_size[1])):
            image_row = []
            for x in range(int(rect[2] / self.image_size[0])):
                image_row.append(self.image_at((rect[0] + x * self.image_size[0],rect[1] + y * self.image_size[1]),
                                               **kwargs))
            images.append(image_row)
        return images


class ImageDefinition:
    """Define an image and make sure that image creation is not done repeatedly"""
    __slots__ = "__sheet_name", "__image_location", "__color_key", "__flip", "__size", "__image_size", "__images",\
                "__rotate"

    __sheet_name: str
    __image_location: Tuple[int, int]
    __color_key: Tuple[int, int, int]
    __flip: Tuple[bool, bool]
    # this varaible will save when get_images is called once before te prevent unnecesairy transform an image_at calls
    __images: List[pygame.Surface]
    __size: util.Size
    __rotate: int
    __image_size: util.Size

    def __init__(
        self,
        sheet_name: str,
        image_location: Tuple[int, int],
        color_key: Tuple[int, int, int] = con.INVISIBLE_COLOR,
        flip: Tuple[bool, bool] = (False, False),
        image_size: util.Size = con.BLOCK_SIZE,
        size: util.Size = util.Size(10, 10),
        rotate: int = 0
    ):
        self.__sheet_name = sheet_name
        self.__image_location = image_location
        self.__color_key = color_key
        self.__flip = flip
        self.__size = size
        self.__rotate = rotate
        self.__image_size = image_size
        self.__images = []

    def images(self) -> List[pygame.Surface]:
        """Get/create all images defined by the image definition"""
        if len(self.__images) > 0:
            return self.__images
        return self.__create_images()

    def set_size(self, size: Union[pygame.Rect, Tuple[int, int, int, int], List[int]]):
        """Allow to set the scale after the fact"""
        self.__size = util.Size(*size)
        self.__create_images()

    def __create_images(self) -> List[pygame.Surface]:
        """Get defined images from image sheets and potentially scale and transform when neccesairy"""
        global image_sheets
        norm_image = image_sheets[self.__sheet_name].image_at(
            self.__image_location, color_key=self.__color_key, size=self.__size)
        norm_size = norm_image.get_size()
        if norm_size[0] != self.__image_size[0] or norm_size[1] != self.__image_size[1]:
            norm_image = pygame.transform.scale(norm_image, self.__image_size.size)
        if self.__rotate != 0:
            norm_image = pygame.transform.rotate(norm_image, self.__rotate)
        self.__images = [norm_image]
        if self.__flip[0]:
            horizontal_flip_image = pygame.transform.flip(norm_image, True, False)
            self.__images.append(horizontal_flip_image)
        if self.__flip[1]:
            vertical_flip_image = pygame.transform.flip(norm_image, False, True)
            self.__images.append(vertical_flip_image)
        return self.__images


class Animation:
    def __init__(self, images, frame_time):
        self.active = False
        self.__images = images
        self.__elapsed_time = 0
        self.__frame_time = frame_time
        self.__total_time = len(self.__images) * self.__frame_time
        self.new_frame_started = False

    def start(self):
        self.__elapsed_time = 0
        self.active = True
        self.new_frame_started = False

    def stop(self):
        self.active = False
        self.new_frame_started = False

    def current_image(self):
        if not self.active:
            return self.__images[-1]
        frame = self.__get_frame()
        return self.__images[frame]

    def update(self):
        self.new_frame_started = False
        current_frame = self.__get_frame()
        self.__elapsed_time += con.GAME_TIME.get_time()
        new_frame = self.__get_frame()
        self.new_frame_started = current_frame != new_frame
        if self.__elapsed_time >= self.__total_time:
            self.active = False

    def __get_frame(self):
        return int(self.__elapsed_time / self.__frame_time)
