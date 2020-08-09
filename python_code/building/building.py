from python_code.widgets import *

#globals
SELECTED_WIDGET = None

def select_an_item(widget):
    global SELECTED_WIDGET
    if SELECTED_WIDGET and widget != SELECTED_WIDGET:
        SELECTED_WIDGET.set_selected(False)
    SELECTED_WIDGET = widget
    #add an event that presses the building key to exit the interface
    newevent = pygame.event.Event(KEYDOWN, unicode="b",
                                  key=pygame.locals.K_b,
                                  mod=pygame.locals.KMOD_NONE)  # create the event
    pygame.event.post(newevent)
    
def get_selected_item():
    return SELECTED_WIDGET.item

class BuildingInterface(EventHandler):
    def __init__(self, board, *groups):
        EventHandler.__init__(self, [])
        self.board = board
        self.__window = BuildingWindow(self.board.inventorie_blocks[0].inventory, *groups)

    def show(self, value):
        """
        Toggle showing the crafting window or not. This also makes sure that no
        real updates are pushed while the window is invisible

        :param value: a boolean
        """
        self.__window.visible = value

    def handle_events(self, events):
        """
        Handle events issued by the user not consumed by the Main module. This
        function can also be used as an update method for all things that only
        need updates with new inputs.

        Note: this will trager quite often considering that moving the mouse is
        also considered an event.

        :param events: a list of events
        """
        leftovers = super().handle_events(events)
        if self.__window.visible:
            self.__window.handle_events(events)


class BuildingWindow(Frame):
    COLOR = (173, 94, 29, 150)
    def __init__(self, terminal_inventory, *groups):
        Frame.__init__(self, INTERFACE_WINDOW_POS, INTERFACE_WINDOW_SIZE,
                       *groups, layer=INTERFACE_LAYER, color=self.COLOR,
                       title = "PICK ITEM TO BUILD:")
        self.visible = False
        self.static = False
        self.__inventory = terminal_inventory
        self._inventory_sp = None
        self.__initiate_widgets()

        self.__prev_no_items = self.__inventory.number_of_items

    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.

        :See: Entity.update()
        """
        super().update(*args)
        if self.__prev_no_items < self.__inventory.number_of_items:
            self.__prev_no_items = self.__inventory.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.name() for widget in self._inventory_sp.widgets]
        for item in self.__inventory.items:
            if item.name() not in covered_items:
                #remove the alpha channel
                lbl = ItemLabel((0, 0), item, color=self.COLOR[:-1])
                def set_selected(self, selected):
                    self.set_selected(selected)
                    if selected:
                        select_an_item(self)

                lbl.set_action(1, set_selected, [lbl, True], ["pressed"])
                self._inventory_sp.add_widget(lbl)

    def __initiate_widgets(self):
        #create scrollable inventory
        self._inventory_sp  = ScrollPane((25, 50), (650, 625), color=self.COLOR[:-1])
        self.add_widget(self._inventory_sp)
        self.add_border(self._inventory_sp)
