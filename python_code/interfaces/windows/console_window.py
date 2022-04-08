#!/usr/bin/env python

import pygame
from typing import Union, Tuple, List, Dict, Any, TYPE_CHECKING

from interfaces.windows.base_window import Window
import utility.utilities as util
import utility.constants as con
from utility import console
import interfaces.widgets as widgets

if TYPE_CHECKING:
    from board.sprite_groups import CameraAwareLayeredUpdates
    from board.board import Board
    import user


class ConsoleWindow(Window):

    WINDOW_SIZE: util.Size = util.Size(con.SCREEN_SIZE.width, 0.6 * con.SCREEN_SIZE.height)
    WINDOW_POS: Union[Tuple[int, int], List] = (0, 0)

    __input_line: Union["ConsoleLine", None]
    __text_log_label: Union["TextLogLabel", None]
    __log: "TextLog"
    __console: console.Console

    def __init__(
        self,
        sprite_group: "CameraAwareLayeredUpdates",
        board: "Board",
        user_: "user.User"
    ):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, sprite_group, static=False, title="CONSOLE",
                         color=(150, 150, 150))
        self.__input_line = None
        self.__text_log_label = None
        self.__log = TextLog()
        self.__console = console.Console(board, user_)

        self.__init_widgets()
        self.add_key_event_listener(con.K_TAB, self.__create_tab_information, types=["pressed"])
        self.add_key_event_listener(con.K_UP, self.__set_log_line, values=[-1], types=["unpressed"])
        self.add_key_event_listener(con.K_DOWN, self.__set_log_line, values=[1], types=["unpressed"])

    def __set_log_line(
        self,
        direction: int
    ):
        if direction == 1:
            line = self.__log.line_down()
        elif direction == -1:
            line = self.__log.line_up()
        else:
            raise util.GameException(f"Invalid direction for retrieving Console line {direction}")
        self.__input_line.active_line.set_line_text(line.text)

    def run_starting_script(self):
        self.__console.process_command_line_text("scripts start")

    def __init_widgets(self):
        self.__input_line = ConsoleLine(self.WINDOW_SIZE.width - 10)
        self.add_widget((5, self.WINDOW_SIZE.height - self.__input_line.rect.height - 5), self.__input_line)
        self.add_border(self.__input_line, color=(50, 50, 50))

        self.__text_log_label = TextLogLabel(self.WINDOW_SIZE - (0, self.__input_line.rect.height + 10), self.__log)
        self.add_widget((0, 0), self.__text_log_label)

    def show_window(
        self,
        is_showing: bool
    ):
        super().show_window(is_showing)
        if is_showing is True:
            self.selected_widget = self.__input_line
            self.__input_line.set_selected(True)

    def update(
        self,
        *args: Any
    ):
        """Make sure to process the input line when one is presented when enter is pressed"""
        super().update()
        if self.__input_line.process_line is not None:
            self.add_executed_command_message(self.__input_line.process_line)
            results = self.__console.process_command_line_text(self.__input_line.process_line)
            for message, is_error in results:
                if is_error:
                    [self.add_error_message(m) for m in message.split("\n")]
                else:
                    [self.add_result_message(m) for m in message.split("\n")]
            self.__input_line.process_line = None

    def __create_tab_information(self):
        """Determine tab information that is relevant and append either a list of options or add the information that 
        is shared between all options e.g """
        # get all the text between the start and the cursor
        full_line = self.__input_line.active_line.text
        until_cursor_text = full_line[:self.__input_line.active_line.line_location]
        after_cursor_text = full_line[self.__input_line.active_line.line_location:]
        commands = self._get_commands_from_line(until_cursor_text)
        possible_commands_dict = self.__console.command_tree
        last_command = commands.pop(-1)
        count = 0
        # moving down the tree for all found commands
        while count < len(commands):
            command = commands[count]
            try:
                if type(possible_commands_dict[command]) == dict:
                    possible_commands_dict = possible_commands_dict[command]
                elif type(possible_commands_dict[command]) == str:
                    loop_loc = possible_commands_dict[command].split(" ")
                    possible_commands_dict = self.__console.command_tree
                    for loc in loop_loc:
                        possible_commands_dict = possible_commands_dict[loc]
                else:
                    return
            except KeyError:
                return
            count += 1
        if last_command == "":
            possible_commands = list(possible_commands_dict.keys())
        # if it ends on a perfect command simply add a space to the line
        elif last_command in possible_commands_dict.keys():
            self.__input_line.active_line.append(" ")
            return
        else:
            possible_commands = [key for key in possible_commands_dict.keys() if key.startswith(last_command)]
        if len(possible_commands) == 1:
            # if line ended on a space
            if len(last_command) == 0:
                self.__input_line.active_line.append(possible_commands[0])
            else:
                self.__input_line.active_line.set_line_text(until_cursor_text[:-len(last_command)]
                                                            + possible_commands[0] + after_cursor_text)
                self.__input_line.active_line.set_line_location(len(until_cursor_text) - len(last_command) +
                                                                len(possible_commands[0]))
        elif len(possible_commands) > 0:
            message = " ".join(possible_commands)
            self.add_tab_possibilities_message(message)
            lpc = str(max(possible_commands, key=len))
            letters = ""
            for letter in lpc:
                letters += letter
                if not all(c.startswith(letters) for c in possible_commands):
                    letters = letters[:-1]
                    break
            if not len(last_command) == 0:
                self.__input_line.active_line.set_line_text(until_cursor_text[:-len(last_command)] + letters +
                                                            after_cursor_text)
                self.__input_line.active_line.set_line_location(len(until_cursor_text) - len(last_command) +
                                                                len(letters))

    def _get_commands_from_line(
        self,
        current_line_text: str
    ) -> List[str]:
        word = ""
        commands = []
        list_multiplier = None
        for letter in current_line_text:
            if letter == " ":
                if word != "":
                    commands.append(word)
                word = ""
            elif letter == "[":
                if word != "":
                    commands.append(word)
                    list_multiplier = word
                elif len(commands) >= 1:
                    list_multiplier = commands[-1]
                word = ""
            elif letter == "]":
                word = ""
                if list_multiplier:
                    list_multiplier = commands[commands.index(list_multiplier) - 1]
                    commands = commands[:commands.index(list_multiplier) + 1]
            elif letter == ",":
                word = ""
                if list_multiplier:
                    commands = commands[:commands.index(list_multiplier) + 1]
                else:
                    commands = []
            else:
                word += letter
        commands.append(word)
        return commands

    def add_error_message(self, text):
        message = "ERROR: "
        self.__log.append_other(Line(text=message + text, color=(163, 28, 23)))

    def add_result_message(self, text):
        self.__log.append_other(Line(text=text, color=(25, 118, 168)))

    def add_tab_possibilities_message(self, text):
        self.__log.append_other(Line(text=text, color=(0, 0, 255), line_type="list"))

    def add_executed_command_message(self, text):
        """Print a command that was just executed in greenn"""
        self.__log.append(Line(text=text, color=(64, 235, 52)))


