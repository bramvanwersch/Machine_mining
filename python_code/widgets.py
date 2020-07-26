import pygame
from abc import ABC, abstractmethod

from python_code.entities import Entity
from python_code.constants import *
from python_code.event_handling import EventHandler


class Widget(ABC):
    """
    Basic widget class
    """
    def __init__(self, pos, size, selectable = False, **kwargs):
        self.action_functions = {}
        self.selectable = selectable
        self.selected = False

        self.rect = pygame.Rect((*pos, *size))
        self.visible = True

    def wupdate(self):
        """
        A funtion that allows updating a widget each frame
        """
        pass

    def action(self, key):
        """
        Activates an action function bound to a certain key.

        :param key: the key where the action function is bound to
        """
        self.action_functions[key][0](*self.action_functions[key][1])

    def set_action(self, key, action_function, *values):
        """
        Binds a certain key to an action function. Optional values can be
        supplied that are then added as args.

        :param key: the keyboard key that the function should be activated by
        :param action_function: the function that should trigger when the key
        is used and the mouse is over the widget
        :param values: optional values that can be supplied as additional
        arguments to the action function
        """
        self.action_functions[key] = (action_function, *values)

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
    SELECTED_COLOR = (0,0,0)
    def __init__(self, pos, size, color = (255,255,255), **kwargs):
        Widget.__init__(self,pos, size, **kwargs)
        self.image = self._create_image(size, color, **kwargs)
        self.orig_image = self.image.copy()
        self.color = color
        #parameter that tells the container widget containing this widget to
        #reblit it onto its surface.
        self.changed_image = False

    def _create_image(self, size, color, **kwargs):
        """
        Create an image using a size and color

        :param size: a Size object or tuple of lenght 2
        :param color: a rgb color as tuple of lenght 2 or 3
        :param kwargs: additional named arguments
        :return: a pygame Surface object
        """
        if "image" in kwargs:
            return kwargs["image"]
        elif len(color) == 3:
            image = pygame.Surface(size).convert()
        # included alpha channel
        elif len(color) == 4:
            image = pygame.Surface(size).convert_alpha()
        image.fill(color)
        return image

    def set_selected(self, selected):
        """
        Add a border around the outside of a widget when it is selected
        :See: Widget.set_selected()
        """
        super().set_selected(selected)
        if self.selected:
            pygame.draw.rect(self.image, self.image.get_rect(), self.SELECTED_COLOR)
        else:
            self.image = self.orig_image
        self.changed_image = True

    def set_image(self, image):
        """
        Change the full image of a widget or change it back to the orig_image
        by setting image to None
        :param image: a Surface Object or None
        """
        if image == None:
            self.image = self.orig_image
        else:
            self.image = image
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
            self.image = self.orig_image.copy()
        s = FONTS[font_size].render(str(text), True, color)
        self.image.blit(s, pos)
        self.changed_image = True


class ItemLabel(Label):
    """
    Specialized label specifically for displaying items
    """
    SIZE = Size(42, 42)
    ITEM_SIZE = Size(30, 30)
    def __init__(self, pos, item, **kwargs):
        self.item = item
        Label.__init__(self, pos, self.SIZE, **kwargs)
        self.previous_total = self.item.quantity
        # when innitiating make sure the number is displayed
        self.set_text(str(self.previous_total), (10, 10),
                      color=self.item.TEXT_COLOR)

    def _create_image(self, size, color, **kwargs):
        """
        Customized image which is an image containing a block and a border
        :See: Label._create_image()
        :return: pygame Surface object
        """
        # create a background surface
        image = pygame.Surface(self.SIZE)
        image.fill(color)

        # get the item image and place it in the center
        center = pygame.transform.scale(self.item.surface, self.ITEM_SIZE)
        image.blit(center, (self.SIZE.width / 2 - self.ITEM_SIZE.width / 2,
                            self.SIZE.height / 2 - self.ITEM_SIZE.height / 2))

        # draw rectangle slightly smaller then image
        rect = image.get_rect()
        rect.inflate_ip(-4, -4)
        pygame.draw.rect(image, (0, 0, 0), rect, 3)
        return image

    def wupdate(self):
        """
        Make sure to update the amount whenever it changes.
        """
        if self.previous_total != self.item.quantity:
            self.previous_total = self.item.quantity
            self.set_text(str(self.previous_total), (10, 10), color=self.item.TEXT_COLOR)


