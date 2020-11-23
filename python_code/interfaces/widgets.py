from abc import ABC, abstractmethod

from entities import ZoomableEntity
from utility.constants import *
from utility.event_handling import EventHandler
from interfaces.interface_utility import screen_to_board_coordinate
from block_classes.building_materials import BuildingMaterial
import board.buildings


class KeyActionFunctions:
    """
    Action function for defining actions for widgets. Can be called like a
    function
    """
    def __init__(self, function, values = [], types=["pressed", "unpressed"]):
        """
        :param function: a function object that can be triggered
        :param values: a value or pointer to supply to the function
        :param types: a list of types that should trigger the function
        """
        self.functions = {}
        self.add_action(function, values, types)

    def add_action(self, function, values=[], types=["pressed", "unpressed"]):
        for type in types:
            self.functions[type] = [function, values]

    def __call__(self, *args, **kwargs):
        """
        Allows the class to act like a function

        :param args: optional args
        :param kwargs: optional kwargs
        """
        if args[0] in self.functions:
            function, values = self.functions[args[0]]
            function(*values)


class HoverAction:
    def __init__(self, continious = False):
        self.__continious = continious
        self.__prev_hover_state = False
        self.__action_functions = {True : None, False : None}

    def set(self, hover):
        """
        Set and trigger an hover event when appropraite

        :param hover: a boolean that tells if the mouse is hovering or not
        """
        if hover != self.__prev_hover_state or self.__continious:
            if self.__action_functions[hover]:
                self.__action_functions[hover]("hover")
        self.__prev_hover_state = hover

    def set_hover_action(self, action, values=[]):
        self.__action_functions[True] = KeyActionFunctions(action, values, ["hover"])

    def set_unhover_action(self, action, values=[]):
        self.__action_functions[False] = KeyActionFunctions(action, values, ["hover"])


class SelectionGroup:
    def __init__(self, multiple=False):
        self.multi_mode = multiple
        self.__widgets = set()

    def add(self, widget):
        self.__widgets.add(widget)

    def select(self, widget, *args):
        if not self.multi_mode:
            for w in self.__widgets:
                w.set_selected(False)
        widget.set_selected(True, *args)

    def off(self):
        [w.set_selected(False) for w in self.__widgets]

    def on(self):
        if self.multi_mode:
            [w.set_selected(True) for w in self.__widgets]


class Widget(ABC):
    """
    Basic widget class
    """
    def __init__(self, size, selectable = False, **kwargs):
        self.action_functions = {}
        self.selectable = selectable
        self.selected = False

        #innitial position is 0, 0
        self.rect = pygame.Rect((0, 0, *size))
        self.visible = True

    def wupdate(self):
        """
        A funtion that allows updating a widget each frame
        """
        pass

    def action(self, key, type):
        """
        Activates an action function bound to a certain key.

        :param key: the key where the action function is bound to
        """
        self.action_functions[key](type)

    def set_action(self, key, action_function, values=[], types=["pressed", "unpressed"]):
        """
        Binds a certain key to an action function. Optional values can be
        supplied that are then added as args.

        :param key: the keyboard key that the function should be activated by
        :param action_function: the function that should trigger when the key
        is used and the mouse is over the widget
        :param values: a list of values
        :param: types: a list of event types that should trigger the action
        function
        """
        if key in self.action_functions:
            self.action_functions[key].add_action(action_function, values, types)
        else:
            self.action_functions[key] = KeyActionFunctions(action_function, values, types)

    def set_selected(self, selected):
        """
        Set a widget as selected. Allowing a highlight for instance

        :param selected: a boolean telling the state of selection
        """
        self.selected = selected


