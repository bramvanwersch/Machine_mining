from typing import Dict, Any

from utility import constants as con, loading_saving
import block_classes.blocks as block_classes
import block_classes.materials.environment_materials as environment_materials


class Flora:
    def __init__(self):
        self.__plants = dict()

    def add(self, plant: "Plant"):
        self.__plants[plant.id] = plant

    def get(self, plant_id: str):
        return self.__plants[plant_id]

    def remove(self, plant_id: str):
        self.__plants.pop(plant_id)

    def __contains__(self, item: block_classes.Block):
        return item.id in self.__plants

    def __iter__(self):
        return iter(self.__plants.values())


class Plant(loading_saving.Savable):

    DIRECTION_ADDITON = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    ID = 0

    def __init__(self, start_block, residing_chunk):
        self.id = "Plant{}".format(self.ID)
        Plant.ID += 1
        self.material = start_block.material
        self.__blocks = [start_block]
        self.grow_block.id = self.id
        self.__residing_chunk = residing_chunk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocks": [block.to_dict() for block in self.__blocks],
            "id": self.id,
        }

    def is_loaded(self):
        return self.__residing_chunk.is_loaded()

    def grow(self, surrounding_blocks):
        direction = self.material.CONTINUATION_DIRECTION
        if surrounding_blocks[direction] is None or surrounding_blocks[direction].name() != "Air":
            return None
        material_obj = getattr(environment_materials, self.grow_block.name())
        extension_block = block_classes.Block(self.grow_block.coord, material_obj(image_key=direction), id_=self.id)

        # move the tip of the plant forward
        self.grow_block.rect.topleft = (self.grow_block.rect.left + con.BLOCK_SIZE.width * self.DIRECTION_ADDITON[direction][0],
                                        self.grow_block.rect.top + con.BLOCK_SIZE.height * self.DIRECTION_ADDITON[direction][1])
        self.__blocks.insert(len(self.__blocks) - 1, extension_block)
        return extension_block, self.grow_block

    def can_grow(self):
        return self.material.GROW_CHANCE > 0 and self.size() < self.material.MAX_SIZE

    def remove_block(self, block):
        index = 0
        for index, p_block in enumerate(self.__blocks):
            if p_block.coord == block.coord:
                break
        remove_blocks = self.__blocks[index:]
        self.__blocks = self.__blocks[:index]
        if self.size() > 0:
            self.__blocks[-1].material.image_key = -1
        return remove_blocks

    @property
    def grow_block(self):
        return self.__blocks[-1]

    @property
    def base_block(self):
        # the block that connects the plant to the ground
        return self.__blocks[0]

    def size(self):
        return len(self.__blocks)
