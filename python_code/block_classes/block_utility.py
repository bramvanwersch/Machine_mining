import inspect
from typing import Set

import block_classes.materials as base_materials
import block_classes.ground_materials as ground_m
import block_classes.flora_materials as flora_m
import block_classes.building_materials as build_m
import utility.utilities as util


# Collections used for getting all type of a certain material for conventience
fuel_materials = set()
ore_materials = set()
filler_materials = set()
flora_materials = set()


def material_instance_from_string(string: str, **kwargs) -> base_materials.BaseMaterial:
    """Get the instance of the material named by string

    Args:
        string (str): name of the material you want the instance from
        **kwargs: optional arguments

    Returns:
        material instance
    """
    if string in dir(ground_m):
        material = getattr(ground_m, string)
    elif string in dir(flora_m):
        material = getattr(flora_m, string)
    elif string in dir(build_m):
        material = getattr(build_m, string)
    # elif string in dir(block_classes.machine_materials):
    #     material = getattr(block_classes.machine_materials, string)
    else:
        material = getattr(base_materials, string)
    return material(**kwargs)


def configure_material_collections() -> None:
    """Configure the sets of materials names at the beginning of the module"""
    global fuel_materials, ore_materials, filler_materials, flora_materials
    for module in (flora_m, ground_m):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            selected_sets = []
            if issubclass(cls, ground_m.Burnable) and not util.is_abstract(cls):
                selected_sets.append(fuel_materials)
            if issubclass(cls, ground_m.OreMaterial) and not util.is_abstract(cls):
                selected_sets.append(ore_materials)
            if issubclass(cls, ground_m.FillerMaterial) and not util.is_abstract(cls) and \
                    cls is not ground_m.FillerMaterial:
                selected_sets.append(filler_materials)
            if (issubclass(cls, flora_m.FloraMaterial) or issubclass(cls, flora_m.MultiFloraMaterial))\
                    and not util.is_abstract(cls):
                selected_sets.append(flora_materials)
            if len(selected_sets) > 0:
                [set_.add(cls) for set_ in selected_sets]
    __add_collection(flora_materials, flora_m.ShroomCollection())
    __add_collection(filler_materials, ground_m.StoneCollection())


def __add_collection(set_: Set, *collections) -> None:
    """Add all materials present in a collection to the provided set"""
    for collection in collections:
        set_.add(collection)
        for elem in set_.copy():
            if elem in collection:
                set_.remove(elem)
