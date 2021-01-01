from abc import ABC, abstractmethod
import pygame
from typing import List, Tuple, Union, Set, Dict, Callable, Any, ClassVar

import entities
import utility.constants as con
import utility.utilities as util
import utility.image_handling as image_handlers
import utility.event_handling as event_handlers
import interfaces.interface_utility as interface_util


class BaseEvent(ABC):
    ALLOWED_STATES: ClassVar[List[str]]

    states: Dict[str, Union[None, Tuple[Callable, List]]]

    def __init__(
        self,
        function: Callable,
        values: List = None,
        types: List = None
    ):
        self.states = {state_name: None for state_name in self.ALLOWED_STATES}
        self.add_action(function, values, types)

    def add_action(
        self,
        function: Callable,
        values: List = None,
        types: List = None
    ) -> None:
        """Add an action for one of the 2 states"""
        types = types if types else self.ALLOWED_STATES
        values = values if values else []
        for _type in types:
            if _type not in types:
                raise util.GameException("State {} is not allowed for {} use one of {}".format(_type, type(self),
                                                                                               self.ALLOWED_STATES))
            self.states[_type] = (function, values)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def ALLOWED_STATES(self) -> List[str]:
        pass

    def __call__(
        self,
        *args,
        **kwargs
    ) -> Any:
        """Allows the class to act like a function"""
        if self.states[args[0]] is not None:
            function, values = self.states[args[0]]
            function(*values)


class KeyEvent(BaseEvent):
    """
    Action function for defining actions for widgets. Can be called like a
    function
    """
    ALLOWED_STATES: ClassVar[List[str]] = ["pressed", "unpressed"]


class HoverEvent(BaseEvent):
    ALLOWED_STATES: ClassVar[List[str]] = ["hover", "unhover"]

    __prev_hover_state: str
    __continious: bool

    def __init__(
        self,
        function: Callable,
        values: List = None,
        types: List = None,
        continious: bool = False
    ):
        super().__init__(function, values, types)
        self.__prev_hover_state = "unhover"
        self.__continious = continious

    def __call__(
        self,
        *args,
        **kwargs
    ) -> Any:
        """Make sure that hover events are not triggered every time if the hover state did not change unless forced
        by __continious flag"""
        if args[0] != self.__prev_hover_state or self.__continious:
            self.__prev_hover_state = args[0]
            function, values = self.states[args[0]]
            function(*values)


class SelectionGroup:
    """A collection of widgets to control selection of the widgets"""
    multi_mode: bool
    __widgets: Set

    def __init__(
        self,
        multiple: bool = False
    ):
        self.multi_mode = multiple
        self.__widgets = set()

    def add(
        self,
        widget
    ) -> None:
        self.__widgets.add(widget)

    def select(
        self,
        widget,
        *args
    ) -> None:
        if not self.multi_mode:
            for w in self.__widgets:
                w.set_selected(False)
        widget.set_selected(True, *args)

    def off(self) -> None:
        """Turn all widgets off"""
        [w.set_selected(False) for w in self.__widgets]

    def on(self) -> None:
        """Turn all widgets on"""
        if self.multi_mode:
            [w.set_selected(True) for w in self.__widgets]


