#!/usr/bin/python3
"""Interface widgets"""

# library imports
from abc import ABC
import pygame
from typing import List, Tuple, Union, Set, Dict, Callable, Any, ClassVar, TYPE_CHECKING

# own imports
import entities
import utility.constants as con
import utility.utilities as util
import utility.event_handling as event_handlers
import utility.image_handling as image_handling
import interfaces.interface_utility as interface_util
if TYPE_CHECKING:
    import inventories


class WidgetEvent(ABC):
    ALLOWED_STATES: ClassVar[List[str]] = ["pressed", "unpressed"]

    states: Dict[str, Union[None, Tuple[Callable, List]]]
    __prev_state: str
    __no_repeat: bool

    def __init__(
        self,
        function: Callable,
        values: List = None,
        types: List = None,
        no_repeat: bool = False
    ):
        self.states = {state_name: None for state_name in self.ALLOWED_STATES}
        self.add_action(function, values, types)
        self.__prev_state = "unpressed"
        self.__no_repeat = no_repeat

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

    def __call__(
        self,
        *args,
        **kwargs
    ) -> Any:
        """Allows the class to act like a function"""
        if self.states[args[0]] is not None:
            if self.__no_repeat and self.__prev_state == args[0]:
                return
            function, values = self.states[args[0]]
            function(*values)
        self.__prev_state = args[0]


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


class WidgetPosition:
    """Configure a toplet position of the inner rect in such a way that the rect is placed in a desired way inside
    the outer rect based on the position value"""

    __inner_rect: pygame.Rect
    __outer_rect: pygame.Rect
    position: Union[Tuple[int, int], List[int]]

    def __init__(
        self,
        pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]],
        inner_rect: pygame.Rect,
        outer_rect: pygame.Rect
    ):
        self.__inner_rect = inner_rect
        self.__outer_rect = outer_rect
        self.position = self.__convert_location(pos)

    def __convert_location(self, pos) -> List[int]:
        pos = list(pos)
        if type(pos[0]) in [float, int]:
            pos[0] = round(pos[0])
        elif pos[0] in ["center", "C"]:
            pos[0] = self.__centerx()
        elif pos[0] in ["west", "W"]:
            pos[0] = self.__west()
        elif pos[0] in ["east", "E"]:
            pos[0] = self.__east()

        if type(pos[1]) in [float, int]:
            pos[1] = round(pos[1])
        if pos[1] in ["center", "C"]:
            pos[1] = self.__centery()
        elif pos[1] in ["north", "N"]:
            pos[1] = self.__north()
        elif pos[1] in ["south", "S"]:
            pos[1] = self.__south()
        return pos

    def __centerx(self) -> int:
        return round(self.__outer_rect.width / 2 - self.__inner_rect.width / 2)

    def __centery(self) -> int:
        return round(self.__outer_rect.height / 2 - self.__inner_rect.height / 2)

    def __west(self) -> int:
        return self.__outer_rect.left

    def __east(self) -> int:
        return self.__outer_rect.right - self.__inner_rect.width

    def __north(self) -> int:
        return self.__outer_rect.top

    def __south(self) -> int:
        return self.__outer_rect.bottom - self.__inner_rect.height

    def __getitem__(self, item):
        return self.position[item]

    def __len__(self):
        return len(self.position)


