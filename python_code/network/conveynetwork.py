
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from block_classes.blocks import ConveyorNetworkBlock


class ConveyorNetwork:

    __belts: Dict[str, "ConveyorNetworkBlock"]

    def __init__(self):
        self.__belts = {}

    def add(self, belt: "ConveyorNetworkBlock"):
        self.__belts[belt.id] = belt

    def remove(self, belt: "ConveyorNetworkBlock"):
        del self.__belts[belt.id]

    def __iter__(self):
        # the copy is neccesairy because loading chunks are able to add belts and that would crash the game
        return iter(self.__belts.copy().values())

    def __len__(self):
        return len(self.__belts)
