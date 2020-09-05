import pygame
from python_code.utility.event_handling import EventHandler
from python_code.utility.utilities import Size
from python_code.utility.constants import KEYDOWN
from python_code.interfaces.widgets import Frame, Label, Button
from python_code.utility.image_handling import image_sheets

class Window(Frame, EventHandler):
    TOP_SIZE = Size(0, 25)
    EXIT_BUTTON_SIZE = Size(25, 25)
    COLOR = (173, 94, 29, 150)
    TOP_BAR_COLOR = (195, 195, 195)
    TEXT_COLOR = (0,0,0)

    def __init__(self, pos, size, *groups, color=COLOR, title=None, **kwargs):
        EventHandler.__init__(self, [])
        Frame.__init__(self, pos, size + self.TOP_SIZE, *groups, color=color, **kwargs)
        self.static = False
        self.visible = False
        self.__add_top_border(size, title)

    def __add_top_border(self, size, title):
        top_label = Label((0,0), Size(size.width - self.EXIT_BUTTON_SIZE.width, self.TOP_SIZE.height), color=self.TOP_BAR_COLOR)
        self.add_widget(top_label)
        if title != None:
            top_label.set_text(title, (10,5), self.TEXT_COLOR, font_size=25, add=True)
        button_image = image_sheets["general"].image_at((20,0),self.EXIT_BUTTON_SIZE)
        exit_button = Button((size.width - self.EXIT_BUTTON_SIZE.width, 0), self.EXIT_BUTTON_SIZE, image=button_image)
        exit_button.set_action(1, self.__close_window)
        self.add_widget(exit_button)

    def _set_title(self, title):
        """
        Permanently add a title to the frame. This is displayed at the top of
        the frame

        :param title: String of what should be displayed
        """
        title = FONTS[15].render(title, True, self.TEXTCOLOR)
        tr = title.get_rect()
        #center the title above the widet
        self.orig_image.blit(title, (int(0.5 * self.rect.width - 0.5 * tr.width), 10))

    def __close_window(self):
        """
        Press the escape key to close the window
        """
        newevent = pygame.event.Event(KEYDOWN, unicode="^[",
                                      key=pygame.locals.K_b,
                                      mod=pygame.locals.KMOD_NONE)  # create the event
        pygame.event.post(newevent)

    def show(self, value: bool):
        """
        Toggle showing the crafting window or not. This also makes sure that no
        real updates are pushed while the window is invisible

        :param value: a boolean
        """
        self.visible = value

    def handle_events(self, events):
        """
        Handle events issued by the user not consumed by the Main module. This
        function can also be used as an update method for all things that only
        need updates with new inputs.

        Note: this will trager quite often considering that moving the mouse is
        also considered an event.

        :param events: a list of events
        """
        if self.visible:
            leftovers = super().handle_events(events)