class Widget(event_handlers.EventHandler, ABC):
    """
    Basic widget class
    """
    __listened_for_events: Dict[int, KeyEvent]
    selectable: bool
    selected: bool
    rect: pygame.Rect
    visible: bool

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        selectable: bool = True,
        recordable_keys: List = None,
        **kwargs
    ):
        recordable_keys = recordable_keys if recordable_keys else None
        super().__init__(recordable_keys)
        self.__listened_for_events = {}
        # are allowed to select
        self.selectable = selectable
        # state of selection
        self.selected = False

        # innitial position is 0, 0
        self.rect = pygame.Rect((0, 0, size[0], size[1]))
        self.visible = True

    def wupdate(self):
        """
        A function that allows updating a widget each frame
        """
        pass

    def action(
        self,
        key: int,
        _type: str
    ) -> Any:
        """Activates an action function bound to a certain key."""
        self.__listened_for_events[key](_type)

    def add_key_event_listener(
        self,
        key: int,
        action_function: Callable,
        values: List = None,
        types: List = None
    ) -> None:
        """Link functions to key events and trigger when appropriate"""
        if key in self.__listened_for_events:
            self.__listened_for_events[key].add_action(action_function, values, types)
        else:
            self.__listened_for_events[key] = KeyEvent(action_function, values, types)
            self.add_recordable_key(key)

    def add_hover_event_listener(
        self,
        hover_action_function: Callable,
        unhover_action_function: Callable,
        hover_values: List = None,
        unhover_values: List = None
    ) -> None:
        """Link functions to hover events and trigger when appropriate"""
        self.add_key_event_listener(con.BTN_HOVER, hover_action_function, values=hover_values, types=["pressed"])
        self.add_key_event_listener(con.BTN_UNHOVER, unhover_action_function, values=unhover_values,
                                    types=["unpressed"])
        self.add_recordable_key(con.BTN_HOVER)
        self.add_recordable_key(con.BTN_UNHOVER)

    def handle_events(
        self,
        events: List,
        consume: bool = True
    ) -> List[pygame.event.Event]:
        leftover_events = super().handle_events(events, consume)

        pressed = self.get_all_pressed()
        unpressed = self.get_all_unpressed()
        keys = [*zip(pressed, ["pressed"] * len(pressed)),
                *zip(unpressed, ["unpressed"] * len(unpressed))]
        for key, _type in keys:
            if key.name in self.__listened_for_events:
                self.action(key.name, _type)
        return leftover_events

    def set_selected(
        self,
        selected: bool
    ) -> None:
        """Set a widget as selected. Allowing a highlight for instance"""
        if self.selectable:
            self.selected = selected


class Label(Widget):
    """
    Bsically a widget that allows image manipulation
    """
    SELECTED_COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (255, 255, 255)

    surface: Union[None, pygame.Surface]
    orig_surface: Union[None, pygame.Surface]
    color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List]
    changed_image: bool
    text_image: Union[None, pygame.Surface]

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List] = (255, 255, 255),
        border: bool = False,
        border_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        image: pygame.Surface = None,
        image_pos: Union[str, Tuple[int, int], List[int]] = "center",
        image_size: Union[util.Size, Tuple[int, int], List[int]] = None,
        text: str = None,
        text_pos: Union[str, Tuple[int, int], List[int]] = "center",
        text_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        font_size: int = 15,
        **kwargs
    ):
        super().__init__(size, **kwargs)
        self.color = color
        self.surface = self._create_background(size, self.color, border, border_color)
        self.orig_surface = self.surface.copy()

        # variables for saving the values used for creation of the surface
        self.image_specifications = None
        self.text_specifications = None
        self.selection_specifications = None
        self.create_surface(image, image_pos, image_size, text, text_pos, text_color, font_size)

        # parameter that tells the container widget containing this widget to reblit it onto its surface.
        self.changed_image = True

    def create_surface(
        self,
        image: pygame.Surface = None,
        image_pos: Union[str, Tuple[int, int], List[int]] = "center",
        image_size: Union[util.Size, Tuple[int, int], List[int]] = None,
        text: str = None,
        text_pos: Union[str, Tuple[int, int], List[int]] = "center",
        text_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        font_size: int = 15,
    ) -> None:
        if image is not None:
            self.set_image(image, image_pos, image_size)
        if text is not None:
            self.set_text(text, text_pos, text_color, font_size)

    def _create_background(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List],
        border: bool = False,
        border_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0)
    ) -> pygame.Surface:
        """Create the innitial image. This image will be tracked using the orig_image attribute"""
        if len(color) == 3:
            lbl_surface = pygame.Surface(size).convert()
        # included alpha channel
        elif len(color) == 4:
            lbl_surface = pygame.Surface(size).convert_alpha()
        else:
            raise util.GameException("Color argument {} is invalid should have lenght 3 or 4 not {}"
                                     .format(color, len(color)))
        lbl_surface.fill(color)
        if border:
            pygame.draw.rect(lbl_surface, border_color, (0, 0, size[0], size[1]), 4)
        return lbl_surface

    def set_selected(self, selected, color=None):
        super().set_selected(selected)
        self.selection_specifications = [selected, color]
        if color is None:
            color = self.SELECTED_COLOR
        if self.selected:
            pygame.draw.rect(self.surface, color, self.surface.get_rect(), 3)
        else:
            self.clean_image(text=False, image=False)

        self.changed_image = True

    def set_image(self, image, pos="center", size=None, cleaning=False):
        if not cleaning:
            self.clean_image(text=False, selected=False)
        self.image_specifications = [image.copy(), pos, size]
        if size is not None:
            image = pygame.transform.scale(image, size)
        rect = image.get_rect()
        if pos == "center":
            pos = (self.rect.width / 2 - rect.width / 2, self.rect.height / 2 - rect.height / 2)
        self.surface.blit(image, pos)
        # make sure that the selection rectangle is shown
        if self.selected:
            self.set_selected(True)
        self.changed_image = True

    def set_text(self, text, pos, color=(0, 0, 0), font_size=15, cleaning=False):
        if not cleaning:
            self.clean_image(image=False, selected=False)
        self.text_specifications = [text, pos, color, font_size]
        s = con.FONTS[font_size].render(str(text), True, color)
        rect = s.get_rect()
        if pos == "center":
            pos = (self.rect.width / 2 - rect.width / 2, self.rect.height / 2 - rect.height / 2)
        self.surface.blit(s, pos)
        self.text_image = self.surface.copy()
        # make sure that the selection rectangle is shown
        if self.selected:
            self.set_selected(True)
        self.changed_image = True

    def clean_image(self, text=True, selected=True, image=True):
        # reset the surface and readd anything that should not have been cleared
        self.surface = self.orig_surface.copy()
        if not image and self.image_specifications:
            self.set_image(*self.image_specifications, cleaning=True)
        if not text and self.text_specifications:
            self.set_text(*self.text_specifications, cleaning=True)
        if not selected and self.selected:
            self.set_selected(*self.selection_specifications)


