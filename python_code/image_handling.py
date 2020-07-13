import pygame, os

from python_code.constants import IMAGE_DIR
from python_code.utilities import Size

#variable for all image sheets
image_sheets = {}

def load_images():
    """
    Loads all the available image_sheets into memory and saves them by a descriptive name in a dictionary
    """
    global image_sheets
    image_sheets["buildings"] = Spritesheet("building_materials.bmp", Size(10,10))


def load_image(name, colorkey=None):
    fullname = os.path.join(IMAGE_DIR, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print("Cannot load image:", fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
        image = image.convert_alpha()
    return image

class Spritesheet:
    def __init__(self, filename, size):
        self.sheet = load_image(filename)
        self.image_size = size

    def image_at(self, coord, color_key = None):
        if size is not None:
            rect = pygame.Rect(*coord, *size)
        else:
            rect = pygame.Rect(*coord, *self.image_size)
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

    def images_at_rectangle(self, *rects, **kwargs):
        """
        specify rectangles from where images need to be extracted. The rectangles need to be multiples of the size
        dimensions
        :param rects: tuple of lenght 4 or pygame.Rect objects
        :return: a list of images in the rectanges in the order of the specified rectangles aswell as
        """
        images = []
        if "size" in kwargs:
            size = kwargs["size"]
        else:
            size = self.image_size
        for rect in rects:
            for y in range(int(rect[3] / size[1])):
                for x in range(int(rect[2] / size[0])):
                    images.append(self.image_at((rect[0] + x * size[0],rect[1] + y * size[1]), **kwargs))
        return images