class Label(Widget):
    """
    Bsically a widget that allows image manipulation
    """
    SELECTED_COLOR = (255, 255, 255)
    def __init__(self, size, color = (255,255,255), **kwargs):
        Widget.__init__(self, size, **kwargs)
        self.image = self._create_image(size, color, **kwargs)
        self.orig_image = self.image.copy()
        self.color = color
        #parameter that tells the container widget containing this widget to
        #reblit it onto its surface.
        #always reblit at the start
        self.changed_image = True
        self.text_image = None

    def _create_image(self, size, color, image=None, border=None, border_color=(0,0,0),
                      text=None, font_size=15, text_color=(0,0,0), text_pos="center", **kwargs):
        """
        Create an image using a size and color

        :param size: a Size object or tuple of lenght 2
        :param color: a rgb color as tuple of lenght 2 or 3
        :param kwargs: additional named arguments
        :return: a pygame Surface object
        """
        if image:
            return image
        if len(color) == 3:
            image = pygame.Surface(size).convert()
        # included alpha channel
        elif len(color) == 4:
            image = pygame.Surface(size).convert_alpha()
        image.fill(color)
        if border:
            pygame.draw.rect(image, border_color, (0,0,*self.rect.size), 4)
        #add text when defined
        if text:
            text = FONTS[font_size].render(text, True, text_color)
            text_rect = text.get_rect()
            if text_pos == "center":
                text_pos = (self.rect.width / 2 - text_rect.width / 2, self.rect.height / 2 - text_rect.height / 2)
            image.blit(text, text_pos)
        return image

    def set_selected(self, selected, color=None):
        """
        Add a border around the outside of a widget when it is selected
        :See: Widget.set_selected()
        """
        super().set_selected(selected)
        if color == None:
            color = self.SELECTED_COLOR
        if self.selected:
            pygame.draw.rect(self.image, color, self.image.get_rect(), 3)
        else:
            self._clean_image(text = False)

        self.changed_image = True

    def set_image(self, image, pos = "center", size=None):
        """
        Change the full image of a widget or change it back to the orig_image
        by setting image to None

        :param image: a Surface Object or None
        :Note: resetting the image does not work if the original is transparant
        """
        if image == None:
            self.image = self.orig_image.copy()
        else:
            if size != None:
                image = pygame.transform.scale(image, size)
            rect = image.get_rect()
            if pos == "center":
                pos = (self.rect.width / 2 - rect.width / 2, self.rect.height / 2 - rect.height / 2)
            self.image.blit(image, pos)
        self.changed_image = True

    def set_text(self, text, pos, color = (0,0,0), font_size = 15, add = False):
        """
        Place some text on the widget

        :param text: A String to display
        :param pos: The position of the topleft corner
        :param color: the Color of the text default is black
        :param font_size: the size of the font. Can choose a range between 12 and 35
        :param add: if the text should be added to the current image or to the
        orig_image
        """
        if not add:
            self._clean_image()
        s = FONTS[font_size].render(str(text), True, color)
        rect = s.get_rect()
        if pos == "center":
            pos = (self.rect.width / 2 - rect.width / 2, self.rect.height / 2 - rect.height / 2)
        self.image.blit(s, pos)
        self.text_image = self.image.copy()
        if self.selected:
            self.set_selected(True)
        self.changed_image = True

    def _clean_image(self, text = True, selected = True):
        """
        Controlled cleaning of the image. You can specify to clean the text and
        or the border by setting text or selected to True

        :param text: a boolean that is True when the text should be cleaned
        False if not
        :param selected: a boolean that is True when selected border should be
        cleaned False if not
        """
        if self.text_image and not text:
            self.image = self.text_image.copy()
        else:
            self.image = self.orig_image.copy()
            self.text_image = None
        if self.selected and not selected:
            #draw selected
            pygame.draw.rect(self.image, self.SELECTED_COLOR, self.image.get_rect(), 3)


class Button(Label):
    COLOR_CHANGE = 75
    def __init__(self, size, **kwargs):
        super().__init__(size, **kwargs)
        self._hover_image = self._create_hover_image(**kwargs)
        self._hover = HoverAction()
        self._hover.set_hover_action(self.set_image, values=[self._hover_image])
        self._hover.set_unhover_action(self.set_image, values=[None])

    def _create_hover_image(self, hover_image=None, **kwargs):
        if hover_image:
            return hover_image
        kwargs["color"] = self.__hover_color()
        hover_image = self._create_image(self.image.get_size(), **kwargs)
        return hover_image

    def __hover_color(self):
        new_color = []
        for channel in self.color:
            if channel + self.COLOR_CHANGE > 255:
                new_color.append(channel - self.COLOR_CHANGE)
            else:
                new_color.append(channel + self.COLOR_CHANGE)
        return new_color