class Button(Label):
    COLOR_CHANGE = 75
    def __init__(self, size, hover_image=None, **kwargs):
        super().__init__(size, **kwargs)
        if hover_image is not None:
            self._hover_surface = hover_image
            self.add_hover_event_listener(self.set_image, self.set_image, hover_values=[self._hover_surface],
                                          unhover_values=[self.surface])
        else:
            self._hover_surface = self.create_hover_surface()
            self.add_hover_event_listener(self.set_image, self.clean_image, hover_values=[self._hover_surface],
                                          unhover_values=[False, False, True])

    def create_hover_surface(self):
        """Fill all pixels of color self.color with a new color. Carfull do not call to much"""
        w, h = self.surface.get_size()
        hover_color = self.__hover_color()
        hover_surface = self.surface.copy()
        for x in range(w):
            for y in range(h):
                present_color = self.surface.get_at((x, y))
                if present_color == self.color:
                    hover_surface.set_at((x, y), hover_color)
        return hover_surface

    def __hover_color(self):
        new_color = []
        for channel in self.color:
            if channel + self.COLOR_CHANGE > 255:
                new_color.append(channel - self.COLOR_CHANGE)
            else:
                new_color.append(channel + self.COLOR_CHANGE)
        return new_color


class Pane(Label):
    """
    Container widget that allows selecting and acts as an image for a number
    of widgets
    """
    def __init__(self, size, **kwargs):
        Label.__init__(self, size, **kwargs)
        self.widgets = []
        self.selectable = False

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
        self.orig_surface.blit(widget.surface, pos)
        self.surface = self.orig_surface.copy()

    def wupdate(self, *args):
        """
        Update all the widgets in this container, and make sure to redraw them
        when needed

        :param args: optional argumetns
        """
        for widget in self.widgets:
            widget.wupdate()
            if widget.changed_image:
                self.__redraw_widget(widget)
                widget.changed_image = False

    def _find_hovered_widgets(self, pos):
        """
        Recursively traverse all containers in containers to find the widget
        the user is hovering over. Then activate a potential action function

        :param pos: The position of the mouse relative to the container
        :return: a list of selected widgets with the bottommost one at the end
        of the list
        """
        selected_widgets = []
        unselected_widgets = []
        adjusted_pos = (pos[0] - self.rect.left, pos[1] - self.rect.top)
        for widget in self.widgets:
            collide = widget.rect.collidepoint(adjusted_pos)
            if collide:
                if isinstance(widget, Pane):
                    selected_widgets.append(widget)
                    lower_selected, lower_unselected = widget._find_hovered_widgets(adjusted_pos)
                    if lower_selected:
                        selected_widgets.extend(lower_selected)
                    elif lower_unselected:
                        lower_unselected.extend(lower_unselected)
                else:
                    selected_widgets.append(widget)
            else:
                unselected_widgets.append(widget)
        return selected_widgets, unselected_widgets

    def _get_selectable_widgets(self):
        selectable_widgets = []
        for widget in self.widgets:
            if widget.selectable:
                selectable_widgets.append(widget)
            elif isinstance(widget, Pane):
                selectable_widgets.extend(widget._get_selectable_widgets())
        return selectable_widgets

    def __redraw_widget(self, widget):
        """
        Method that redraws a widget in a container.

        :param widget:

        Sets the self.changed_image flag to True to forse potential containers
        that contain this container to redraw this container
        """
        self.orig_surface.blit(widget.surface, dest=widget.rect, area=(0, 0, *widget.rect.size))
        self.surface = self.orig_surface.copy()
        self.changed_image = True

    def add_border(self, widget, color=(0,0,0)):
        """
        add a border around a specified widget. The widget should be in the pane
        :param widget:
        :return:
        """
        rect = widget.rect.inflate(4, 4)
        pygame.draw.rect(self.orig_surface, color, rect, 3)
        self.surface = self.orig_surface.copy()


