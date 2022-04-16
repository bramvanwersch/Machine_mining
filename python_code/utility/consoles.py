import pygame
import re
from typing import Union, Tuple, List, Dict, Any, TYPE_CHECKING
import os
import inspect
from abc import ABC, abstractmethod

import utility.inventories
import utility.utilities as util
import utility.constants as con
from utility.constants import DEBUG
from utility import game_timing
from block_classes.materials import building_materials, environment_materials, ground_materials,\
    machine_materials, materials

if TYPE_CHECKING:
    from utility.inventories import Inventory
    from board.board import Board
    from machines.base_machine import Machine, MachineBlock
    import user


class Console(ABC):
    command_tree: Dict[str, Any]

    def __init__(self):
        self.command_tree = {}

    @abstractmethod
    def process_line(
        self,
        text: str
    ) -> List[Tuple[str, bool]]:
        pass


class MainConsole(Console):
    """Class that allows for using commands in order to manipulate values while the game is running
    Quick guide:
        - Every command is build up in a simple way. Name of main command, a series of names indicating where to find
         the value. A potential value to set the located value too.
        - tab can be pressed to see the allowed commands given a certain type point.
        - square brackets ([]) can be used in order to save typing by allowing some sort of multiplication e.g print
         debug [FPS, NO_LIGHTING] -means-> print debug FPS and print debug NO_LIGTHING, this works in a nested fashion
         as well
        - brackets and ; are used in order to set lists in order to not interfer with the square bracket syntax
    """
    __board: "Board"
    __user: "user.User"

    def __init__(
        self,
        board: "Board",
        user_: "user.User"
    ):
        super().__init__()
        self.__board = board
        self.__user = user_
        self.__innitialise_command_tree()

    def __innitialise_command_tree(self):
        self.command_tree["print"] = self.__create_print_tree()
        self.command_tree["scripts"] = self.__create_script_tree()
        self.command_tree["set"] = self.__create_set_tree()
        self.command_tree["add_item"] = self.__create_add_item_tree()

    def __create_print_tree(self) -> Dict[str, Any]:
        tree = dict()
        tree["debug"] = self.__create_attribute_tree(DEBUG, "printables")
        tree["workers"] = {f"worker_{index + 1}": self.__create_attribute_tree(worker, "printables")
                           for index, worker in enumerate(self.__user.workers)}
        tree["buildings"] = \
            {f"buildling_{index + 1}({buidling.name()[:3]})": self.__create_attribute_tree(buidling, "printables")
             for index, buidling in enumerate(self.__user.board.buildings.values())}
        tree["timings"] = False
        return tree

    def __create_set_tree(self) -> Dict[str, Any]:
        tree = dict()
        tree["debug"] = self.__create_attribute_tree(DEBUG, "setables")
        tree["workers"] = {f"worker_{index + 1}": self.__create_attribute_tree(worker, "setables")
                           for index, worker in enumerate(self.__user.workers)}
        tree["buildings"] = \
            {f"buildling_{index + 1}({buidling.name()[:3]})": self.__create_attribute_tree(buidling, "setables")
             for index, buidling in enumerate(self.__user.board.buildings.values())}
        return tree

    def __create_script_tree(self) -> Dict[str, Any]:
        """Scrips are read from a file that contain a name, ':' and then a oneliner to be executed"""
        partsfile = os.path.join(con.DATA_DIR, "scripts.txt")
        f = open(partsfile, "r")
        lines = f.readlines()
        f.close()
        tree = {}
        for line in lines:
            name, command_line = line.split(":")
            tree[name] = command_line
        return tree

    def __create_add_item_tree(self) -> Dict[str, Any]:
        tree = dict()
        for module, module_name in [(building_materials, "building_materials"),
                                    (environment_materials, "environment_materials"),
                                    (ground_materials, "ground_materials"),
                                    (machine_materials, "machine_materials")]:
            tree[module_name] = {}
            for cls_name, cls in inspect.getmembers(module, inspect.isclass):
                if inspect.isclass(cls) and issubclass(cls, materials.BaseMaterial) and not util.is_abstract(cls):
                    tree[module_name][cls_name] = cls
        return tree

    def __create_attribute_tree(
        self,
        target: util.ConsoleReadable,
        function: str
    ) -> Dict[str, Any]:
        """Starting from a ConsoleReadable collect all relevant values at a certain provided function and check if
        those are console readable. If that os the case recursively continue"""
        tree = {}
        target_function = getattr(target, function)
        attributes = target_function()
        for str_atr in attributes:
            new_target = getattr(target, str_atr)
            if isinstance(new_target, util.ConsoleReadable):
                tree[str_atr] = self.__create_attribute_tree(new_target, function)
            else:
                tree[str_atr] = False
        return tree

    def process_line(
        self,
        text: str
    ) -> List[Tuple[str, bool]]:
        """Process a string that presumably represents a valid command, return a message and bool indicating failure"""
        results = []
        try:
            commands_list = self.__text_to_commands(text)
        except ValueError as e:
            return [(str(e), True)]
        for arguments in commands_list:
            arguments = arguments.strip().split(" ")
            try:
                if arguments[0] == "print":
                    results.append(self.__process_arguments(arguments))
                elif arguments[0] == "scripts":
                    # special case
                    results.extend(self._process_script_call(arguments))
                elif arguments[0] == "set":
                    results.append(self.__process_arguments(arguments))
                elif arguments[0] == "add_item":
                    results.append(self.__process_add_item(arguments))
                else:
                    results.append(("{} is not a valid command. Choose one of the following: {}."
                                    .format(arguments[0], ", ".join(self.command_tree.keys())), True))
            except (IndexError, KeyError):
                results.append((f"Not enough arguments supplied for the {arguments[0]} command.", True))
        return results

    def __text_to_commands(
        self,
        text: str
    ) -> List[str]:
        """Extract all commands in a given text by writing out all the lists into lines of commands conveyed by those
        lists"""
        text = text.strip()
        lists = {}
        if text.count("]") != text.count("["):
            raise ValueError("Uneven amount of open and closing brackets.")
        # first get all lists within lists
        count = 0
        while True:
            matches = re.findall("\[[^\[]+?\]", text)  # noqa --> because fuck off
            if matches:
                for match in matches:
                    text = text.replace(match, ",list" + str(count))
                    lists["list" + str(count)] = match
                    count += 1
            else:
                break
        # then get all commands conveyed by those lists
        return self.__get_command_list(text, lists)

    def __get_command_list(
        self,
        text: str,
        lists: Dict
    ) -> List[str]:
        text: List = text.split(",")
        fl = []
        for i in range(len(text)):
            if text[i] in lists:
                text[i] = self.__get_command_list(lists[text[i]][1:-1], lists)
                for val in text[i]:
                    combined = text[i - 1].strip() + " " + val.strip()
                    fl.append(combined)
                    # remove the shorter version from the final_list
                    if text[i-1] in fl:
                        fl.remove(text[i-1])
            else:
                fl.append(text[i])
        return fl

    def __process_arguments(
        self,
        arguments: List[str]
    ) -> Tuple[str, bool]:
        start_argument_index = 1
        check_dictionary = self.command_tree[arguments[0]][arguments[1]]
        if arguments[1] == "debug":
            target = DEBUG
        elif arguments[1] == "workers":
            target = self.__user.workers[int(arguments[2].split("_")[1]) - 1]
            start_argument_index = 2
            check_dictionary = check_dictionary[arguments[2]]
        elif arguments[1] == "buildings":
            target = list(self.__user.board.buildings.values())[int(arguments[2].split("_")[1].split("(")[0]) - 1]
            start_argument_index = 2
            check_dictionary = check_dictionary[arguments[2]]
        elif arguments[1] == "timings":
            return game_timing.TIMINGS.get_time_summary()[:-1], False
        else:
            raise util.GameException(f"Unexpected value to print from; {arguments[1]}")

        return getattr(self, f"_process_{arguments[0]}")(arguments, start_argument_index, check_dictionary, target)

    def __process_add_item(self, arguments):
        if len(arguments) < 4:
            return f"Expected 3 arguments to add item only got {len(arguments)}", True
        material = getattr(globals()[arguments[1]], arguments[2])()
        try:
            amount = int(arguments[3])
        except ValueError:
            return "Expected the amount argument to be a valid integer", True
        if amount <= 0:
            return "The amount must be bigger then 0", True
        item = utility.inventories.Item(material, amount)
        self.__board.add_to_terminal_inventory(item)
        return f"Added {str(item)} to the terminal", False

    def _process_print(
        self,
        arguments: List[str],
        start_argument_index: int,
        check_dictionary: Dict,
        target: Any
    ) -> Tuple[str, bool]:
        """Process a print call by the user"""
        index = start_argument_index + 1
        # walk down the tree for all the arguments
        while index < len(arguments):
            if not isinstance(check_dictionary, dict) or arguments[index] not in check_dictionary:
                return "Value {} cannot be accessed or is not allowed to be accessed".\
                           format(".".join(arguments[start_argument_index:])), True
            else:
                check_dictionary = check_dictionary[arguments[index]]
            target = getattr(target, arguments[index])
            index += 1
        return "Value of {} is {}".format(".".join(arguments[start_argument_index:]), str(target)), False

    def _process_script_call(
        self,
        arguments: List[str]
    ) -> List[Tuple[str, bool]]:
        """Process a script call by taking the name and taking the provided line"""
        command_line = self.command_tree["scripts"][arguments[1]]
        results = self.process_line(command_line)
        return results

    def _process_set(
        self,
        arguments: List[str],
        start_argument_index: int,
        check_dictionary: Dict,
        target: Any
    ) -> Tuple[str, bool]:
        index = start_argument_index + 1
        # walk down the tree for all the arguments
        if len(arguments) < 3:
            return "Expected at least 3 arguments for a set call.", True
        while index < len(arguments) - 2:
            if not isinstance(check_dictionary, dict) or arguments[index] not in check_dictionary:
                return "Value {} cannot be accessed or is not allowed to be accessed". \
                           format(".".join(arguments[start_argument_index:])), True
            else:
                check_dictionary = check_dictionary[arguments[index]]
            target = getattr(target, arguments[index])
            index += 1
        new_value = arguments[-1]
        target_attribute = arguments[-2]
        if not hasattr(target, target_attribute):
            return "Value {} cannot be accessed or is not allowed to be accessed". \
                       format(".".join(arguments[start_argument_index:])), True
        current_value = getattr(target, target_attribute)
        try:
            proper_type_new_value = self.__convert_to_type(new_value, current_value)
        except ValueError as e:
            return str(e), True
        setattr(target, target_attribute, proper_type_new_value)
        return "The value {} = {} is set to {}".format('.'.join(arguments[start_argument_index:-1]), current_value,
                                                       str(proper_type_new_value)), False

    def __convert_to_type(
        self,
        string_to_convert: str,
        orig_value: Any
    ) -> Any:
        try:
            if isinstance(orig_value, str):
                return string_to_convert
            elif isinstance(orig_value, bool):
                return self.__string_to_bool(string_to_convert)
            elif isinstance(orig_value, int):
                return int(string_to_convert)
            elif isinstance(orig_value, float):
                return float(string_to_convert)
            elif isinstance(orig_value, list) or isinstance(orig_value, tuple):
                return self.__string_to_list(string_to_convert, orig_value)
            elif isinstance(orig_value, pygame.math.Vector2):
                values = self.__string_to_list(string_to_convert, [orig_value[0], orig_value[1]])
                return pygame.math.Vector2(*values)
            elif isinstance(orig_value, pygame.Rect):
                values = self.__string_to_list(string_to_convert, [orig_value[0], orig_value[1], orig_value[2],
                                                                   orig_value[3]])
                return pygame.Rect(*values)
            elif con.DEBUG.WARNINGS:
                print("No case for value of type {}".format(type(orig_value)))
        except ValueError as e:
            raise e
        raise ValueError("cannot convert to type_s {}. No known method.".format(type(orig_value)))

    def __string_to_bool(
        self,
        value: str
    ) -> bool:
        value = value.lower()
        if value == "true" or value == "t":
            return True
        elif value == "false" or value == "f":
            return False
        else:
            raise ValueError("expected a boolean to be either: true, t, false or f (case insensitive)".format(value))

    def __string_to_list(
        self,
        value: str,
        orig_list: Union[List, Tuple]
    ) -> List[Any]:
        """
        only a one dimensional list is expected
        """
        if "(" not in value:
            raise ValueError("expected a list to be of form (val1;val2;..)")
        value = value.replace("(", "").replace(")", "")
        the_list = [val.strip() for val in value.split(";")]
        if len(orig_list) != len(the_list):
            raise ValueError("list is of wrong length. Expected a list of lenght {}.".format(len(orig_list)))
        for index, value in enumerate(orig_list):
            val_type = type(value)
            try:
                user_value = the_list[index]
                if val_type != str:
                    user_value = user_value.strip()
                correct_typed_value = self.__convert_to_type(user_value, value)
                the_list[index] = correct_typed_value
            except ValueError:
                raise ValueError("expected value of type {} at index {}. Cannot convert {} to {}."
                                 .format(val_type, index, the_list[index], val_type))
        return the_list


