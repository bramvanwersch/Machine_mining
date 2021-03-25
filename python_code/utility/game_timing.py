import time
from typing import Callable, Dict, List, Union, Any


TIMINGS: Union[None, "Timings"] = None


def config_timings_value():
    """Innitialise the TIMINGS value"""
    global TIMINGS
    TIMINGS = Timings()


class Timings:
    """Track the timings of values that are marked with the time_function decorator"""

    named_timings: Dict[str, "_TimedValue"]
    __frame_number: int

    def __init__(self):
        self.named_timings = dict()
        self.__frame_number = 0

    def add(
        self,
        name: str,
        value: float
    ):
        """Add a value to a named timing"""
        if name in self.named_timings:
            self.named_timings[name].add_value(value, self.__frame_number)
        else:
            self.named_timings[name] = _TimedValue()
            self.named_timings[name].add_value(value, self.__frame_number)

    def increase_frame_count(self):
        self.__frame_number += 1

    def get_time_summary(self) -> str:
        """Get the percentages of all the named timings that are saved"""
        summary = f"Past {_TimedValue.MAX_SAVED_TIMINGS} frames timings:\n"
        timings = {name: timed_value.get_average_value() for name, timed_value in self.named_timings.items()}
        total_time_timed = sum(timings.values())
        if total_time_timed == 0:
            return ""
        for name, timing in timings.items():
            summary += f"{name}: ({(timing / total_time_timed) * 100:.2f}%)\n"
        return summary


class _TimedValue:
    """Track a list of a certain length of time it took to run a function per frame. All calls in one frame are put
    together"""
    MAX_SAVED_TIMINGS = 100  # a list of timings saved for each saved varaible

    time_values: List[Union[float, None]]
    __additon_index: int
    __frame_nmr: int

    def __init__(self):
        self.time_values = [None for _ in range(self.MAX_SAVED_TIMINGS)]
        self.__addition_index = 0
        self.__frame_nmr = 0

    def add_value(
        self,
        value: float,
        actual_frame_number: int
    ):
        """Add a value at the addition_index (cycles from 0-MAX_SAVED_TIMINGS to make it a bit more efficient) and add
        the value up if within the same frame otherwise put in the next slot"""
        if actual_frame_number != self.__frame_nmr:
            self.__frame_nmr = actual_frame_number
            self.time_values[self.__addition_index] = value
            self.__addition_index += 1
            if self.__addition_index > self.MAX_SAVED_TIMINGS - 1:
                self.__addition_index = 0
        else:
            self.time_values[self.__addition_index - 1] += value

    def get_average_value(self) -> float:
        """Get the average value of the time_values"""
        valid_values = [value for value in self.time_values if value is not None]
        return sum(valid_values) / len(valid_values)


def time_function(time_name: str) -> Any:
    """Time a function decorated with this"""
    def function_decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            global TIMINGS
            TIMINGS.add(time_name, end - start)
            return result
        return wrapper
    return function_decorator
