

class Filter:
    def __init__(self, blacklist=[], whitelist=[]):
        self.__blacklist = set(blacklist)
        self.__whitelist = set(whitelist)

    def allowed(self, item_name):
        if len(self.__whitelist) > 0 and item_name not in self.__whitelist or \
                item_name in self.__blacklist:
            return False
        return True

    def set_blacklist(self, *item_names):
        self.__blacklist = set(item_names)

    def set_whitelist(self, *item_names):
        self.__whitelist = set(item_names)


class Inventory:
    def __init__(self, max_wheight, in_filter=None, out_filter=None):
        self.__container = {}
        self.wheight = [0, max_wheight]

        if in_filter != None:
            self.in_filter = in_filter
        else:
            self.in_filter = Filter()
        if out_filter != None:
            self.out_filter = out_filter
        else:
            self.out_filter = Filter()

    def get(self, item_name, amnt, ignore_filter=False):
        """
        Get an item and amount form the inventory

        :param item: the name of the item
        :param amnt: the amount of the item
        :return: None if no item available or the available amount up till the
        requested amount of the item in a new Item Object
        """
        if not ignore_filter and not self.check_item_get(item_name):
            return
        else:
            item = self.__container[item_name]
            available_amnt = self.__remove_quantity(item, amnt)
            if available_amnt > 0:
                return Item(item.material, available_amnt)
        return None

    def get_all_items(self, ignore_filter=False):
        """
        Get a list of all items and there total amounts in new Item objects.
        The amounts are removed from the original inventory.
        :return:
        """
        items = []
        for key in list(self.__container.keys()):
            item = self.get(key, self.__container[key].quantity, ignore_filter=ignore_filter)
            if item:
                items.append(item)
        return items

    def check_item_get(self, item_name, quantity=1):
        if not self.out_filter.allowed(item_name) or item_name not in self.__container or\
                self.__container[item_name].quantity < quantity:
            return False
        return True

    def check_item_deposit(self, item_name):
        if not self.in_filter.allowed(item_name):
            return False
        return True

    def __remove_quantity(self, item, amnt):
        available_amnt = min(item.quantity, amnt)
        item.quantity -= available_amnt
        self.wheight[0] -= item.WHEIGHT * available_amnt
        return available_amnt

    def add_blocks(self, *blocks, ignore_filter = False):
        for block in blocks:
            item = Item(block.material)
            self.__add_item(item, ignore_filter=ignore_filter)

    def add_materials(self, *materials, ignore_filter=False):
        for material in materials:
            item = Item(material)
            self.__add_item(item, ignore_filter=ignore_filter)

    def add_items(self, *items, ignore_filter = False):
        for item in items:
            self.__add_item(item, ignore_filter=ignore_filter)

    def __add_item(self, item, ignore_filter=False):
        if not ignore_filter and not self.check_item_deposit(item.name()):
            return
        if not item.name() in self.__container:
            self.__container[item.name()] = item
        else:
            self.__container[item.name()].quantity += item.quantity
        self.wheight[0] += self.__container[item.name()].WHEIGHT * item.quantity

    def __contains__(self, name):
        return name in self.__container

    @property
    def full(self):
        return self.wheight[0] > self.wheight[1]

    @property
    def empty(self):
        return self.wheight[0] == 0

    @property
    def item_names(self):
        return self.__container.keys()

    @property
    def number_of_items(self):
        """
        :return: lenght of the keys of the __container
        """
        return len(self.__container)

    @property
    def items(self):
        return self.__container.values()

    def item_pointer(self, name):
        if name in self.__container:
            return self.__container[name]
        return None

    def __str__(self):
        final_str = ""
        for item in self.__container.values():
            final_str += "{}: {}\n".format(item.name(), item.quantity)
        return final_str[:-1]

class Item:
    """
    Tracks a single item using the __material of the item and a quantity
    """
    def __init__(self, material, quantity = 1):
        self.material = material
        self.quantity = quantity

    def __getattr__(self, item):
        """
        Give al attributes of the __material to the item
        :param item: the attribute of interest
        :return:
        """
        return getattr(self.material, item)

    def copy(self):
        return Item(self.material, self.quantity)

    def __str__(self):
        return "{}: {}".format(self.material.name(), self.quantity)