import pygame
from abc import ABC, abstractmethod

from python_code.entities import Entity
from python_code.constants import *
from python_code.event_handling import EventHandler


class Widget(ABC):
    def __init__(self, pos, size, selectable = False, **kwargs):
        self.action_functions = {}
        self.selectable = selectable
        self.selected = False

        self.rect = pygame.Rect((*pos, *size))
        self.visible = True

    def wupdate(self):
        return None

    def action(self, e):
        for event in e:
            if event.type == MOUSEBUTTONDOWN:
                self.action_functions[event.button]()
            if event.type == KEYDOWN:
                if event.key in self.action_functions:
                    self.action_functions[event.key]()

    def set_action(self, action_function, key):
        self.action_functions[key] = action_function

    def set_selected(self, selected):
        self.selected = selected

class Label(Widget):
    """
    Bsically a widget that allows image manipulation
    """
    SELECTED_COLOR = (0,0,0)
    def __init__(self, pos, size, color = (255,255,255), **kwargs):
        Widget.__init__(self,pos, size, **kwargs)
        self.image = self._create_image(size, color, **kwargs)
        self.orig_image = self.image
        self.changed_image = False

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

    def set_selected(self, selected):
        super().set_selected(selected)
        if self.selected:
            pygame.draw.rect(self.image, self.image.get_rect(), self.SELECTED_COLOR)
            self.image = self.selected_image
        else:
            self.image = self.orig_image
        self.changed_image = True

    def set_image(self, image):
        if image == None:
            self.image = self.orig_image
        else:
            self.image = image
        self.changed_image = True

    def set_text(self, text, font_size = 22):
        s = FONT22.render(str(text), True, (0,0,0))
        self.image.blit(s, self.rect)


class Pane(Label, EventHandler):
    """
    Container widget that allows selecting and acts as an image for a number
    of widgets
    """
    def __init__(self, pos, size, **kwargs):
        Label.__init__(self, pos, size, **kwargs)
        EventHandler.__init__(self, "ALL")
        self.widgets = []


    def wupdate(self, *args):
        for widget in self.widgets:
            widget.wupdate()
            if widget.changed_image:
                self.__redraw_widget(widget)
                widget.changed_image = False

    def handle_events(self, events):
        super().handle_events(events)


    def __redraw_widget(self, widget):
        self.orig_image.blit(widget.image, widget.rect)

    def add_widget(self, widget):
        self.widgets.append(widget)
        self.orig_image.blit(widget.image, widget.rect)


class Frame(Entity, Pane):
    """
    Container for widgets, that is an entity so it can act as a window. Every
    gui should have a frame to be able to display and handle updates
    """
    TEXTCOLOR = (0,0,0)
    def __init__(self, pos, size, *groups, title=None, **kwargs):
        """
        Creates a MenuPane that holds othger widgets and regulated selection of the widgets in the pane itself.
        :param rect: size of the pane
        :param image: image to be displayed on the pane
        :param groups: sprite group for this widget and widgets in this widget to be added to
        :param title: optional title
        """
        Entity.__init__(self, pos, size, *groups, **kwargs)
        Pane.__init__(self, pos, size, **kwargs)
        if title:
            self._set_title(title)

    def _set_title(self, title):
        title = FONT30.render(title, True, self.TEXTCOLOR)
        tr = title.get_rect()
        #center the title above the widet
        self.image.blit(title, (int(0.5 * self.rect.width - 0.5 * tr.width), 10))


class ScrollPane(Pane):
    def __init__(self, pos, size, total_size, **kwargs):
        super().__init__(pos, total_size, **kwargs)
        #the total rectangle
        self.total_rect = self.rect
        #the rect that is visible as the image
        self.rect = python.Rect((*pos, *size))





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