class Pane(Label, EventHandler):
    """
    Container widget that allows selecting and acts as an image for a number
    of widgets
    """
    def __init__(self, size, allowed_events = "ALL", **kwargs):
        Label.__init__(self, size, **kwargs)
        EventHandler.__init__(self, allowed_events)
        self.widgets = []

    def add_widget(self, pos, widget, add=False):
        """
        Add widgets at the provided rectangle of the widget
        :See: BaseConstraints.add_widget()
        """
        rect = widget.rect
        pos = list(pos)
        if pos[0] == "center":
            pos[0] = self.rect.width / 2 - rect.width / 2
        if pos[1] == "center":
            pos[1] = self.rect.height / 2 - rect.height / 2
        if add:
            pos = (rect.left + pos[0], rect.top + pos[1])
        widget.rect = pygame.Rect((*pos, *rect.size))
        self.widgets.append(widget)
        self.orig_image.blit(widget.image, pos)
        self.image = self.orig_image.copy()

    def wupdate(self, *args):
        """
        Update all the widgets in this container, and make sure to redraw them
        when needed

        :param args: optiinal argumetns
        """
        for widget in self.widgets:
            widget.wupdate()
            if widget.changed_image:
                self.__redraw_widget(widget)
                widget.changed_image = False

    def _find_selected_widgets(self, pos):
        """
        Recursively traverse all containers in containers to find the widget
        the user is hovering over. Then activate a potential action function

        :param pos: The position of the mouse relative to the container
        :return: a list of selected widgets with the bottommost one at the end
        of the list
        """
        selected_widgets = [self]
        adjusted_pos = (pos[0] - self.rect.left, pos[1] - self.rect.top)
        for widget in self.widgets:
            collide = widget.rect.collidepoint(adjusted_pos)
            #save if the widget is hovered over at this moment when implementing a hover action
            if hasattr(widget, "_hover"):
                widget._hover.set(collide)
            if collide:
                if isinstance(widget, Pane):
                    selected_widgets.append(widget)
                    lower_selected = widget._find_selected_widgets(adjusted_pos)
                    if lower_selected:
                        for w in lower_selected:
                            selected_widgets.append(w)
                else:
                    selected_widgets.append(widget)
        return selected_widgets

    def __redraw_widget(self, widget):
        """
        Method that redraws a widget in a container.

        :param widget:

        Sets the self.changed_image flag to True to forse potential containers
        that contain this container to redraw this container
        """
        self.orig_image.blit(widget.image, dest=widget.rect, area=(0,0,*widget.rect.size))
        self.image = self.orig_image.copy()
        self.changed_image = True

    def add_border(self, widget, color=(0,0,0)):
        """
        add a border around a specified widget. The widget should be in the frame
        :param widget:
        :return:
        """
        rect = widget.rect.inflate(4, 4)
        pygame.draw.rect(self.orig_image, color, rect, 3)
        self.image = self.orig_image.copy()


class Frame(ZoomableEntity, Pane):
    """
    Container for widgets, that is an entity so it can act as a window. Every
    gui should have a frame to be able to display and handle updates
    """
    def __init__(self, pos, size, *groups, **kwargs):
        Pane.__init__(self, size, **kwargs)
        ZoomableEntity.__init__(self, pos, size, *groups, **kwargs)

    def update(self, *args):
        """
        Entity update method that is used to update all widgets in the frame

        :See: Entity.update()
        """
        super().update(*args)
        self.wupdate(*args)

    def zoom(self, zoom):
        self._zoom = zoom

