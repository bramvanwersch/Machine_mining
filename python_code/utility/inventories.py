from typing import Union, List, Set, Dict, TYPE_CHECKING, Iterable, Any
if TYPE_CHECKING:
    from block_classes.blocks import Block
    from block_classes.materials import BaseMaterial


class Filter:
    """Inventory filter that can tell if an item is allowed or not"""
    __slots__ = "__whitelist", "__blacklist"
    __blacklist: Set
    __whitelist: Set

    def __init__(
        self,
        blacklist: Union[List[str], None] = None,
        whitelist: Union[List[str], None] = None
    ):
        self.__blacklist = set(blacklist if blacklist is not None else [])
        self.__whitelist = set(whitelist if whitelist is not None else [])

    def allowed(
        self,
        item_name: str
    ) -> bool:
        """Check if an item is allowed by this filter"""
        if len(self.__whitelist) > 0 and item_name not in self.__whitelist or \
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


class Inventory:
    """Inventory for managing items within"""
    __slots__ = "__container", "in_filter", "out_filter", "wheight"
    __container: Dict[str, "Item"]
    wheight: List[int]
    in_filter: Union[Filter]
    out_filter: Union[Filter]

    def __init__(
        self,
        max_wheight,
        in_filter: Union[Filter, None] = None,
        out_filter: Union[Filter, None] = None
    ):
        self.__container = {}
        self.wheight = [0, max_wheight]

        self.in_filter = in_filter if in_filter is not None else Filter()
        self.out_filter = out_filter if out_filter is not None else Filter()

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
            item = self.__container[item_name]
            available_amnt = self.__remove_quantity(item, amnt)
            if available_amnt > 0:
                return Item(item.material, available_amnt)
        return None

    def get_first(
        self,
        amnt: int
    ) -> Union["Item", None]:
        """Get the first item from the inventory that is allowed."""
        for item in self.__container.values():
            if self.check_item_get(item.name, 1):
                return self.get(item.name, amnt)
        return None

    def get_all_items(
        self,
        ignore_filter: bool = False
    ) -> List["Item"]:
        """Get al items from the inventory meaning all items are removed with this action"""
        items = []
        for key in list(self.__container.keys()):
            item = self.get(key, self.__container[key].quantity, ignore_filter=ignore_filter)
            if item:
                items.append(item)
        return items

    def check_item_get(
        self,
        item_name: str,
        quantity: int = 1
    ) -> bool:
        """Check if it is allowed to get a certain items based on filters and a provided amount"""
        if not self.out_filter.allowed(item_name) or item_name not in self.__container or\
                self.__container[item_name].quantity < quantity:
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
        if not item.name() in self.__container:
            self.__container[item.name()] = item
        else:
            self.__container[item.name()].quantity += item.quantity
        self.wheight[0] += self.__container[item.name()].WHEIGHT * item.quantity

    def __contains__(
        self,
        name: str
    ) -> bool:
        return name in self.__container

    @property
    def full(self) -> bool:
        return self.wheight[0] > self.wheight[1]

    @property
    def empty(self) -> bool:
        return self.wheight[0] == 0

    @property
    def item_names(self) -> Iterable[str]:
        return self.__container.keys()

    @property
    def number_of_items(self) -> int:
        return len(self.__container)

    @property
    def items(self) -> Iterable["Item"]:
        return self.__container.values()

    def item_pointer(
        self,
        name: str
    ) -> Union[None, "Item"]:
        """Return a pointer to an item in the invetory."""
        if name in self.__container:
            return self.__container[name]
        return None

    def __str__(self) -> str:
        final_str = "Inventory:"
        for item in self.__container.values():
            final_str += f"{str(item)}\n"
        return final_str[:-1]


class Item:
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

    def __getattr__(
        self,
        item: str
    ) -> Any:
        """Give al attributes of the __material to the item"""
        return getattr(self.material, item)

    def copy(self) -> "Item":
        return Item(self.material, self.quantity)

    def __str__(self) -> str:
        return "{}: {}".format(self.material.name(), self.quantity)
