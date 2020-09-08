from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window
from python_code.utility.utilities import Size


class FurnaceWindow(Window):
    SIZE = Size(100, 100)

    def __init__(self, furnace_object, *groups):
        self.furnace = furnace_object
        fr = self.furnace.rect
        location = fr.bottomleft
        Window.__init__(self,location , self.SIZE,
                       *groups, layer=INTERFACE_LAYER, title = "FURNACE",
                        allowed_events=[1, K_ESCAPE], static=True)

class TerminalWindow(Window):
    SIZE = Size(200, 100)
    COLOR = (173, 94, 29)

    def __init__(self, terminal_object, *groups):
        self.__terminal = terminal_object
        self.__terminal_inv = self.__terminal.blocks[0][0].inventory
        fr = self.__terminal.rect
        location = fr.bottomleft
        Window.__init__(self, location, self.SIZE,
                        *groups, layer=INTERFACE_LAYER, title="TERMINAL",
                        allowed_events=[1, K_ESCAPE], static=True)
        self.__add_widgets()
        self.__prev_no_items = self.__terminal_inv.number_of_items
    
    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.
        """
        super().update(*args)
        if self.__prev_no_items < self.__terminal_inv.number_of_items:
            self.__prev_no_items = self.__terminal_inv.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.name() for widget in self.__inventory_pane.widgets]
        for item in self.__terminal_inv.items:
            if item.name() not in covered_items:
                #remove the alpha channel
                lbl = ItemLabel((0, 0), item, color=(173, 94, 29))

                self.__inventory_pane.add_widget(lbl)

    def __add_widgets(self):
        self.__inventory_pane = ScrollPane((10, 10), self.SIZE - (20, 20), color=self.COLOR)
        self.add_widget(self.__inventory_pane)
        self.add_border(self.__inventory_pane)