class ConsoleLine(widgets.MultilineTextBox):
    """The command line where the commands are typed"""

    process_line: Union[str, None]

    def __init__(
        self,
        width: int
    ):
        super().__init__(util.Size(width, con.FONTS[22].get_linesize() + 6), lines=1, font_size=22)
        self.add_key_event_listener(con.K_RETURN, action_function=self.handle_return, types=["pressed"])
        self.remove_key_event_listener(con.K_TAB)
        self.process_line = None

    def handle_return(self):
        self.process_line = self.active_line.text
        self.active_line.set_line_text("")


class TextLogLabel(widgets.Label):
    """The area above the command line containing the replies of the console"""
    # TODO use a scrollpane in order to better see the full history

    __log: "TextLog"

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        text_log: "TextLog",
        color: Union[Tuple[int, int, int], List[int]] = (150, 150, 150),
        **kwargs
    ):
        super().__init__(size, color=color, selectable=False, **kwargs)
        self.__log = text_log

    def wupdate(self):
        super().wupdate()
        if self.__log.changed:
            image = self.__create_log_image()
            self.set_image(image, (0, 0))
            self.__log.changed = False

    def __create_log_image(self):
        """Create the label image to be displayed only called when the log is changed"""
        image = pygame.Surface(self.rect.size)
        image.fill((150, 150, 150))
        prev_line_heigth = 0
        for i, line in enumerate(iter(self.__log)):
            if self.rect.height - prev_line_heigth < 0:
                break
            text = line.render()
            prev_line_heigth += text.get_size()[1]
            image.blit(text, (5, self.rect.height - prev_line_heigth))
        return image.convert()