#need to be here otherwise rects are not properly chnaged
    @property
    def rect(self):
        """
        Returns a rectangle that represents the zoomed version of the
        self.orig_rect

        :return: a pygame Rect object
        """
        if self._zoom == 1 or not self.static:
            return self.orig_rect
        width, height = self.orig_rect.size
        orig_pos = list(self.orig_rect.center)
        orig_pos[0] = round(orig_pos[0] * self._zoom + 0.5 * (width - width * self._zoom))
        orig_pos[1] = round(orig_pos[1] * self._zoom + 0.5 * (height - height * self._zoom))
        rect = self.image.get_rect(center = orig_pos)
        return rect

    @rect.setter
    def rect(self, rect):
        self.orig_rect = rect

    def handle_events(self, events):
        """
        Handle events that are issued to the frame.

        :param events: a list of pygame Events

        activates events on the last element in the selected list (a list of
        all widgets that the user hovers over at this moment). It then tries
        to apply these events to all widgets in this list.
        """
        leftover_events = super().handle_events(events)
        pos = pygame.mouse.get_pos()

        if self.static:
            pos = screen_to_board_coordinate(pos, self.groups()[0].target, 1)
        selected = self._find_selected_widgets(pos)

        pressed = self.get_all_pressed()
        unpressed = self.get_all_unpressed()
        keys = [*zip(pressed, ["pressed"]* len(pressed)),
                *zip(unpressed, ["unpressed"]* len(unpressed))]
        #handle all events from the most front widget to the most back one.
        while selected != None and len(selected) > 0:
            widget = selected.pop()
            for index in range(len(keys) - 1, -1, -1):
                key, type = keys[index]
                if key.name in widget.action_functions:
                    widget.action(key.name, type)
                    #remove event as to not trigger it twice
                    del keys[index]
        return leftover_events


class ScrollPane(Pane):
    """
    A Pane that can be scrolled
    """
    SCROLL_SPEED = 20
    #space between the outside of the crafting window and the closest label
    BORDER_SPACE = 3
    def __init__(self, size, **kwargs):
        super().__init__(size, **kwargs)
        self.next_widget_topleft = [self.BORDER_SPACE, self.BORDER_SPACE]
        #the total rectangle
        self.total_rect = self.rect.copy()

        self.__total_offset_y = 0

        self.set_action(4, self.scroll_y, [self.SCROLL_SPEED])
        self.set_action(5, self.scroll_y, [-self.SCROLL_SPEED])

    def add_widget(self, pos, widget):
        """
        Overrides FreeConstriants method and adds widgets automatically so
        they will fit within the pane. Also makes sure that the offset of the
        scrolling is taken into account

        Note: pos does not serve a purpoise at the moment

        :See: FreeConstraints.add_widget()
        """
        #configure the position of the next
        if len(self.widgets) > 0:
            #when the widget does not fit on the frame put it on the next line
            if self.widgets[-1].rect.right + widget.rect.width > self.total_rect.width - self.BORDER_SPACE:
                #when the total rect is to small extend it.
                if self.widgets[-1].rect.bottom + widget.rect.height + self.BORDER_SPACE + self.total_rect.top > self.total_rect.bottom:
                    extra_room = (self.widgets[-1].rect.bottom + widget.rect.height + self.BORDER_SPACE + self.total_rect.top) - self.total_rect.bottom
                    self.__extend_scroll_image(extra_room)
                self.next_widget_topleft = [self.BORDER_SPACE, self.widgets[-1].rect.bottom]
            else:
                self.next_widget_topleft = self.widgets[-1].rect.topright
        self.widgets.append(widget)
        widget.rect.topleft = self.next_widget_topleft
        self.orig_image.blit(widget.image, widget.rect)

    def scroll_y(self, offset_y):
        """
        Scroll down the main image of the pane

        :param offset_y: an integer tnat is the amount the image should be
        scrolled in the y direction
        """
        #make sure to not scroll out of range
        if self.total_rect.bottom + self.__total_offset_y + offset_y < self.rect.bottom or\
            offset_y + self.__total_offset_y > 0:
            return

        #to make sure not to scroll when it is not needed
        width, height = self.orig_image.get_size()
        self.__total_offset_y += offset_y
        self.orig_image.fill(self.color)
        self.orig_image.scroll(0, offset_y)

        #make sure the location of the widgets contained is moved accordingly
        for widget in self.widgets:
            widget.rect.move_ip(0, offset_y)
            widget.changed_image = True

    def __extend_scroll_image(self, amnt):
        """
        Extend the current orig_image and total_rect to hold more image.

        :param amnt: the amount of pixels to extend the image by in the y
        direction

        """
        self.total_rect.height += amnt
        orig_copy = self.orig_image.copy()
        self.orig_image = pygame.Surface(self.total_rect.size).convert()
        self.orig_image.fill(self.color)
        self.orig_image.blit(orig_copy, (0,self.__total_offset_y))