class MachineConsole(Console):

    _code_wrapper: Union["_MachineCodeWrapper", None]

    def __init__(self):
        super().__init__()
        self._code_wrapper = None

    def set_machine(
        self,
        machine: "Machine"
    ):
        # this value is set before the user can open the interface and use the console
        self._code_wrapper = _MachineCodeWrapper(machine)
        self.command_tree = self._code_wrapper.get_possible_commands_dict()

    def process_line(
        self,
        text: str
    ) -> List[Tuple[str, bool]]:
        if "(" not in text:
            return [(f"Functions need opening and closing brackets after the name", True)]
        if text.strip()[-1] != ")":
            return [(f"Functions need opening and closing brackets after the name", True)]
        function_name, args = self._get_function_call(text)
        if function_name not in self.command_tree:
            return [(f"No function with name {function_name}", True)]
        try:
            # make sure it is always a string
            return [(str(self.command_tree[function_name](*args)), False)]
        except Exception as e:
            return [(f"call failed with message: {str(e)}", True)]

    def _get_function_call(self, text: str) -> Tuple[str, List[str]]:
        function_name, argument_part = text.split("(")
        argument_part = argument_part.replace(")", "")
        arguments = [arg.strip() for arg in argument_part.split(",")]

        # in case no arguments are provided, but keeping empty arguments for consistency
        if len(arguments) == 1 and arguments[0] == "":
            arguments = []
        return function_name, arguments


