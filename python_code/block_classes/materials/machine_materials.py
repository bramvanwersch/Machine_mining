from abc import ABC
from typing import List, ClassVar, Dict, Type, Any

# own imports
from utility import constants as con
import utility.image_handling

import block_classes.materials.materials as base_materials
import block_classes.blocks as blocks
import block_classes.machine_blocks as machine_blocks
import machines.logic_components as components


class MachineComponent(base_materials.TransportableMaterial, ABC):

    def __init__(
        self,
        changed: bool = False,
        **kwargs
    ):
        self._changed = changed

    # noinspection PyPep8Naming
    @property
    def VIEWABLE(self) -> bool:
        # if this component is shown in detail in the machine view
        return False

    # noinspection PyPep8Naming
    @property
    def LOGIC_COMPONENT(self) -> Type[components.LogicComponent]:
        return components.LogicComponent

    @property
    def changed(self):
        changed = self._changed
        self._changed = False
        return changed

    def connecting_directions(self) -> List[int]:
        return [0, 1, 2, 3]

    @property
    def id(self):
        return f"{id(self)}"


class MultiImageMachineComponent(MachineComponent, base_materials.MultiImageMaterial, ABC):

    def __init__(self, image_key=None, **kwargs):
        MachineComponent.__init__(self, **kwargs)
        base_materials.MultiImageMaterial.__init__(self, image_key)

    def change_image_key(
        self,
        value: Any
    ):
        self.image_key = value
        self._changed = True

    @property
    def id(self):
        return f"{id(self)}{self.image_key}"

    def set_active(
        self,
        value: bool
    ):
        super().set_active(value)
        self._changed = True


class UnbuildableMachineComponent(MultiImageMachineComponent, base_materials.Unbuildable, ABC):
    pass


class WireConnector(UnbuildableMachineComponent):
    LOGIC_COMPONENT: Type[components.LogicComponent] = components.ConnectorLogicComponent
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {"": utility.image_handling.ImageDefinition("buildings", (50, 40)),
         "r": utility.image_handling.ImageDefinition("buildings", (60, 40)),
         "g": utility.image_handling.ImageDefinition("buildings", (70, 40)),
         "b": utility.image_handling.ImageDefinition("buildings", (80, 40)),
         "rg": utility.image_handling.ImageDefinition("buildings", (90, 40)),
         "rb": utility.image_handling.ImageDefinition("buildings", (0, 50)),
         "gb": utility.image_handling.ImageDefinition("buildings", (10, 50)),
         "rgb": utility.image_handling.ImageDefinition("buildings", (20, 50))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (50, 40), image_size=con.TRANSPORT_BLOCK_SIZE)

    def __init__(self, image_key=None, **kwargs):
        super().__init__(image_key=image_key if image_key is not None else "", **kwargs)


class NormalMachineComponent(base_materials.ImageMaterial, MachineComponent, ABC):
    pass


class MachineConnector(NormalMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineTerminal(NormalMachineComponent):
    _BLOCK_TYPE: ClassVar[blocks.Block] = machine_blocks.MachineTerminalBlock
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (70, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (70, 0), image_size=con.TRANSPORT_BLOCK_SIZE)


class MachineInventory(NormalMachineComponent):
    """Visual not an actual inventory will increase the carying capacity of the terminal"""
    IMAGE_DEFINITIONS: ClassVar[List[utility.image_handling.ImageDefinition]] = \
        utility.image_handling.ImageDefinition("buildings", (80, 30))
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (80, 30), image_size=con.TRANSPORT_BLOCK_SIZE)


class RotatableMachineComponent(MultiImageMachineComponent, base_materials.RotatableMaterial, ABC):

    def rotate(
        self,
        rotate_count: int
    ):
        self._changed = True
        self.image_key = rotate_count
        self.image_key %= 4


class MachineDrill(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 0)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 0)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 0)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 0))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 0), image_size=con.TRANSPORT_BLOCK_SIZE)
    VIEWABLE: bool = True


class MachineMover(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 10)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 10)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 10)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 10))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 10), image_size=con.TRANSPORT_BLOCK_SIZE)
    VIEWABLE: bool = True


class MachinePlacer(RotatableMachineComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 20)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 20)),
         2: utility.image_handling.ImageDefinition("buildings", (80, 20)),
         3: utility.image_handling.ImageDefinition("buildings", (90, 20))}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (60, 20), image_size=con.TRANSPORT_BLOCK_SIZE)
    VIEWABLE: bool = True


class WireComponent(RotatableMachineComponent, base_materials.Unbuildable, ABC):

    def rotate(
        self,
        rotate_count: int
    ):
        self.image_key = rotate_count
        self.image_key %= 2

    def connecting_directions(self) -> List[int]:
        if self.image_key == 0:
            return [1, 3]
        else:
            return [0, 2]


class DirectionalWireComponent(RotatableMachineComponent, base_materials.Unbuildable, ABC):

    def connecting_directions(self) -> List[int]:
        if self.image_key == 0 or self.image_key == 2:
            return [1, 3]
        else:
            return [0, 2]


class RedWire(WireComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (90, 30)),
         1: utility.image_handling.ImageDefinition("buildings", (90, 30), rotate=90)}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (90, 30), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (0, 40)),
         1: utility.image_handling.ImageDefinition("buildings", (0, 40), rotate=90)}


class RedInverterWire(DirectionalWireComponent):
    LOGIC_COMPONENT: Type[components.LogicComponent] = components.InverterLogicComponent
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (30, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (30, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (20, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (20, 60), rotate=90)
         }
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (30, 50), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (60, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (60, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (50, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (50, 60), rotate=90)}


class GreenWire(WireComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (10, 40)),
         1: utility.image_handling.ImageDefinition("buildings", (10, 40), rotate=90)}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (10, 40), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (20, 40)),
         1: utility.image_handling.ImageDefinition("buildings", (20, 40), rotate=90)}


class GreenInverterWire(DirectionalWireComponent):
    LOGIC_COMPONENT: Type[components.LogicComponent] = components.InverterLogicComponent
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (40, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (40, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (10, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (10, 60), rotate=90)}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (40, 50), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (70, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (70, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (40, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (40, 60), rotate=90)}


class BlueWire(WireComponent):
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (30, 40)),
         1: utility.image_handling.ImageDefinition("buildings", (30, 40), rotate=90)}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (30, 40), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (40, 40)),
         1: utility.image_handling.ImageDefinition("buildings", (40, 40), rotate=90)}


class BlueInverterWire(DirectionalWireComponent):
    LOGIC_COMPONENT: Type[components.LogicComponent] = components.InverterLogicComponent
    IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (50, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (50, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (0, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (0, 60), rotate=90)}
    TRANSPORT_IMAGE_DEFINITION: ClassVar[utility.image_handling.ImageDefinition] = \
        utility.image_handling.ImageDefinition("buildings", (50, 50), image_size=con.TRANSPORT_BLOCK_SIZE)
    ACTIVE_IMAGE_DEFINITIONS: ClassVar[Dict[int, List[utility.image_handling.ImageDefinition]]] = \
        {0: utility.image_handling.ImageDefinition("buildings", (80, 50)),
         1: utility.image_handling.ImageDefinition("buildings", (80, 50), rotate=90),
         2: utility.image_handling.ImageDefinition("buildings", (30, 60)),
         3: utility.image_handling.ImageDefinition("buildings", (30, 60), rotate=90)}
