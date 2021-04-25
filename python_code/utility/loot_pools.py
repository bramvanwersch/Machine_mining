from typing import Dict, List, TYPE_CHECKING, Type
import random

from utility.inventories import Item
if TYPE_CHECKING:
    from block_classes.materials import BaseMaterial


class ItemLootPool:
    __total_items: int
    __likelyhoods: Dict[Type["BaseMaterial"], float]

    def __init__(
        self,
        total_items: int,
        item_likelyhoods: Dict[Type["BaseMaterial"], float]
    ):
        self.__total_rolls = total_items
        self.__likelyhoods = item_likelyhoods

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