class ItemLabel(Label):
    """
    Specialized label specifically for displaying items
    """

    def __init__(self, size, item, border = True, **kwargs):
        self.item = item
        #is set when innitailising label, just to make sure
        self.item_image = None
        self.__border = border
        Label.__init__(self, size, **kwargs)
        if self.item != None:
            self.previous_total = self.item.quantity
            # when innitiating make sure the number is displayed
            self.set_text(str(self.previous_total), (6,6),
                          color=self.item.TEXT_COLOR)

    def add_item(self, item):
        self.item = item
        self.image = self._create_image(self.rect.size, self.color)
        self.orig_image = self.image.copy()
        if self.item != None:
            self.previous_total = self.item.quantity
            self.set_text(str(self.previous_total), (6,6),
                          color=self.item.TEXT_COLOR)

        self.changed_image = True

    def _create_image(self, size, color, **kwargs):
        """
        Customized image which is an image containing a block and a border

        :See: Label._create_image()
        :return: pygame Surface object
        """
        size = Size(*size)
        item_size = size - (10, 10)
        # create a background surface
        image = pygame.Surface(size)
        image.fill(color)

        if self.item != None:
            # get the item image and place it in the center
            if isinstance(self.item.material, BuildingMaterial):
                item_image = board.buildings.building_type_from_material(self.item.material).full_image()
            else:
                item_image = self.item.material.surface
            self.item_image = pygame.transform.scale(item_image, item_size)
            image.blit(self.item_image, (size.width / 2 - item_size.width / 2,
                                size.height / 2 - item_size.height / 2))

            # draw rectangle slightly smaller then image
            if self.__border:
                rect = image.get_rect()
                rect.inflate_ip(-4, -4)
                pygame.draw.rect(image, (0, 0, 0), rect, 3)
        return image

    def wupdate(self):
        """
        Make sure to update the amount whenever it changes.
        """
        if self.item != None and self.previous_total != self.item.quantity:
            self.previous_total = self.item.quantity
            self.set_text(str(self.previous_total), (6,6), color=self.item.TEXT_COLOR)


class ProgressArrow(Label):
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        arrow_image = image_sheets["general"].image_at((0, 0), size=(20, 20), color_key=(255, 255, 255))
        arrow_image = pygame.transform.scale(arrow_image, (50,50))
        a_lbl = Label((140, 50), (50, 50), color=INVISIBLE_COLOR)
        a_lbl.set_image(arrow_image)

### ALL OLD STUFF ### could come in handy later

# class Button(Widget):
#     def __init__(self, text="", text_color=(0, 0, 0),
#                  highlight_color=(252, 151, 0)):
#         Widget.__init__(self, size, color, **kwargs)
#         # create a selected and unselected image to swich between
#         text = self.font30.render(text, True, text_color,
#                                   self.background_color)
#         unselected_surface = pygame.Surface(
#             (text.get_rect().width + 14, text.get_rect().height + 14))
#         unselected_surface.fill(self.background_color)
#         self.rect = unselected_surface.blit(text, (
#         text.get_rect().x + 7, text.get_rect().y + 7))
#         self.unselected_image = unselected_surface
#
#         selected_surface = unselected_surface.copy()
#         pygame.draw.rect(selected_surface, (0, 0, 0),
#                          selected_surface.get_rect(), 3)
#         self.selected_image = selected_surface
#
#         self.image = self.unselected_image
#         self.text = text
#         self.selectable = True
#         self.selected = False
#
#     def set_selected(self, selected):
#         self.selected = selected
#         if self.selected:
#             self.image = self.selected_image
#         else:
#             self.image = self.unselected_image