class Widget(event_handlers.EventHandler, ABC):
    """
    Basic widget class
    """
    _listened_for_events: Dict[int, WidgetEvent]
    selectable: bool
    selected: bool
    rect: pygame.Rect
    visible: bool
    board_position: Union[Tuple[int, int], List[int]]
    surface: Union[None, pygame.Surface] = NotImplemented
    orig_surface: Union[None, pygame.Surface] = NotImplemented

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        selectable: bool = True,
        recordable_keys: List = None,
        tooltip: "Tooltip" = None,
        board_pos: Union[Tuple[int, int], List[int]] = (0, 0),
        **kwargs
    ):
        recordable_keys = recordable_keys if recordable_keys else None
        super().__init__(recordable_keys)
        self._listened_for_events = {}
        # are allowed to select
        self.selectable = selectable
        # state of selection
        self.selected = False

        # innitial position is 0, 0
        self.rect = pygame.Rect((0, 0, size[0], size[1]))
        self.visible = True
        self.board_position = list(board_pos)
        if tooltip:
            self.add_tooltip(tooltip)

    def wupdate(self):
        """
        A function that allows updating a widget each frame
        """
        pass

    def move(
        self,
        offset: Union[Tuple[int, int], List[int]]
    ) -> None:
        self.board_position[0] += offset[0]
        self.board_position[1] += offset[1]

    def action(
        self,
        key: event_handlers.Key,
        _type: str
    ) -> Any:
        """Activates an action function bound to a certain key."""
        self._listened_for_events[key.name](_type)

    def add_tooltip(
        self,
        tooltip: "Tooltip"
    ) -> None:
        self.add_hover_event_listener(tooltip.show_tooltip, tooltip.show_tooltip, hover_values=[True],
                                      unhover_values=[False])

    def add_key_event_listener(
        self,
        key: int,
        action_function: Callable,
        values: List = None,
        types: List = None,
        no_repeat: bool = False
    ) -> None:
        """Link functions to key events and trigger when appropriate"""
        if key in self._listened_for_events:
            self._listened_for_events[key].add_action(action_function, values, types)
        else:
            self._listened_for_events[key] = WidgetEvent(action_function, values, types, no_repeat)
            self.add_recordable_key(key)

    def add_hover_event_listener(
        self,
        hover_action_function: Callable,
        unhover_action_function: Callable,
        hover_values: List = None,
        unhover_values: List = None
    ) -> None:
        """Link functions to hover events and trigger when appropriate"""
        self.add_key_event_listener(con.BTN_HOVER, hover_action_function, values=hover_values, types=["pressed"],
                                    no_repeat=True)
        self.add_key_event_listener(con.BTN_HOVER, unhover_action_function, values=unhover_values, types=["unpressed"],
                                    no_repeat=True)

    def handle_events(
        self,
        events: List,
        type_: str = None,
        consume_events: bool = True
    ) -> List[pygame.event.Event]:
        leftover_events = super().handle_events(events, consume_events)

        pressed = self.get_all_pressed()
        unpressed = self.get_all_unpressed()
        keys = [*zip(pressed, ["pressed"] * len(pressed)),
                *zip(unpressed, ["unpressed"] * len(unpressed))]
        for key, _type in keys:
            self.action(key, _type)
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
    Widget that can contain text an image and can be selected

    A Label has 3 layers that can be present an image a text and a selection rectangle on the outside. The order of
    drawing is always image then text then selection.
    """
    SELECTED_COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (255, 255, 255)

    color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List]
    surface: Union[None, pygame.Surface]
    orig_surface: Union[None, pygame.Surface]

    __image_specifications: Union[None, List]
    __text_specifications: Union[None, List]
    __selection_specifications: Union[None, List]

    changed_image: bool

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List] = (255, 255, 255),
        border: bool = False,
        border_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        border_shrink: Union[Tuple[int, int], List[int]] = (0, 0),
        border_width: int = 3,
        image: pygame.Surface = None,
        image_pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]] = ("center", "center"),
        image_size: Union[util.Size, Tuple[int, int], List[int]] = None,
        text: str = None,
        text_pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]] = ("center", "center"),
        text_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        font_size: int = 15,
        **kwargs
    ):
        super().__init__(size, **kwargs)
        self.color = color
        self.surface = self.__create_background(size, self.color, border, border_color, border_width, border_shrink)
        self.orig_surface = self.surface.copy()

        # variables for saving the values used for creation of the surface
        self.__image_specifications = None
        self.__text_specifications = None
        self.__selection_specifications = None
        self.create_surface(image, image_pos, image_size, text, text_pos, text_color, font_size)

        # parameter that tells the container widget containing this widget to reblit it onto its surface.
        self.changed_image = True

    def create_surface(
        self,
        image: pygame.Surface = None,
        image_pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]] = ("center", "center"),
        image_size: Union[util.Size, Tuple[int, int], List[int]] = None,
        text: str = None,
        text_pos: Union[Tuple[Union[int, str], Union[str, int]], List[int]] = ("center", "center"),
        text_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        font_size: int = 15,
    ) -> None:
        if image is not None:
            self.set_image(image, image_pos, image_size)
        if text is not None:
            self.set_text(text, text_pos, text_color, font_size)

    def __create_background(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List],
        border: bool = False,
        border_color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        border_width: int = 3,
        border_shrink: Union[Tuple[int, int], List[int]] = (0, 0)
    ) -> pygame.Surface:
        """Create background image where text highlight and images can be displayed on"""
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
            pygame.draw.rect(lbl_surface, border_color, (int(border_shrink[0] / 2), int(border_shrink[1] / 2),
                                                         size[0] - border_shrink[0], size[1] - border_shrink[1]),
                             border_width)
        return lbl_surface

    def get_text(self):
        if self.__text_specifications:
            return self.__text_specifications[0]
        return ""

    def set_image(
        self,
        image: pygame.Surface,
        pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]] = ("center", "center"),
        size: Union[util.Size, Tuple[int, int], List[int]] = None,
        redraw: bool = True
    ) -> None:
        if redraw:
            self.clean_surface()
        if size is not None:
            image = pygame.transform.scale(image, size)
        rect = image.get_rect()
        pos = WidgetPosition(pos, rect, self.rect)
        # make sure transform is not reopeaditly triggered
        self.__image_specifications = [image.copy(), pos, None]
        self.surface.blit(image, pos.position)
        if redraw:
            if self.__text_specifications:
                self.set_text(*self.__text_specifications, redraw=False)
            if self.__selection_specifications:
                self.set_selected(*self.__selection_specifications, redraw=False)
        self.changed_image = True

    def set_text(
        self,
        text: str,
        pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]] = ("center", "center"),
        color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0),
        font_size: int = 15,
        redraw: bool = True
    ) -> None:

        s = con.FONTS[font_size].render(str(text), True, color)
        rect = s.get_rect()
        pos = WidgetPosition(pos, rect, self.rect)
        self.__text_specifications = [text, pos, color, font_size]

        if redraw:
            self.clean_surface(clean_image=False)
        self.surface.blit(s, pos.position)
        # make sure that the selection rectangle is shown
        if redraw:
            if self.__selection_specifications:
                self.set_selected(*self.__selection_specifications, redraw=False)
        self.changed_image = True

    def set_selected(
        self,
        selected: bool,
        color: Union[Tuple[int, int, int], List[int]] = None,
        redraw: bool = True
    ) -> None:
        super().set_selected(selected)
        if not self.selectable:
            return
        self.__selection_specifications = [selected, color]
        if redraw:
            self.clean_surface(clean_text=False, clean_image=False)
        if color is None:
            color = self.SELECTED_COLOR
        if self.selected:
            pygame.draw.rect(self.surface, color, self.surface.get_rect(), 3)

        self.changed_image = True

    def clean_surface(
        self,
        clean_text: bool = True,
        clean_selected: bool = True,
        clean_image: bool = True
    ) -> None:
        """Allow to clean a certain type or multiple of the image"""
        # reset the surface and reado anything that should not have been cleared
        self.surface = self.orig_surface.copy()
        if not clean_image and self.__image_specifications:
            self.set_image(*self.__image_specifications, redraw=False)
        if not clean_text and self.__text_specifications:
            self.set_text(*self.__text_specifications, redraw=False)
        if not clean_selected and self.__selection_specifications:
            self.set_selected(*self.__selection_specifications, redraw=False)
        self.changed_image = True


class Button(Label):
    COLOR_CHANGE: ClassVar[int] = 75

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        hover_image: Union[None, pygame.Surface] = None,
        **kwargs
    ):
        super().__init__(size, **kwargs)
        if hover_image is not None:
            hover_surface = hover_image
        else:
            hover_surface = self.create_hover_surface()
        self.add_hover_event_listener(self.set_image, self.set_image, hover_values=[hover_surface],
                                      unhover_values=[self.surface])

    def create_hover_surface(self) -> pygame.Surface:
        """Fill all pixels of color self.color with a new color. Method is relatovely heavy"""
        w, h = self.surface.get_size()
        hover_color = self.__hover_color()
        hover_surface = self.surface.copy()
        for x in range(w):
            for y in range(h):
                present_color = self.surface.get_at((x, y))
                if present_color == self.color:
                    hover_surface.set_at((x, y), hover_color)
        return hover_surface

    def __hover_color(self) -> List[int]:
        """ Create a hover color. Which is a lighter color"""
        new_color = []
        for channel in self.color:
            if channel + self.COLOR_CHANGE > 255:
                new_color.append(channel - self.COLOR_CHANGE)
            else:
                new_color.append(channel + self.COLOR_CHANGE)
        return new_color


class Pane(Label):
    """Container widget that allows selecting and acts as an image for a number of widgets. Changes on the pane are
    handled on widget level as far as possible"""
    widgets: List[Widget]

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        **kwargs
    ):
        Label.__init__(self, size, selectable=False, **kwargs)
        self.widgets = []

    def add_widget(
        self,
        pos: Union[Tuple[Union[int, str], Union[str, int]], List[Union[int, str]]],
        widget: Widget,
        add_topleft: bool = False
    ) -> None:
        """
        Add a widget at the provided position
        """
        rect = widget.rect
        pos = WidgetPosition(pos, rect, self.rect)
        # create the position relative to the rect of this Pane
        if add_topleft:
            pos = (rect.left + pos[0], rect.top + pos[1])
        widget.rect = pygame.Rect((pos[0], pos[1], rect.width, rect.height))
        widget.board_position = [self.board_position[0] + pos[0], self.board_position[1] + pos[1]]
        self.widgets.append(widget)
        self.orig_surface.blit(widget.surface, pos)
        self.surface = self.orig_surface.copy()

    def wupdate(self, *args) -> None:
        """Update all the widgets in this container based on the changed_image attribute"""
        for widget in self.widgets:
            widget.wupdate()
            if widget.changed_image:
                self.__redraw_widget(widget)
                widget.changed_image = False

    def move(self, offset: Union[Tuple[int, int], List[int]]) -> None:
        super().move(offset)
        for widget in self.widgets:
            widget.move(offset)

    def _find_hovered_widgets(
        self,
        pos: Union[Tuple[int, int], List[int]]
    ) -> Tuple[List[Widget], List[Widget]]:
        """Recursively traverse all containers this pane and subsequent panes to find all hovered and unhovered
         widgets"""
        hovered_widgets = []
        unhovered_widgets = []
        adjusted_pos = (pos[0] - self.rect.left, pos[1] - self.rect.top)
        adjusted_own_rect = pygame.Rect((0, 0, self.rect.width, self.rect.height))
        for widget in self.widgets:
            collide = widget.rect.collidepoint(adjusted_pos) and adjusted_own_rect.collidepoint(adjusted_pos)
            if collide:
                hovered_widgets.append(widget)
            else:
                unhovered_widgets.append(widget)
            if isinstance(widget, Pane):
                lower_selected, lower_unselected = widget._find_hovered_widgets(adjusted_pos)
                hovered_widgets.extend(lower_selected)
                unhovered_widgets.extend(lower_unselected)
        return hovered_widgets, unhovered_widgets

    def _get_selectable_widgets(self):
        """Recursively find all widgets that are have attribute selectable True"""
        selectable_widgets = []
        for widget in self.widgets:
            if widget.selectable:
                selectable_widgets.append(widget)
            elif isinstance(widget, Pane):
                selectable_widgets.extend(widget._get_selectable_widgets())
        return selectable_widgets

    def __redraw_widget(
        self,
        widget: Widget
    ) -> None:
        """Method that redraws a widget in this container. No check is performed"""
        self.orig_surface.blit(widget.surface, dest=widget.rect,
                               area=pygame.Rect((0, 0, widget.rect.width, widget.rect.height)))
        self.surface = self.orig_surface.copy()
        self.changed_image = True

    def add_border(
        self,
        widget: Widget,
        color: Union[Tuple[int, int, int], List[int]] = (0, 0, 0)
    ) -> None:
        """add a border around a specified widget. The widget should be in the pane"""
        rect = widget.rect.inflate(4, 4)
        pygame.draw.rect(self.orig_surface, color, rect, 3)
        self.surface = self.orig_surface.copy()


class SelectionList(Pane):
    __FONT_SIZE = 20
    __FONT = con.FONTS[__FONT_SIZE]
    LINE_HEIGHT = __FONT.size("T")[1] + 10
    __EXPAND_BUTTON_IMAGE: ClassVar[List[image_handling.ImageDefinition]] = \
        image_handling.ImageDefinition("general", (70, 10), image_size=util.Size(LINE_HEIGHT, LINE_HEIGHT))
    __EXPAND_BUTTON_HOVER_IMAGE: ClassVar[List[image_handling.ImageDefinition]] = \
        image_handling.ImageDefinition("general", (80, 10), image_size=util.Size(LINE_HEIGHT, LINE_HEIGHT))

    __expanded_options_frame: Union[None, "Frame"]
    __show_label: Union[None, Label]

    def __init__(
        self,
        sprite_group,
        options: List[str] = None,
        **kwargs
    ):
        self.__options = options if options else ["<placeholder>"]
        size = self.__get_size()
        super().__init__(size, **kwargs)
        self.__show_label = None
        self.__expand_button = None
        self.__expanded_options = False
        self.__expanded_options_frame = None
        self.__options_selection_group = SelectionGroup()
        self.__init_widgets(sprite_group)

    def __get_size(self) -> util.Size:
        longest_line = str(max(self.__options, key=lambda x: self.__FONT.size(x)[0]))
        size = util.Size(*self.__FONT.size(longest_line))
        # add extra space for the button
        size.height += 10
        size.width += size.height + 10
        return size

    def __init_widgets(
        self,
        sprite_group: pygame.sprite.AbstractGroup
    ) -> None:
        line_width = self.rect.width - self.rect.height
        line_height = self.LINE_HEIGHT
        self.__show_label = Label((line_width, line_height), self.color, border=True, text=self.__options[0],
                                  font_size=self.__FONT_SIZE, selectable=False)
        self.add_widget((0, 0), self.__show_label)
        self.__expand_button = Button((line_height, line_height), image=self.__EXPAND_BUTTON_IMAGE.images()[0],
                                      hover_image=self.__EXPAND_BUTTON_HOVER_IMAGE.images()[0], border=True)
        self.__expand_button.add_key_event_listener(1, self.__show_expanded_options, types=["unpressed"])
        self.add_widget((line_width, 0), self.__expand_button)

        # position is determined when the frame is opened
        self.__expanded_options_frame = Frame((0, 0), (line_width, line_height * len(self.__options)),
                                              sprite_group, visible=False, color=self.color, static=False)
        for index, option_text in enumerate(self.__options):
            option_label = Label((line_width, line_height), text=option_text, font_size=self.__FONT_SIZE, border=True,
                                 border_width=2, border_shrink=(4, 4), color=self.color)
            if index == 0:
                option_label.set_selected(True)
            self.__options_selection_group.add(option_label)
            option_label.add_key_event_listener(1, self.__select_expanded_option, values=[option_label],
                                                types=["unpressed"])
            self.__expanded_options_frame.add_widget((0, index * line_height), option_label)
        # make sure that events are captured that could cover the frame containing the options
        self.rect.height += self.__expanded_options_frame.rect.height

    def select_option(self, option_str: str) -> None:
        # these only contain labels
        for label in self.__expanded_options_frame.widgets:
            label: Label
            if label.get_text() == option_str:
                self.__select_expanded_option(label)
                break

    def __select_expanded_option(
        self,
        widget: Label
    ):
        self.__expanded_options = False
        self.__options_selection_group.select(widget)
        self.__expanded_options_frame.show(self.__expanded_options)
        self.__show_label.set_text(widget.get_text(), ("center", "center"), font_size=self.__FONT_SIZE)

    def __show_expanded_options(self):
        self.__expanded_options = not self.__expanded_options
        self.__expanded_options_frame.rect.topleft = (self.board_position[0],
                                                      self.board_position[1] + self.__show_label.rect.height)

        self.__expanded_options_frame.show(self.__expanded_options)

    def handle_events(
        self,
        events: List,
        type_: str = None,
        consume_events: bool = True
    ) -> List[pygame.event.Event]:
        leftover_events = super().handle_events(events, type_=type_, consume_events=consume_events)
        if self.__expanded_options:
            if type_ == "mouse":
                leftover_events = self.__expanded_options_frame.handle_mouse_events(leftover_events,
                                                                                    consume_events=consume_events)
            elif type_ == "other":
                leftover_events = self.__expanded_options_frame.handle_other_events(leftover_events,
                                                                                    consume_events=consume_events)
        return leftover_events


class Frame(entities.ZoomableEntity, Pane):
    """Pane that belongs to a sprite group thus it is drawn whenever it is visible"""
    selected_widget: Union[None, Widget]
    __select_top_widget_flag: bool

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        size: Union[util.Size, Tuple[int, int], List[int]],
        *groups: pygame.sprite.AbstractGroup,
        **kwargs
    ):
        Pane.__init__(self, size, board_pos=pos, **kwargs)
        entities.ZoomableEntity.__init__(self, pos, size, *groups, **kwargs)
        self.selected_widget = None
        self.__select_top_widget_flag = False
        self.__previous_board_pos = self.board_position
        # frame events are not consumed when triggered
        self.add_key_event_listener(con.K_UP, self.__select_next_widget, values=[con.K_UP], types=["pressed"])
        self.add_key_event_listener(con.K_DOWN, self.__select_next_widget, values=[con.K_DOWN], types=["pressed"])
        self.add_key_event_listener(con.K_LEFT, self.__select_next_widget, values=[con.K_LEFT], types=["pressed"])
        self.add_key_event_listener(con.K_RIGHT, self.__select_next_widget, values=[con.K_RIGHT], types=["pressed"])
        self.add_key_event_listener(con.K_RETURN, self.__activate_selected_widget, types=["pressed"])
        self.add_key_event_listener(1, self.__select_top_widget, types=["unpressed"])

    def update(self, *args):
        """Call pane wupdate method in order to update relevant widgets """
        super().update(*args)
        if self.is_showing() and self.__previous_board_pos != self.rect.topleft:
            self.move([self.__previous_board_pos[0] - self.rect.left, self.__previous_board_pos[1] - self.rect.top])
            self.__previous_board_pos = self.rect.topleft
        self.wupdate(*args)

    def __select_top_widget(self):
        self.__select_top_widget_flag = True

    def set_zoom(
        self,
        zoom: float
    ) -> None:
        self._zoom = zoom

    @property
    def rect(self):
        """Returns a rectangle that represents the zoomed version of the self.orig_rect"""
        if self._zoom == 1 or not self.static:
            return self.orig_rect
        width, height = self.orig_rect.size
        orig_pos = list(self.orig_rect.center)
        orig_pos[0] = round(orig_pos[0] * self._zoom + 0.5 * (width - width * self._zoom))
        orig_pos[1] = round(orig_pos[1] * self._zoom + 0.5 * (height - height * self._zoom))
        rect = self.surface.get_rect(center=orig_pos)
        return rect

    @rect.setter
    def rect(
        self,
        rect: pygame.Rect
    ) -> None:
        self.orig_rect = rect

    def __select_next_widget(
        self,
        direction: int
    ) -> None:
        """Find the widget that is closest in the correct direction of all the selectable widgets to select that
        widget instead"""
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
        # moving up or down
        if direction == con.K_UP or direction == con.K_DOWN:
            # make sure widgets are partially overlapping in the x-direction
            elligable_widgets = \
                [w for w in selectable_widgets if s_rect.left <= w.rect.left <= s_rect.right or
                 s_rect.right >= w.rect.right >= s_rect.left]
            if direction == con.K_UP:
                elligable_widgets_above = [w for w in elligable_widgets if w.rect.centery < s_rect.centery]
                if len(elligable_widgets_above) > 0:
                    # select the closest above the current
                    self.selected_widget = sorted(elligable_widgets_above,
                                                  key=lambda x: s_rect.centery - x.rect.centery)[0]
            else:
                elligable_widgets_below = [w for w in elligable_widgets if w.rect.centery > s_rect.centery]
                if len(elligable_widgets_below) > 0:
                    # select the closest bewow the current
                    self.selected_widget = sorted(elligable_widgets_below,
                                                  key=lambda x: x.rect.centery - s_rect.centery)[0]
        # moving left or right
        if direction == con.K_LEFT or direction == con.K_RIGHT:
            # make sure widgets are partially overlapping in the x-direction
            elligable_widgets = \
                [w for w in selectable_widgets if s_rect.top <= w.rect.top <= s_rect.bottom or
                 s_rect.bottom >= w.rect.bottom >= s_rect.top]
            if direction == con.K_LEFT:
                elligable_widgets_west = [w for w in elligable_widgets if w.rect.centerx < s_rect.centerx]
                if len(elligable_widgets_west) > 0:
                    # select the closest above the current
                    self.selected_widget = sorted(elligable_widgets_west,
                                                  key=lambda x: s_rect.centerx - x.rect.centerx)[0]
            else:
                elligable_widgets_east = [w for w in elligable_widgets if w.rect.centerx > s_rect.centerx]
                if len(elligable_widgets_east) > 0:
                    # select the closest bewow the current
                    self.selected_widget = sorted(elligable_widgets_east,
                                                  key=lambda x: x.rect.centerx - s_rect.centerx)[0]
        self.selected_widget.set_selected(True)

    def __activate_selected_widget(self) -> None:
        """perform the action bound to a widget on mouse-1"""
        if self.selected_widget is not None:
            self.selected_widget.action(event_handlers.Key(1), "unpressed")

    def handle_mouse_events(
            self,
            events: List[pygame.event.Event],
            consume_events: bool = True
    ):
        # events that are triggered on this frame widget trigger first
        leftover_events = self.handle_events(events, type_="mouse", consume_events=False)
        pos = pygame.mouse.get_pos()
        if self.static:
            # the group 0 is always a CameraAwareLayerUpdates spritegroup
            # noinspection PyUnresolvedReferences
            pos = interface_util.screen_to_board_coordinate(pos, self.groups()[0].target, 1)
        hovered, unhovered = self._find_hovered_widgets(pos)
        # add a hover event that can be consumed in the same way as normal events.
        leftover_events.append(pygame.event.Event(con.HOVER, button=con.BTN_HOVER))
        # handle all events from the most front widget to the most back one. --> this should be mouse events
        if hovered is not None:
            while len(hovered) > 0 and len(leftover_events) > 0:
                widget = hovered.pop()
                if self.__select_top_widget_flag is True and widget.selectable:
                    self.__select_top_widget_flag = False
                    if self.selected_widget:
                        self.selected_widget.set_selected(False)
                    self.selected_widget = widget
                    self.selected_widget.set_selected(True)
                leftover_events = widget.handle_events(leftover_events, type_="mouse", consume_events=consume_events)
        # make sure the flag is false at the end
        self.__select_top_widget_flag = False
        # trigger an unhover event for all widgets not hovered
        unhover_event = [pygame.event.Event(con.UNHOVER, button=con.BTN_HOVER)]
        for widget in unhovered:
            widget.handle_events(unhover_event, type_="mouse")
        return leftover_events

    def handle_other_events(
            self,
            events: List[pygame.event.Event],
            consume_events: bool = True
    ):
        """Handle all events but key events for the widget that is selected"""
        leftover_events = self.handle_events(events, type_="other", consume_events=consume_events)

        if self.selected_widget:
            leftover_events = self.selected_widget.handle_events(leftover_events, type_="other",
                                                                 consume_events=consume_events)
        return leftover_events


class Tooltip(entities.Entity):
    """Strict frame containing one or more labels with text"""
    # the extra area around the text to make the tooltip feel less cramped
    __EXTRA_SIZE: ClassVar[Tuple[int, int]] = (10, 10)

    font: pygame.font.Font
    lines: List[str]
    __showing_tooltip: bool

    def __init__(
        self,
        sprite_group: pygame.sprite.AbstractGroup,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List[int]] = (150, 150, 150),
        text: str = "",
        font_size: int = 15
    ):
        self.font = con.FONTS[font_size]
        self.lines = text.split("\n")
        size = self.__get_size()
        # the position is not important because it will be changed when shown
        super().__init__((0, 0), size, sprite_group, color=color, visible=False, layer=con.TOOLTIP_LAYER, static=False)
        self.__showing_tooltip = False

    def __get_size(self) -> util.Size:
        longest_line = str(max(self.lines, key=lambda x: self.font.size(x)[0]))
        size = util.Size(*self.font.size(longest_line))
        size.height *= len(self.lines)
        size += self.__EXTRA_SIZE
        return size

    def _create_surface(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List[int]],
        **kwargs
    ):
        """Add the lines and a border to the default rendered """
        surface = super()._create_surface(size, color, **kwargs)
        line_height = size[1] / len(self.lines)
        for index, line in enumerate(self.lines):
            rendereded_line = self.font.render(line, True, (0, 0, 0))
            pos = [self.__EXTRA_SIZE[0] / 2, line_height * index]
            if index == 0:
                pos[1] += self.__EXTRA_SIZE[1] / 2
            surface.blit(rendereded_line, pos)
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 3)
        return surface

    def is_showing(self) -> bool:
        return super().is_showing() and self.__showing_tooltip

    def show_tooltip(
        self,
        value: bool
    ) -> None:
        self.show(value)
        self.__showing_tooltip = value
        if value:
            mouse_pos = pygame.mouse.get_pos()
            self.rect.topleft = mouse_pos


class ScrollPane(Pane):
    """
    A Pane that can be scrolled
    """
    SCROLL_SPEED: ClassVar[int] = 20  # pixels
    # space between the outside of the crafting window and the closest label
    BORDER_SPACE: ClassVar[int] = 3  # pixels

    __next_widget_topleft: Union[Tuple[int, int], List[int]]
    __total_rect: pygame.Rect
    __total_offset: int

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        **kwargs
    ):
        super().__init__(size, **kwargs)
        self.__next_widget_topleft = [self.BORDER_SPACE, self.BORDER_SPACE]
        # the rectangle of the surface, can be bigger then the rect that displays the information
        self.__total_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)

        # can only be negative
        self.__total_offset_y = 0

        self.add_key_event_listener(4, self.scroll_y, [self.SCROLL_SPEED])
        self.add_key_event_listener(5, self.scroll_y, [-self.SCROLL_SPEED])

    def add_widget(
            self,
            widget: Widget,
    ) -> None:
        # configure the position of the next
        if len(self.widgets) > 0:
            # when the widget does not fit on the current line go a line down
            if self.widgets[-1].rect.right + widget.rect.width + self.BORDER_SPACE > self.__total_rect.width:
                # when the total rect is to small extend it.
                if self.widgets[-1].rect.bottom + widget.rect.height + self.BORDER_SPACE > self.__total_rect.height:
                    extra_room = (self.widgets[-1].rect.bottom + widget.rect.height + self.BORDER_SPACE) - \
                                 self.__total_rect.height
                    self.__extend_scroll_image(extra_room)
                self.__next_widget_topleft = [self.BORDER_SPACE, self.widgets[-1].rect.bottom]
            else:
                self.__next_widget_topleft = self.widgets[-1].rect.topright
        self.widgets.append(widget)
        widget.rect.topleft = self.__next_widget_topleft
        self.orig_surface.blit(widget.surface, widget.rect)

    def scroll_y(
        self,
        offset_y: int
    ) -> None:
        """Scroll the main image of the pane"""
        # for cases with negative offset
        if self.__total_rect.height - self.rect.height + offset_y + self.__total_offset_y < 0:
            # both offsets are negative at this point
            offset_y = - self.SCROLL_SPEED - (self.__total_rect.height - self.rect.height + offset_y +
                                              self.__total_offset_y)
        # for cases with positive offset
        elif self.__total_offset_y + offset_y > 0:
            offset_y -= self.__total_offset_y + offset_y
        self.__total_offset_y += offset_y
        self.orig_surface.fill(self.color)
        self.orig_surface.scroll(0, offset_y)

        # make sure the location of the widgets contained is moved accordingly
        for widget in self.widgets:
            widget.rect.move_ip(0, offset_y)
            widget.changed_image = True

    def __extend_scroll_image(
        self,
        amnt: int
    ) -> None:
        """Extend the current orig_surface and total_rect to hold more image"""
        self.__total_rect.height += amnt
        orig_copy = self.orig_surface.copy()
        self.orig_surface = pygame.Surface(self.__total_rect.size).convert()
        self.orig_surface.fill(self.color)
        self.orig_surface.blit(orig_copy, (0, self.__total_offset_y))


class ItemDisplay(Label):

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        item: Union[None, "inventories.Item"] = None,
        border: bool = True,
        border_shrink: Union[Tuple[int, int], List[int]] = (3, 3),
        **kwargs
    ):
        super().__init__(size, border=border, border_shrink=border_shrink, **kwargs)
        self.item = item
        self.previous_total = 0
        if self.item:
            self.add_item(item)

    def add_item(
        self,
        item: "inventories.Item"
    ) -> None:
        """Add or change the item displayed"""
        self.item = item
        self.__add_item_image()
        self.__add_quantity_text()
        self.changed_image = True

    def __add_item_image(self) -> None:
        """Add the image of the item in the correct size"""
        item_size = util.Size(*self.rect.size) - (12, 12)
        item_image = self.item.material.full_surface
        item_image = pygame.transform.scale(item_image, item_size)
        self.set_image(item_image)

    def __add_quantity_text(self) -> None:
        """Add the quantity text"""
        self.previous_total = self.item.quantity
        self.set_text(str(self.previous_total), (5, 5), color=self.item.TEXT_COLOR)

    def wupdate(self):
        """Make sure to update the amount whenever it changes"""
        super().wupdate()
        if self.item is not None and self.previous_total != self.item.quantity:
            self.__add_quantity_text()


# class TextBox(ScrollPane):
#     INNITIAL_KEY_REPEAT_SPEED = 180
#     KEY_REPEAT_SPEED = 15
#
#     def __init__(self, size, **kwargs):
#         super().__init__(size, **kwargs)
#         self.text_log = TextLog()
#         self.current_line = Line()
#         self.blinker_speed = 500
#         self.blinker_visible = [True, self.blinker_speed]
#         self.processed = True
#         self.process_line = self.current_line
#         self.command_tree = None
#         # innitial, actual
#         self.key_repeat_speed = [0, 0]
#
#     def wupdate(self, *args):
#         super().wupdate(*args)
#         self.blinker_visible[1] -= con.GAME_TIME.get_time()
#         if self.blinker_visible[1] <= 0:
#             self.blinker_visible = [not self.blinker_visible[0], self.blinker_speed]
#         for event in self.events:
#             if event.type == KEYDOWN:
#                 self.pressed_keys[event.key] = True
#                 if len(event.unicode) == 1:
#                     self.active_key = event.unicode
#                 self.key_repeat_speed = [self.INNITIAL_KEY_REPEAT_SPEED, 0]
#             if event.type == KEYUP:
#                 unpressed_char = self.pressed_keys[event.key]
#                 self.active_key = None
#                 self.pressed_keys[event.key] = False
#         if self.key_repeat_speed[1] <= 0:
#             self.key_repeat_speed[1] = self.KEY_REPEAT_SPEED
#             if self.pressed_keys[K_BACKSPACE]:
#                 if len(self.current_line) > 0:
#                     self.current_line.delete()
#             elif self.pressed_keys[K_RETURN]:
#                 self.text_log.append(self.current_line)
#                 self.process_line = self.current_line
#                 self.processed = False
#                 self.current_line = Line()
#                 self.text_log.location = 0
#             elif self.pressed_keys[K_UP]:
#                 self.current_line = self.text_log.line_up()
#             elif self.pressed_keys[K_DOWN]:
#                 self.current_line = self.text_log.line_down()
#             elif self.pressed_keys[K_LEFT]:
#                 self.current_line - 1
#             elif self.pressed_keys[K_RIGHT]:
#                 self.current_line + 1
#             elif self.pressed_keys[K_TAB]:
#                 self.__create_tab_information()
#             else:
#                 if self.active_key:
#                     self.current_line.append(self.active_key)
#         else:
#             if self.key_repeat_speed[0] > 0:
#                 self.key_repeat_speed[0] -= con.GAME_TIME.get_time()
#             elif self.key_repeat_speed[1] > 0:
#                 self.key_repeat_speed[1] -= con.GAME_TIME.get_time()
#
#     def _get_image(self):
#         image = super()._get_image()
#         text = self.current_line.render_str(blinker = self.blinker_visible[0], header = ">:")
#         image.blit(text, (10, self.rect.height - text.get_size()[1]))
#         prev_line_heigth = text.get_size()[1]
#         for i, line in enumerate(iter(self.text_log)):
#             if self.rect.height - prev_line_heigth < 0:
#                 break
#             text = line.render_str()
#             prev_line_heigth += text.get_size()[1]
#             image.blit(text, (10, self.rect.height - prev_line_heigth))
#         return image.convert()
#
#     def add_error_message(self, text):
#         message = "ERROR: "
#         self.text_log.append_um(Line(text = message + text, color = (163, 28, 23)))
#
#     def add_conformation_message(self, text):
#         self.text_log.append_um(Line(text = text, color = (25, 118, 168)))


class TextLine(Label):
    __BLINKER_SPEED = 500

    def __init__(self, width, text="", text_font=20, text_color=(0, 0, 0), **kwargs):
        self.__text_font = text_font
        self.__font = con.FONTS[text_font]
        self.__text_color = text_color
        size = (width, self.__font.size("T")[1] + 10)
        super().__init__(size, color=(100, 100, 100), **kwargs, recordable_keys=con.KEY_KEYS)

        self.text = text
        self.__blinker_timer = 0
        self.__blinker_active = False
        self.line_location = len(self.text)

    def wupdate(self):
        super().wupdate()
        self.__blinker_timer += con.GAME_TIME.get_time()
        if self.__blinker_timer > self.__BLINKER_SPEED:
            self.__blinker_timer = 0
            self.__blinker_active = not self.__blinker_active

    def action(
        self,
        key: event_handlers.Key,
        _type: str
    ) -> Any:
        self.add_letter()

    def add_letter(self, key):
        print(pygame.key.name(key))

    def render(self, blinker=False, header=""):
        if blinker:
            text = "{}{}|{}".format(header, self.text[:self.line_location], self.text[self.line_location:])
        else:
            text = "{}{}".format(header, self.text)
        self.set_text(text, (0, "C"), self.__text_color, self.__text_font)

    def move_line_location(self, value):
        if value > 0 and self.line_location + value <= len(self.text):
            self.line_location += value
        elif value < 0 and self.line_location + value >= 0:
            self.line_location += value

    def append(self, value):
        self.text = self.text[:self.line_location] + value + self.text[self.line_location:]
        self.line_location += len(value)

    def delete(self):
        if self.line_location > 0:
            self.line_location -= 1
            self.text = self.text[:self.line_location] + self.text[self.line_location + 1:]