class Frame(entities.ZoomableEntity, Pane):
    """
    Container for widgets, that is an entity so it can act as a window. Every
    gui should have a frame to be able to display and handle updates
    """
    def __init__(self, pos, size, *groups, **kwargs):
        Pane.__init__(self, size, **kwargs)
        entities.ZoomableEntity.__init__(self, pos, size, *groups, **kwargs)
        self.selected_widget = None
        self.add_key_event_listener(con.K_UP, self.__select_next_widget, values=[con.K_UP], types=["pressed"])
        self.add_key_event_listener(con.K_DOWN, self.__select_next_widget, values=[con.K_DOWN], types=["pressed"])
        self.add_key_event_listener(con.K_LEFT, self.__select_next_widget, values=[con.K_LEFT], types=["pressed"])
        self.add_key_event_listener(con.K_RIGHT, self.__select_next_widget, values=[con.K_RIGHT], types=["pressed"])
        self.add_key_event_listener(con.K_RETURN, self.__activate_selected_widget, types=["pressed"])

    def update(self, *args):
        """
        Entity update method that is used to update all widgets in the frame

        :See: Entity.update()
        """
        super().update(*args)
        self.wupdate(*args)

    def zoom(self, zoom):
        self._zoom = zoom

    @property
    def image(self):
        return self.surface

    @image.setter
    def image(self, v):
        self.surface = v

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

    def __select_next_widget(self, direction):
        selectable_widgets = self._get_selectable_widgets()

        if len(selectable_widgets) == 0:
            return
        # if no selected take top most widget
        if self.selected_widget is None:
            self.selected_widget = sorted(self.widgets, key=lambda x: (x.rect.centery, x.rect.centerx))[0]
            self.selected_widget.set_selected(True)
            return
        else:
            s_rect = self.selected_widget.rect
            self.selected_widget.set_selected(False)
        if direction == con.K_UP or direction == con.K_DOWN:
            # make sure widgets are partially overlapping in the x-direction
            elligable_widgets = [w for w in selectable_widgets
                                if (w.rect.left >= s_rect.left and w.rect.left <= s_rect.right) or
                                (w.rect.right <= s_rect.right and w.rect.right >= s_rect.left)]
            if direction == con.K_UP:
                elligable_widgets_above = [w for w in elligable_widgets if w.rect.centery < s_rect.centery]
                if len(elligable_widgets_above) > 0:
                    # select the closest above the current
                    self.selected_widget = sorted(elligable_widgets_above, key=lambda x: s_rect.centery - x.rect.centery)[0]
            else:
                elligable_widgets_below = [w for w in elligable_widgets if w.rect.centery > s_rect.centery]
                if len(elligable_widgets_below) > 0:
                    # select the closest bewow the current
                    self.selected_widget = sorted(elligable_widgets_below, key=lambda x: x.rect.centery - s_rect.centery)[0]
        if direction == con.K_LEFT or direction == con.K_RIGHT:
            # make sure widgets are partially overlapping in the x-direction
            elligable_widgets = [w for w in selectable_widgets
                                if (w.rect.top >= s_rect.top and w.rect.top <= s_rect.bottom) or
                                (w.rect.bottom <= s_rect.bottom and w.rect.bottom >= s_rect.top)]
            if direction == con.K_LEFT:
                elligable_widgets_west = [w for w in elligable_widgets if w.rect.centerx < s_rect.centerx]
                if len(elligable_widgets_west) > 0:
                    # select the closest above the current
                    self.selected_widget = sorted(elligable_widgets_west, key=lambda x: s_rect.centerx - x.rect.centerx)[0]
            else:
                elligable_widgets_east = [w for w in elligable_widgets if w.rect.centerx > s_rect.centerx]
                if len(elligable_widgets_east) > 0:
                    # select the closest bewow the current
                    self.selected_widget = sorted(elligable_widgets_east, key=lambda x: x.rect.centerx - s_rect.centerx)[0]
        self.selected_widget.set_selected(True)

    def __activate_selected_widget(self):
        if self.selected_widget != None:
            self.selected_widget.action(1, "unpressed")

    def handle_events(self, events, consume=True):
        # events that are triggered on this frame widget trigger first
        leftover_events = super().handle_events(events, consume)
        pos = pygame.mouse.get_pos()
        if self.static:
            pos = interface_util.screen_to_board_coordinate(pos, self.groups()[0].target, 1)
        hovered, unhovered = self._find_hovered_widgets(pos)

        # add a hover event that can be consumed in the same way as normal events.
        leftover_events.append(pygame.event.Event(con.HOVER, button=con.BTN_HOVER))
        # handle all events from the most front widget to the most back one.
        while hovered is not None and len(hovered) > 0 and len(leftover_events) > 0:
            widget = hovered.pop()
            leftover_events = widget.handle_events(leftover_events)
        unhover_event = [pygame.event.Event(con.UNHOVER, button=con.BTN_UNHOVER)]
        for widget in unhovered:
            widget.handle_events(unhover_event)
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

        self.add_key_event_listener(4, self.scroll_y, [self.SCROLL_SPEED])
        self.add_key_event_listener(5, self.scroll_y, [-self.SCROLL_SPEED])

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
        self.orig_surface.blit(widget.surface, widget.rect)

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
        width, height = self.orig_surface.get_size()
        self.__total_offset_y += offset_y
        self.orig_surface.fill(self.color)
        self.orig_surface.scroll(0, offset_y)

        #make sure the location of the widgets contained is moved accordingly
        for widget in self.widgets:
            widget.rect.move_ip(0, offset_y)
            widget.changed_image = True

    def __extend_scroll_image(self, amnt):
        """
        Extend the current orig_surface and total_rect to hold more image.

        :param amnt: the amount of pixels to extend the image by in the y
        direction

        """
        self.total_rect.height += amnt
        orig_copy = self.orig_surface.copy()
        self.orig_surface = pygame.Surface(self.total_rect.size).convert()
        self.orig_surface.fill(self.color)
        self.orig_surface.blit(orig_copy, (0,self.__total_offset_y))


