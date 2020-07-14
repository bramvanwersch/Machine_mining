

class Inventory:
    def __init__(self, max_wheight):
        self.container = {}
        self.wheight = [0, max_wheight]

    def get(self, item_name, amnt):
        """
        Get an item and amount form the inventory

        :param item: the name of the item
        :param amnt: the amount of the item
        :return: None if no item available or the available amount up till the
        requested amount of the item in an Item Object
        """
        if item_name in self.container:
            item = self.container[item_name].quantity
            available_amnt = min(item.quantity, amnt)
            item -= available_amnt
            self.wheight[0] -= item.WHEIGHT * available_amnt
            if item.quantity <= 0:
                del self.container[item_name]
            return Item(item.material, available_amnt)
        else:
            return None

    def add(self, *blocks):
        for block in blocks:
            if not block in self.container:
                self.container[block.material.NAME] = Item(block.material)
            else:
                self.container[block.material.NAME] += 1
            self.wheight[0] += self.container[block.material.NAME].WHEIGHT

    @property
    def full(self):
        return self.wheight[0] > self.wheight[1]

class Item:
    """
    Tracks a single item using the __material of the item and a quantity
    """
    def __init__(self, material, quantity = 1):
        self.material = material
        self.quantity = quantity

    def __iadd__(self, other):
        self.quantity += other
        return self

    def __isub__(self, other):
        self.quantity -= other
        return self

    def __getattr__(self, item):
        """
        Give al attributes of the __material to the item
        :param item: the attribute of interest
        :return:
        """
        return getattr(self.material, item)