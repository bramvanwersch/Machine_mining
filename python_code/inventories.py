

class Inventory:
    def __init__(self, max_wheight):
        self.__container = {}
        self.wheight = [0, max_wheight]

    def get(self, item_name, amnt):
        """
        Get an item and amount form the inventory

        :param item: the name of the item
        :param amnt: the amount of the item
        :return: None if no item available or the available amount up till the
        requested amount of the item in a new Item Object
        """
        if item_name in self.__container:
            item = self.__container[item_name]
            available_amnt = self.__remove_quantity(item, amnt)

            return Item(item.material, available_amnt)
        else:
            return None

    def get_all_items(self):
        """
        Get a list of all items and there total amounts in new Item objects.
        The amounts are removed from the original inventory.
        :return:
        """
        items = []
        for key in list(self.__container.keys()):
            items.append(self.get(key, self.__container[key].quantity))
        return items

    def check_item(self, item_name, quantity):
        if item_name in self.__container and self.__container[item_name].quantity >= quantity:
            return True
        return False

    def __remove_quantity(self, item, amnt):
        available_amnt = min(item.quantity, amnt)
        item.quantity -= available_amnt
        self.wheight[0] -= item.WHEIGHT * available_amnt
        return available_amnt

    def add_blocks(self, *blocks):
        for block in blocks:
            if not block.material.name() in self.__container:
                self.__container[block.name()] = Item(block.material)
            else:
                self.__container[block.name()].quantity += 1
            self.wheight[0] += self.__container[block.name()].WHEIGHT

    def add_items(self, *items):
        for item in items:
            if not item.name() in self.__container:
                self.__container[item.name()] = item
            else:
                self.__container[item.name()].quantity += item.quantity
            self.wheight[0] += self.__container[item.name()].WHEIGHT * item.quantity

    @property
    def full(self):
        return self.wheight[0] > self.wheight[1]

    @property
    def empty(self):
        return len(self.__container) == 0

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