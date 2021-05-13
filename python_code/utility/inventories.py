from typing import Union, List, Set, Dict, TYPE_CHECKING, Iterable, Any
import random

from utility import utilities as util, loading_saving
if TYPE_CHECKING:
    import pygame
    from block_classes.materials.materials import BaseMaterial
    from block_classes.blocks import Block


class Filter(loading_saving.Savable, loading_saving.Loadable):
    """Inventory filter that can tell if an item is allowed or not"""
    __slots__ = "__whitelist", "__blacklist"

    __blacklist: Set
    __whitelist: Union[Set, None]

    def __init__(
        self,
        blacklist: Union[List[str], None] = None,
        whitelist: Union[List[str], None] = None
    ):
        self.__blacklist = set(blacklist if blacklist is not None else [])
        self.__whitelist = whitelist if whitelist is None else set(whitelist)

    def __init_load__(self, blacklist=None, whitelist=None):
        self.__init__(blacklist, whitelist)

    def to_dict(self):
        return {
            "blacklist": list(self.__blacklist) if self.__blacklist is not None else [],
            "whitelist": list(self.__whitelist) if self.__whitelist is not None else []
        }

    @classmethod
    def from_dict(cls, dct):
        blacklist = set(dct["blacklist"])
        whitelist = set(dct["whitelist"])
        return cls.load(blacklist=blacklist, whitelist=whitelist)

    def allowed(
        self,
        item_name: str
    ) -> bool:
        """Check if an item is allowed by this filter"""
        if self.__whitelist is not None and item_name not in self.__whitelist or \
                item_name in self.__blacklist:
            return False
        return True

    def set_blacklist(
        self,
        *item_names: List[str]
    ):
        self.__blacklist = set(item_names)

    def add_blacklist(
        self,
        *item_names: List[str]
    ):
        for item_name in item_names:
            self.__blacklist.add(item_name)

    def remove_from_blacklist(
        self,
        *item_names: List[str]
    ):
        for item_name in item_names:
            if item_name in self.__blacklist:
                self.__blacklist.remove(item_name)

    def set_whitelist(
        self,
        *item_names: List[str]
    ):
        self.__whitelist = set(item_names)

    def add_whitelist(
        self,
        *item_names: List[str]
    ):
        for item_name in item_names:
            self.__whitelist.add(item_name)

    def remove_from_whitelist(
        self,
        *item_names: List[str]
    ):
        for item_name in item_names:
            if item_name in self.__whitelist:
                self.__whitelist.remove(item_name)

    def __str__(self) -> str:
        info_str = "Filter:\n"
        info_str += f"Whitelist: {[name for name in self.__whitelist] if self.__whitelist is not None else []}\n"
        info_str += f"Blacklist: {[name for name in self.__blacklist]}"
        return info_str