class _MachineCodeWrapper:
    """This will be a wrapper for all functions that can be called on machines in the language and from console"""
    _machine: "Machine"

    def __init__(self, machine: "Machine"):
        self._machine = machine

    def get_possible_commands_dict(self):
        return {tpl[0]: tpl[1] for tpl in inspect.getmembers(self, predicate=inspect.ismethod) if
                tpl[0] not in {"__init__", "get_possible_commands_dict"}}

    # here are all callable methods from console and language

    def get_size(self) -> int:
        return self._machine.size

    def get_parts(self) -> List["MachineBlock"]:
        """
        Get all the blocks that the machine is made up of starting from the block with the lowest x, y coordinate then
        increasing first the x and then the y coordinate.

        Returns:
            A List of Block instances
        """
        return self._machine.get_blocks()

    def get_placers(self) -> List["MachineBlock"]:
        """
        Get all the placers in the machine starting from the block with the lowest x, y coordinate then
        increasing first the x and then the y coordinate.

        Returns:
            A List of Block instances
        """
        return self._machine.get_blocks(machine_materials.MachinePlacer)

    def get_drills(self) -> List["MachineBlock"]:
        """
        Get all the drills in the machine starting from the block with the lowest x, y coordinate then
        increasing first the x and then the y coordinate.

        Returns:
            A List of Block instances
        """
        return self._machine.get_blocks(machine_materials.MachineDrill)

    def get_movers(self) -> List["MachineBlock"]:
        """
        Get all the movers in the machine starting from the block with the lowest x, y coordinate then
        increasing first the x and then the y coordinate.

        Returns:
            A List of Block instances
        """
        return self._machine.get_blocks(machine_materials.MachineDrill)

    def get_inventory(self) -> "Inventory":
        """
        Get the inventory of the current machine. This inventory can be used to check items
        Returns:

        """
        return "To be implemented"

    def get_overview(self):
        blocks = self._machine.get_blocks()
        max_x_block = max(blocks, key=lambda x: x.x_coordinate)
        max_y_block = max(blocks, key=lambda x: x.y_coordinate)
        strings = [[" " for _ in range(max_x_block.x_coordinate + 1)] for _ in range(max_y_block.y_coordinate + 1)]
        for block in blocks:
            strings[block.y_coordinate][block.x_coordinate] = f"{block.get_letter()}"
        strings = [''.join(lst) for lst in strings]
        return '\n'.join(strings)

    def drill(self, drills):
        pass

    def place(self, placers, block_type):
        pass

    def move_x(self, amnt):
        pass

    def move_y(self, amnt):
        pass

    def help(self, function_name):
        pass
