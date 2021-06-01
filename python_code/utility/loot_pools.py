from typing import Dict, List, TYPE_CHECKING, Type, Any
import random

from utility.inventories import Item
from utility import loading_saving
if TYPE_CHECKING:
    from block_classes.materials.materials import BaseMaterial


class ItemLootPool(loading_saving.Savable, loading_saving.Loadable):
    __total_items: int
    __likelyhoods: Dict[Type["BaseMaterial"], float]

    def __init__(
        self,
        total_items: int,
        item_likelyhoods: Dict[Type["BaseMaterial"], float]
    ):
        self.__total_rolls = total_items
        self.__likelyhoods = item_likelyhoods

    def __innit_load(
        self,
        total_rolls: int,
        likelyhoods: Dict[Type["BaseMaterial"], float]
    ):
        self.__total_rolls = total_rolls
        self.__likelyhoods = likelyhoods

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rolls": self.__total_rolls,
            "likelyhoods": {mat.__name__: value for mat, value in self.__likelyhoods.items()}
        }

    @classmethod
    def from_dict(cls, dct):
        from block_classes import block_utility
        total_rolls = dct["total_rolls"]
        likelyhoods = {block_utility.material_class_from_string(name): value
                       for name, value in dct["likelyhoods"].items()}
        cls.load(total_rolls=total_rolls, likelyhoods=likelyhoods)

    def roll_all_items(self) -> List[Item]:
        """Roll all items in the loot pool ands return as item objects"""
        item_materials = random.choices(list(self.__likelyhoods.keys()),
                                        list(self.__likelyhoods.values()), k=self.__total_rolls)
        items = {}
        for material in item_materials:
            if material in items:
                items[material].quantity += 1
            else:
                items[material] = Item(material(), 1)
        return list(items.values())