class Inventory(loading_saving.Savable, loading_saving.Loadable, util.ConsoleReadable):
    """Inventory for managing items within"""
    __slots__ = "_container", "in_filter", "out_filter", "wheight"
    _container: Dict[str, "Item"]
    wheight: List[int]
    in_filter: Union[Filter]
    out_filter: Union[Filter]

    def __init__(
        self,
        max_wheight: int,
        in_filter: Union[Filter, None] = None,
        out_filter: Union[Filter, None] = None,
        items: List["Item"] = None
    ):
        self._container = {item.name(): item for item in items} if items else {}
        self.wheight = [0, max_wheight]

        self.in_filter = in_filter if in_filter is not None else Filter()
        self.out_filter = out_filter if out_filter is not None else Filter()

    def __init_load__(self, items=None, wheight=None, in_filter=None, out_filter=None):
        self._container = {item.name(): item for item in items}
        self.wheight = wheight

        self.in_filter = in_filter
        self.out_filter = out_filter

    def to_dict(self):
        return {
            "items": [item.to_dict() for item in self._container.values()],
            "wheight": self.wheight,
            "in_filter": self.in_filter.to_dict(),
            "out_filter": self.out_filter.to_dict()
        }

    @classmethod
    def from_dict(cls, dct):
        items = [Item.from_dict(d) for d in dct["items"]]
        in_filter = Filter.from_dict(dct["in_filter"])
        out_filter = Filter.from_dict(dct["out_filter"])
        return cls.load(items=items, wheight=dct["wheight"], in_filter=in_filter, out_filter=out_filter)

    def get(
        self,
        item_name: str,
        amnt: int,
        ignore_filter: bool = False
    ) -> Union["Item", None]:
        """Get an item from the inventory and remove it. Return the available amount if the full amount is not present
        or None if the item is not present at all or amount is 0. Copies of the original are returned meaning that
        modifying them will not affect the inventory item directly"""
        if not ignore_filter and not self.check_item_get(item_name):
            return
        else:
            item = self._container[item_name]
            available_amnt = self.__remove_quantity(item, amnt)
            if available_amnt > 0:
                return Item(item.material, available_amnt)
        return None

    def get_random_item(
        self,
        amnt: int
    ) -> Union["Item", None]:
        """Get the first item from the inventory that is allowed."""
        allowed_items = [item.name() for item in self._container.values() if self.check_item_get(item.name(), 1)]
        if len(allowed_items) == 0:
            return None
        chosen_item_name = random.choice(allowed_items)
        return self.get(chosen_item_name, amnt)

    def get_all_items(
        self,
        ignore_filter: bool = False
    ) -> List["Item"]:
        """Get al items from the inventory meaning all items are removed with this action"""
        items = []
        for key in list(self._container.keys()):
            item = self.get(key, self._container[key].quantity, ignore_filter=ignore_filter)
            if item:
                items.append(item)
        return items

    def check_item_get(
        self,
        item_name: str,
        quantity: int = 1
    ) -> bool:
        """Check if it is allowed to get a certain items based on filters and a provided amount"""
        if not self.out_filter.allowed(item_name) or item_name not in self._container or\
                self._container[item_name].quantity < quantity:
            return False
        return True

    def check_item_deposit(
        self,
        item_name: str
    ) -> bool:
        """Check if an item is alloed to be deposited based on filters"""
        if not self.in_filter.allowed(item_name):
            return False
        return True

    def __remove_quantity(
        self,
        item: "Item",
        amnt: int
    ) -> int:
        """Remove a quantity from an item. Return the extracted amount, can be less then the requested amount"""
        available_amnt = min(item.quantity, amnt)
        item.quantity -= available_amnt
        self.wheight[0] -= item.WHEIGHT * available_amnt
        return available_amnt

    def add_blocks(
        self,
        *blocks: "Block",
        ignore_filter: bool = False
    ):
        """Add a number of blocks to this inventory by creating item classes"""
        for block in blocks:
            item = Item(block.material)
            self.__add_item(item, ignore_filter=ignore_filter)

    def add_materials(
        self,
        *materials: "BaseMaterial",
        ignore_filter: bool = False
    ):
        """Add a number of materials to this inventory by creating item classes"""
        for material in materials:
            item = Item(material)
            self.__add_item(item, ignore_filter=ignore_filter)

    def add_items(
        self,
        *items: "Item",
        ignore_filter: bool = False
    ):
        """Add a number of items to this inventory"""
        for item in items:
            self.__add_item(item, ignore_filter=ignore_filter)

    def __add_item(
        self,
        item: "Item",
        ignore_filter: bool = False
    ):
        """Add an item to the inventory by creating a new entry if not already present or adding to the amount
        otherwise"""
        if not ignore_filter and not self.check_item_deposit(item.name()):
            return
        if not item.name() in self._container:
            self._container[item.name()] = item
        else:
            self._container[item.name()].quantity += item.quantity
        self.wheight[0] += self._container[item.name()].WHEIGHT * item.quantity

    def __contains__(
        self,
        name: str
    ) -> bool:
        return name in self._container

    @property
    def full(self) -> bool:
        return self.wheight[0] > self.wheight[1]

    @property
    def empty(self) -> bool:
        return self.wheight[0] == 0

    @property
    def item_names(self) -> Iterable[str]:
        return self._container.keys()

    @property
    def number_of_items(self) -> int:
        return len(self._container)

    @property
    def items(self) -> Iterable["Item"]:
        return self._container.values()

    def item_pointer(
        self,
        name: str
    ) -> Union[None, "Item"]:
        """Return a pointer to an item in the invetory."""
        if name in self._container:
            return self._container[name]
        return None

    def __str__(self) -> str:
        final_str = "Inventory:\n"
        for item in self._container.values():
            final_str += f"{str(item)}\n"
        return final_str[:-1]


class Item(loading_saving.Savable, loading_saving.Loadable):
    """Tracks a single item using the __material of the item and a quantity"""
    __slots__ = "material", "quantity"
    material: "BaseMaterial"
    quantity: int

    def __init__(
        self,
        material: "BaseMaterial",
        quantity: int = 1
    ):
        self.material = material
        self.quantity = quantity

    def __init_load__(self, material=None, quantity=None):
        self.__init__(material, quantity)

    def to_dict(self):
        return {
            "material": self.material.to_dict(),
            "quantity": self.quantity
        }

    @classmethod
    def from_dict(cls, dct):
        from block_classes.materials.materials import BaseMaterial
        material = BaseMaterial.from_dict(dct["material"])
        return cls.load(material=material, quantity=dct["quantity"])

    def __getattr__(
        self,
        item: str
    ) -> Any:
        """Give al attributes of the __material to the item"""
        return getattr(self.material, item)

    def copy(self) -> "Item":
        return Item(self.material, self.quantity)

    def __str__(self) -> str:
        return f"{self.material.name()}: {self.quantity}"


class TransportItem(Item):
    """Class to allow for tracking a rectangle with the item for transport"""
    __slots__ = "rect"

    def __init__(
        self,
        rect: "pygame.Rect",
        material: "BaseMaterial",
        quantity: int = 1
    ):
        super().__init__(material, quantity)
        self.rect = rect

    def __init_load__(self, material=None, quantity=None, rect=None):
        self.__init__(rect, material, quantity)

    def to_dict(self):
        d = super().to_dict()
        d["rect"] = (self.rect.left, self.rect.top, self.rect.width, self.rect.height)
        return d

    @classmethod
    def from_dict(cls, dct):
        from block_classes.materials.materials import BaseMaterial
        rect = pygame.Rect(dct["rect"])
        material = BaseMaterial.from_dict(dct["material"])
        return cls.load(rect=rect, material=material, quantity=dct["quantity"])

    def __str__(self) -> str:
        return f"{super().__str__()}({self.rect})"