class TextLog:
    """Log for tracking the commands typed by the user, warnings and confirmation messages. Commands typed by the user
    are tracked separatelly from the others in order to allow the for finding back these commands

    The user log and warning/confirmation log are dictionaries with indexes as keys, together one full log is formed
    """

    __user_log: Dict
    __warning_and_confirmation_log: Dict
    __user_log_location: int
    changed: bool

    def __init__(self):
        self.__user_log = {}  # the log with user issued commands
        self.__warning_and_confirmation_log = {}  # all other text that is commited to the log
        self.__user_log_location = 0
        self.changed = False

    def __getitem__(self, key):
        return self.__user_log[len(self.__user_log) - key]

    def __len__(self):
        return len(self.__user_log)

    def __iter__(self):
        """return all the user and warning messages in one itter sorted based on the insertion line"""
        combined_keys = list(self.__user_log.keys()) + list(self.__warning_and_confirmation_log.keys())
        combined_keys.sort()
        combined = {**self.__user_log, **self.__warning_and_confirmation_log}
        sorted_lines = reversed(list(combined[key] for key in combined_keys))
        return iter(sorted_lines)

    def append(
        self,
        line: "Line"
    ):
        """Add a line to the user log"""
        self.__user_log[len(self.__user_log) + len(self.__warning_and_confirmation_log)] = line
        self.changed = True
        # always place the cursor at the last line to act like linux instead of windows command line
        self.__user_log_location = 0

    def append_other(
        self,
        line: "Line"
    ):
        """Add a line to the warning/confirmation log"""
        self.__warning_and_confirmation_log[len(self.__user_log) + len(self.__warning_and_confirmation_log)] = line
        self.changed = True

    def line_up(self) -> "Line":
        """Move the line location one line up if possible and return a copy of the the line moved to"""
        if len(self.__user_log) == 0:
            return Line()
        if self.__user_log_location < len(self.__user_log):
            self.__user_log_location += 1
        return list(self.__user_log.values())[-self.__user_log_location].copy()

    def line_down(self) -> "Line":
        """Move the line location one line down if possible and return a copy of the the line moved to"""
        if self.__user_log_location > 0:
            self.__user_log_location -= 1
        if self.__user_log_location == 0:
            return Line()
        return list(self.__user_log.values())[-self.__user_log_location].copy()


class Line:
    """TextLog lines that are easier to keep track of and have methods for console accurate rendering"""

    MAX_LINE_LENGTH = con.SCREEN_SIZE.width
    BACKGROUND_COLOR = (150, 150, 150)

    text: str
    __color: Union[Tuple[int, int, int], List[int]]
    __line_location: int
    __rendered_str: Union[None, pygame.Surface]
    __font: pygame.font.Font
    __line_type: str

    def __init__(
        self,
        text: str = "",
        color: Union[Tuple[int, int, int], List[int]] = (0, 255, 0),
        font: int = 22,
        line_type: str = "normal"
    ):
        self.text = text
        self.__color = color
        self.__line_location = len(self.text)
        self.__rendered_str = None
        self.__font = con.FONTS[font]
        self.__line_type = line_type

    def __str__(self):
        return self.text

    def render(self) -> pygame.Surface:
        """Render the string of this line, either return the rendered version of it was rendered before or actually
        render the string"""
        if self.__rendered_str:
            return self.__rendered_str
        else:
            return self.__render_string()

    def __render_string(self) -> pygame.Surface:
        """Render the string based on the __line_type, the line type determines if a list like format is rendered or
        the normal line with enters if neccesairy"""
        if self.__line_type == "normal":
            text = self.__render_normal_line()
        elif self.__line_type == "list":
            text = self.__render_list_line()
        else:
            raise util.GameException(f"Unsupported line_type {self.__line_type}")
        surf = pygame.Surface((con.SCREEN_SIZE.width + 2, len(text) * self.__font.size("k")[1] + 2))

        surf.fill(self.BACKGROUND_COLOR)
        for index, line in enumerate(text):
            rt = self.__font.render(line, True, self.__color)
            surf.blit(rt, (0, rt.get_size()[1] * index))
        return surf

    def __render_normal_line(self) -> List[str]:
        """Render a 'normal' text line that can be longer then the given MAX_LINE_LENGTH. In that the case the line
        is split up in multiple lines using the words to break."""
        if self.__font.size(self.text)[0] > self.MAX_LINE_LENGTH:
            words = self.text.split(" ")
            lines = [""]
            line_length = 0
            for word in words:
                word_size = self.__font.size(word + " ")[0]
                if line_length + word_size < self.MAX_LINE_LENGTH:
                    lines[len(lines) - 1] += word + " "
                    line_length += word_size
                else:
                    line_length = self.__font.size(word)
                    lines.append(word)
            return lines
        else:
            return [self.text]

    def __render_list_line(self) -> List[str]:
        """Render a line that represents a list of values that are seperated on spaces. In this case the line should
        be shown in sutch a way that the list elements allign under one another if there are multiple lines needed"""
        words = self.text.split(" ")
        longest_word = max(self.__font.size(word + "   ")[0] for word in words)
        lines = [""]
        line_length = 0
        for word in words:
            word_size = self.__font.size(word)[0]
            while word_size < longest_word:
                word += " "
                word_size = self.__font.size(word)[0]
            if line_length + word_size < self.MAX_LINE_LENGTH:
                lines[len(lines) - 1] += word
                line_length += word_size
            else:
                line_length = word_size
                lines.append(word)
        return lines

    def __len__(self):
        return len(self.text)

    def copy(self) -> "Line":
        """Return a copy of this line"""
        return Line(text=self.text, color=self.__color, line_type=self.__line_type)
