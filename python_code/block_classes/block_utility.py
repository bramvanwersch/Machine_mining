
import block_classes
from block_classes import machine_materials


def material_type_from_string(string):
    if string in dir(block_classes.ground_materials):
        material = getattr(block_classes.ground_materials, string)
    elif string in dir(block_classes.flora_materials):
        material = getattr(block_classes.flora_materials, string)
    elif string in dir(block_classes.building_materials):
        material = getattr(block_classes.building_materials, string)
    elif string in dir(block_classes.machine_materials):
        material = getattr(block_classes.machine_materials, string)
    else:
        material = getattr(block_classes.materials, string)
    return material
