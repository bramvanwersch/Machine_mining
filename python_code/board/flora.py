from typing import Dict, Any

from utility import constants as con, loading_saving
import block_classes.blocks as block_classes
import block_classes.materials.environment_materials as environment_materials


class Flora(loading_saving.Savable, loading_saving.Loadable):
    def __init__(self):
        self.__plants = dict()

    def __init_load__(self, plants=None):
        self.__plants = plants

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plants": {plant_id: plant.to_dict() for plant_id, plant in self.__plants.items()}
        }

    @classmethod
    def from_dict(cls, dct):
        plants = {plant_id: Plant.from_dict(d) for plant_id, d in dct["plants"].items()}
        return cls.load(plants=plants)

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


class Plant(loading_saving.Savable, loading_saving.Loadable):

    DIRECTION_ADDITON = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    ID = 0

    def __init__(self, start_block, residing_chunk):
        self.id = "Plant{}".format(self.ID)
        Plant.ID += 1
        self.material = start_block.material
        self.__blocks = [start_block]
        self.grow_block.id = self.id
        self.__chunk_id = residing_chunk

    def __init_load__(self, blocks=None, id_=None, chunk_id=None):
        self.id = id_
        Plant.ID += 1
        self.material = blocks[0].material
        self.__blocks = blocks
        self.__chunk_id = chunk_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocks": [block.to_dict() for block in self.__blocks],
            "id": self.id,
            "chunk_id": self.__chunk_id
        }

    @classmethod
    def from_dict(cls, dct, residing_chunk=None):
        posses = [d["pos"] for d in dct["blocks"]]
        mcds = [block_classes.Block.from_dict(d) for d in dct["blocks"]]
        blocks = [mcd.to_instance().to_block(pos=posses[index], **mcd.block_kwargs) for index, mcd in enumerate(mcds)]
        return cls.load(blocks=blocks, id_=dct["id"], chunk_id=dct["chunk_id"])

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
