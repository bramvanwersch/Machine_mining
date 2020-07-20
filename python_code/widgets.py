import pygame
from abc import ABC, abstractmethod

from python_code.entities import Entity
from python_code.constants import *
from python_code.event_handling import EventHandler


class Widget(ABC):
    SELECTED_COLOR = (0,0,0)
    def __init__(self, pos,  size, color = (255,255,255), **kwargs):
        self.action_functions = {}
        self.selectable = False
        self.selected = False

        self.image = self._create_image(size, color, **kwargs)
        self.orig_image = self.image
        self.rect = self.image.get_rect(topleft=pos)
        self.visible = True
        self.changed_image = False

    def update(self):
        return None

    def _create_image(self, size, color, **kwargs):
        """
        Create an image using a size and color

        :param size: a Size object or tuple of lenght 2
        :param color: a rgb color as tuple of lenght 2 or 3
        :param kwargs: additional named arguments
        :return: a pygame Surface object
        """
        if len(color) == 3:
            image = pygame.Surface(size).convert()
        # included alpha channel
        elif len(color) == 4:
            image = pygame.Surface(size).convert_alpha()
        image.fill(color)
        return image

    def action(self, e):
        """
        You can define a set of action functions linked to keys these are then executed when the widget is selected. If
        it is marked with SELECTION the action function is activated upon selection
        :param e: a list of events that passed the menu pane loop
        """
        if "SELECTION" in self.action_functions:
            self.action_functions["SELECTION"]()
        for event in e:
            if event.type in self.action_functions:
                self.action_functions[event.type]()
            if event.type == KEYDOWN:
                if event.key in self.action_functions:
                    self.action_functions[event.key]()

    def set_action(self, action_function, key):
        """
        Bind a function to a key that is called when the widget is selected. There is an optional keyword SELECTION that
        makes sure that the function is called upon selection and each frame after while the widget is selected
        :param action_function: a function defenition
        :param key: a key typically an integer representing a key as defined in pygame.locals
        """
        self.action_functions[key] = action_function

    def set_selected(self, selected):
        self.selected = selected
        if self.selected:
            pygame.draw.rect(self.image, self.image.get_rect(), self.SELECTED_COLOR)
            self.image = self.selected_image
        else:
            self.image = self.orig_image
        self.changed_image = True

    def set_image(self, image):
        if image == None:
            self.image = orig_imaage
        else:
            self.image = image
        self.changed_image = True


class Frame(Entity, EventHandler):
    TEXTCOLOR = (0,0,0)
    def __init__(self, pos, size, *groups, title=None, **kwargs):
        """
        Creates a MenuPane that holds othger widgets and regulated selection of the widgets in the pane itself.
        :param rect: size of the pane
        :param image: image to be displayed on the pane
        :param groups: sprite group for this widget and widgets in this widget to be added to
        :param title: optional title
        """
        EventHandler.__init__(self, [K_UP, K_w, K_s, K_DOWN])
        Entity.__init__(self, pos, size, *groups, **kwargs)
        self.widgets = []
        # index of selected widget in the widgets list
        self.selectable_widgets = []
        self.selected_widget = 0

        if title:
            self._set_title(title)

    def _set_title(self, title):
        title = FONT30.render(title, True, self.TEXTCOLOR)
        tr = title.get_rect()
        #center the title above the widet
        self.image.blit(title, (int(0.5 * self.rect.width - 0.5 * tr.width), 10))

    def update(self, *args):
        Entity.update(self, *args)
        for widget in self.widgets:
            widget.update()
            if widget.changed_image:
                self.__redraw_widget(widget)
                widget.changed_image = False

    def handle_events(self, events):
        events = super().handle_events(events)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                for widget in self.widgets:
                    if widget.rect.collidepoint(x, y):
                        widget.action([event])
                        break;
            if self._pressed_keys[K_UP] or self._pressed_keys[K_w]:
                self._change_selected_widget()
            elif self._pressed_keys[K_DOWN] or self._pressed_keys[K_s]:
                self._change_selected_widget(False)
            else:
                selected_widget_events.append(event)
        if self.selectable_widgets:
            self.widgets[self.selected_widget].action(selected_widget_events)


    def _change_selected_widget(self, up=True):
        if not self.selectable_widgets: return
        self.selectable_widgets[self.selected_widget].set_selected(False)
        if up:
            if self.selected_widget <= 0:
                self.selected_widget = len(self.widgets) - 1
            else:
                self.selected_widget -= 1
        else:
            if self.selected_widget >= len(self.widgets) - 1:
                self.selected_widget = 0
            else:
                self.selected_widget += 1
        self.selectable_widgets[self.selected_widget].set_selected(True)

    def __redraw_widget(self, widget):
        self.orig_image.blit(widget.image, widget.rect)

    def add_widget(self, widget):
        self.widgets.append(widget)
        self.orig_image.blit(widget.image, widget.rect)
        if widget.selectable:
            self.selectable_widgets.append(widget)
            self.selectable_widgets.sort(key=lambda x: x.rect.y)

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


class Label(Widget):
    def __init__(self, pos, size, **kwargs):
        Widget.__init__(self,pos, size, **kwargs)


class SelectableLabel(Label):
    def __init__(self, image, size):
        """
        Extension of the label class that
        :param image:
        :param size:
        """
        Label.__init__(self, size)
        self.selectable = True


# methods for images that have a set location but change theire appearance over time.
# pretty much a chiller sprite
class DynamicSurface:
    def __init__(self, rect, background_color=(165, 103, 10), **kwargs):
        self.font18 = pygame.font.Font(
            constants.DATA_DIR + "//Menu//font//manaspc.ttf", 18)
        self.rect = rect
        self.background_color = background_color
        self.image = None

    def update(self):
        self.image = self._get_image()

    def _get_image(self):
        image = pygame.Surface((self.rect.size))
        image.fill(self.background_color)
        return image


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