class ItemDisplay(Label):

    def __init__(self, size: util.Size, item=None, border=True, **kwargs):
        super().__init__(size, **kwargs)
        self.item = item
        self.__border = border
        self.previous_total = 0
        if self.item:
            self.add_item(item)

    def add_item(self, item):
        self.item = item
        self.__add_item_image()
        self.__add_quantity_text()
        if self.__border:
            rect = self.rect
            rect.inflate_ip(-4, -4)
            pygame.draw.rect(self.surface, (0, 0, 0), rect, 3)
        self.changed_image = True

    def __add_item_image(self):
        item_size = util.Size(*self.rect.size) - (10, 10)
        item_image = self.item.material.full_surface
        item_image = pygame.transform.scale(item_image, item_size)
        self.set_image(item_image)

    def __add_quantity_text(self):
        self.previous_total = self.item.quantity
        self.set_text(str(self.previous_total), (5, 0), color=self.item.TEXT_COLOR)

    def wupdate(self):
        """
        Make sure to update the amount whenever it changes.
        """
        super().wupdate()
        if self.item is not None and self.previous_total != self.item.quantity:
            self.__add_quantity_text()


class ProgressArrow(Label):
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        arrow_image = image_handlers.image_sheets["general"].image_at((0, 0), size=(20, 20))
        arrow_image = pygame.transform.scale(arrow_image, (50,50))
        a_lbl = Label((140, 50), (50, 50), color=con.INVISIBLE_COLOR)
        a_lbl.set_image(arrow_image)