class BaseConstraints(ABC):
    """
    Determines how widgets are placed inside a __container widget. This is the
    most basic form that allows free placement
    """
    def __init__(self):
        #make sure the constraints are put on a container. This means that certain methods can assume container values
        if not isinstance(self, Pane):
            raise AttributeError("Constraints can only be put on a container widget")

    @abstractmethod
    def add_widget(self, widget):
        """
        Each constraints should have a method for defining addition of widgets

        :param widget: a widget to add
        """
        pass


class FreeConstraints(BaseConstraints):
    """
    Allow widgets to be placed anywhere in a container using coordinates
    relative to the container
    """
    def __init__(self):
        BaseConstraints.__init__(self)

    def add_widget(self, widget):
        """
        Add widgets at the provided rectangle of the widget
        :See: BaseConstraints.add_widget()
        """
        self.widgets.append(widget)
        self.orig_image.blit(widget.image, widget.rect)
        self.image = self.orig_image.copy()

#note this class has not been tested yet
class GridConstraints(BaseConstraints):
    """
    Allow placing of widgets in a grid format. Note this class is not done
    """
    def __init__(self):
        BaseConstraints.__init__(self)
        self.__widget_matrix = []

    def add_widget(self, widget, column, row):
        self.widgets.append(widget)

        #fit the widget in the matrix
        if row > len(self.__widget_matrix) or column > len(self.__widget_matrix[row]):
            raise ValueError("provided row or column for the widget are to big.")
        if row == len(self.__widget_matrix):
            self.__widget_matrix.append([])
        if column == len(self.__widget_matrix[row]):
            self.__widget_matrix[row].append(widget)
        else:
            self.widgets.remove(self.__widget_matrix[row][column])
            self.__widget_matrix[row][column] = widget

        #configure a location that is next to the widgets beside it
        blit_loc = [0, 0]
        if not row - 1 <= 0:
            blit_loc[1] = self.__widget_matrix[row - 1][column].rect.bottom
        if not column - 1 <= 0:
            blit_loc[0] = self.__widget_matrix[row][column - 1].rect.right
        self.orig_image.blit(widget.image, blit_loc, target=self.rect)
        self.image = self.orig_image.copy()


class Pane(Label, EventHandler, FreeConstraints):
    """
    Container widget that allows selecting and acts as an image for a number
    of widgets
    """
    def __init__(self, pos, size, **kwargs):
        Label.__init__(self, pos, size, **kwargs)
        EventHandler.__init__(self, "ALL")
        self.widgets = []
        self._set_constraints()

    def _set_constraints(self):
        """
        Innitiate the appropriate constraints. This makes it so inheriting
        classes can define different constraints
        TODO make this a more appropriate method
        """
        FreeConstraints.__init__(self)

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
        selected_widgets = []
        adjusted_pos = (pos[0] - self.rect.left, pos[1] - self.rect.top)
        for widget in self.widgets:
            if widget.rect.collidepoint(adjusted_pos):
                if isinstance(widget, ScrollPane):
                    selected_widgets.append(widget)
                    lower_selected = widget._find_selected_widgets(adjusted_pos)
                    if lower_selected:
                        for w in lower_selected:
                            selected_widgets.append(w)
                    return selected_widgets
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