class TextLog:
    def __init__(self):
        self.user_log = {}
        self.warning_log = {}
        self.location = 0

    def __getitem__(self, key):
        return self.user_log[len(self.user_log) - key]

    def __len__(self):
        return len(self.user_log)

    def __iter__(self):
        combined_keys = list(self.user_log.keys()) + list(
            self.warning_log.keys())
        combined_keys.sort()
        combined = {**self.user_log, **self.warning_log}
        sorted_lines = reversed(list(combined[key] for key in combined_keys))
        return iter(sorted_lines)

    def append(self, value):
        self.user_log[len(self.user_log) + len(self.warning_log)] = value
        value.rendered_str = value.rendered_str

    def append_um(self, value):
        # append user messages like warnings and conformations
        self.warning_log[len(self.user_log) + len(self.warning_log)] = value
        value.rendered_str = value.rendered_str

    def line_up(self):
        if not self.user_log:
            return Line()
        if self.location < len(self.user_log):
            self.location += 1
        return list(self.user_log.values())[-self.location].copy()

    def line_down(self):
        if self.location > 0:
            self.location -= 1
        if self.location == 0:
            return Line()
        return list(self.user_log.values())[-self.location].copy()


class Line:
    MAX_LINE_SIZE = 155
    BACKGROUND_COLOR = (75, 75, 75)

    def __init__(self, text="", color=(0, 255, 0)):
        self.color = color
        self.text = text
        self.line_location = len(self.text)
        self.rendered_str = None
        self.font18 = pygame.font.Font(
            constants.DATA_DIR + "//Menu//font//manaspc.ttf", 18)

    def __str__(self):
        return self.text

    def render_str(self, blinker=False, header=""):
        if self.rendered_str:
            return self.rendered_str
        else:
            return self.__get_render_str(blinker, header)

    def __get_render_str(self, blinker, header):
        if blinker:
            t = "{}{}_{}".format(header, self.text[:self.line_location],
                                 self.text[self.line_location + 1:])
        else:
            t = "{}{}".format(header, self.text)
        # if line is bigger then max of screen seperate the words and put them on separate lines
        size = [utilities.SCREEN_SIZE.size[0], 0]
        line_heigth = self.font18.size("k")[1]
        if len(t) > self.MAX_LINE_SIZE:
            words = t.split(" ")
            text = [""]
            l = 0
            for word in words:
                if l + len(word) < self.MAX_LINE_SIZE:
                    text[len(text) - 1] += word + " "
                    l += len(word) + 1
                else:
                    s = self.font18.size(text[len(text) - 1])
                    size[1] += line_heigth
                    l = 0
                    text.append("")
            size[1] += line_heigth
        else:
            text = [t]
            size = self.font18.size(t)
        surf = pygame.Surface((size[0] + 2, size[1] + 2))

        surf.fill(self.BACKGROUND_COLOR)
        for i, line in enumerate(text):
            rt = self.font18.render(line, True, self.color)
            surf.blit(rt, (0, rt.get_size()[1] * i))
        return surf

    def __len__(self):
        return len(self.text)

    def __add__(self, other):
        if self.line_location + other <= len(self.text):
            self.line_location += other

    def __sub__(self, other):
        if self.line_location - other >= 0:
            self.line_location -= other

    def append(self, value):
        self.text = self.text[:self.line_location] + value + self.text[
                                                             self.line_location:]
        self.line_location += len(value)

    def delete(self):
        if self.line_location > 0:
            self.line_location -= 1
            self.text = self.text[:self.line_location] + self.text[
                                                         self.line_location + 1:]

    def copy(self):
        return Line(text=self.text, color=self.color)