### ALL OLD STUFF ### could come in handy later


# class TextLog:
#     def __init__(self):
#         self.user_log = {}
#         self.warning_log = {}
#         self.location = 0
#
#     def __getitem__(self, key):
#         return self.user_log[len(self.user_log) - key]
#
#     def __len__(self):
#         return len(self.user_log)
#
#     def __iter__(self):
#         combined_keys = list(self.user_log.keys()) + list(
#             self.warning_log.keys())
#         combined_keys.sort()
#         combined = {**self.user_log, **self.warning_log}
#         sorted_lines = reversed(list(combined[key] for key in combined_keys))
#         return iter(sorted_lines)
#
#     def append(self, value):
#         self.user_log[len(self.user_log) + len(self.warning_log)] = value
#         value.rendered_str = value.rendered_str
#
#     def append_um(self, value):
#         # append user messages like warnings and conformations
#         self.warning_log[len(self.user_log) + len(self.warning_log)] = value
#         value.rendered_str = value.rendered_str
#
#     def line_up(self):
#         if not self.user_log:
#             return Line()
#         if self.location < len(self.user_log):
#             self.location += 1
#         return list(self.user_log.values())[-self.location].copy()
#
#     def line_down(self):
#         if self.location > 0:
#             self.location -= 1
#         if self.location == 0:
#             return Line()
#         return list(self.user_log.values())[-self.location].copy()
#
#
# class Line:
#     MAX_LINE_SIZE = 155
#     BACKGROUND_COLOR = (75, 75, 75)
#
#     def __init__(self, text="", color=(0, 255, 0)):
#         self.color = color
#         self.text = text
#         self.line_location = len(self.text)
#         self.rendered_str = None
#         self.font18 = pygame.font.Font(
#             con.DATA_DIR + "//Menu//font//manaspc.ttf", 18)
#
#     def __str__(self):
#         return self.text
#
#     def render_str(self, blinker=False, header=""):
#         if self.rendered_str:
#             return self.rendered_str
#         else:
#             return self.__get_render_str(blinker, header)
#
#     def __get_render_str(self, blinker, header):
#         if blinker:
#             t = "{}{}_{}".format(header, self.text[:self.line_location],
#                                  self.text[self.line_location + 1:])
#         else:
#             t = "{}{}".format(header, self.text)
#         # if line is bigger then max of screen seperate the words and put them on separate lines
#         size = [con.SCREEN_SIZE.size[0], 0]
#         line_heigth = self.font18.size("k")[1]
#         if len(t) > self.MAX_LINE_SIZE:
#             words = t.split(" ")
#             text = [""]
#             l = 0
#             for word in words:
#                 if l + len(word) < self.MAX_LINE_SIZE:
#                     text[len(text) - 1] += word + " "
#                     l += len(word) + 1
#                 else:
#                     s = self.font18.size(text[len(text) - 1])
#                     size[1] += line_heigth
#                     l = 0
#                     text.append("")
#             size[1] += line_heigth
#         else:
#             text = [t]
#             size = self.font18.size(t)
#         surf = pygame.Surface((size[0] + 2, size[1] + 2))
#
#         surf.fill(self.BACKGROUND_COLOR)
#         for i, line in enumerate(text):
#             rt = self.font18.render(line, True, self.color)
#             surf.blit(rt, (0, rt.get_size()[1] * i))
#         return surf
#
#     def __len__(self):
#         return len(self.text)
#
#     def __add__(self, other):
#         if self.line_location + other <= len(self.text):
#             self.line_location += other
#
#     def __sub__(self, other):
#         if self.line_location - other >= 0:
#             self.line_location -= other
#
#     def append(self, value):
#         self.text = self.text[:self.line_location] + value + self.text[
#                                                              self.line_location:]
#         self.line_location += len(value)
#
#     def delete(self):
#         if self.line_location > 0:
#             self.line_location -= 1
#             self.text = self.text[:self.line_location] + self.text[
#                                                          self.line_location + 1:]
#
#     def copy(self):
#         return Line(text=self.text, color=self.color)