class Frame(Entity, Pane):
    """
    Container for widgets, that is an entity so it can act as a window. Every
    gui should have a frame to be able to display and handle updates
    """
    TEXTCOLOR = (0,0,0)
    def __init__(self, pos, size, *groups, title=None, **kwargs):
        Entity.__init__(self, pos, size, *groups, **kwargs)
        Pane.__init__(self, pos, size, **kwargs)
        if title:
            self._set_title(title)

    def update(self, *args):
        """
        Entity update method that is used to update all widgets in the frame

        :See: Entity.update()
        """
        super().update(*args)
        self.wupdate(*args)

    def handle_events(self, events):
        """
        Handle events that are issued to the frame.

        :param events: a list of pygame Events
        activates events on the last element in the selected list (a list of
        all widgets that the user hovers over at this moment). It then tries
        to apply these events to all widgets in this list.
        """
        super().handle_events(events)
        selected = self._find_selected_widgets(pygame.mouse.get_pos())

        #handle all events from the most front widget to the most back one.
        keys = [*self.get_pressed(), *self.get_unpressed()]
        while selected != None and len(selected) > 0:
            widget = selected.pop()
            for index in range(len(keys) - 1, -1, -1):
                key_name = keys[index].name
                if key_name in widget.action_functions:
                    widget.action(key_name)
                    #remove event as to not trigger it twice
                    del keys[index]

    def _set_title(self, title):
        """
        Permanently add a title tot the frame. This is displayed at the top of
        the frame

        :param title: String of what should be displayed
        """
        title = FONTS[30].render(title, True, self.TEXTCOLOR)
        tr = title.get_rect()
        #center the title above the widet
        self.orig_image.blit(title, (int(0.5 * self.rect.width - 0.5 * tr.width), 10))

    def add_border(self, widget):
        """
        add a border around a specified widget. The widget should be in the frame
        :param widget:
        :return:
        """
        rect = widget.rect.inflate(4, 4)
        pygame.draw.rect(self.orig_image, (0,0,0), rect, 3)
        self.image = self.orig_image.copy()


class ScrollPane(Pane, FreeConstraints):
    """
    A Pane that can be scrolled
    """
    SCROLL_SPEED = 20
    #space between the outside of the crafting window and the closest label
    BORDER_SPACE = 3
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.next_widget_topleft = [self.BORDER_SPACE,self.BORDER_SPACE]
        #the total rectangle
        self.total_rect = self.rect.copy()
        #make the total rect slightly larger

        self.__total_offset_y = 0

        self.set_action(4, self.scroll_y, [self.SCROLL_SPEED])
        self.set_action(5, self.scroll_y, [-self.SCROLL_SPEED])

    def add_widget(self, widget):
        """
        Overrides FreeConstriants method and adds widgets automatically so
        they will fit within the pane. Also makes sure that the offset of the
        scrolling is taken into account

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
        self.__total_offset_y += offset_y

        width, height = self.orig_image.get_size()
        copy_surf = self.orig_image.copy()
        self.orig_image.blit(copy_surf, (0, offset_y))
        if offset_y < 0:
            self.orig_image.blit(copy_surf, (0, height + offset_y),
                            (0, 0, width, -offset_y))
        else:
            self.orig_image.blit(copy_surf, (0, 0),
                            (0, height - offset_y, width, offset_y))

        #make sure the location of the widgets contained is moved accordingly
        for widget in self.widgets:
            widget.rect.move_ip(0, offset_y)
            widget.changed_image = True

    def __extend_scroll_image(self, amnt):
        """
        Extend the current orig_image and total_rect to hold more image.

        :param amnt: the amount of pixels to extend the image by in the y
        direction

        Note: There is a bug with calling this at the start. I do not know why,
        it makes it so the image is being displayed over the full lenght
        """
        self.total_rect.height += amnt
        orig_copy = self.orig_image.copy()
        self.orig_image = pygame.Surface(self.total_rect.size).convert()
        self.orig_image.fill(self.color)
        self.orig_image.blit(orig_copy, (0,self.__total_offset_y))


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
