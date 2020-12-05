import inspect

import block_classes
from block_classes import machine_materials, flora_materials as flora_m, ground_materials as ground_m


# Collections used for getting all type of a certain material
fuel_materials = set()
ore_materials = set()
filler_materials = set()
flora_materials = set()


def material_instance_from_string(string, **kwargs):
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
    return material(**kwargs)


def configure_material_collections():
    global fuel_materials, ore_materials, filler_materials, flora_materials
    for module in (flora_m, ground_m):
        for name, obj in inspect.getmembers(module, inspect.isclass):
            selected_sets = []
            if issubclass(obj, ground_m.FuelMaterial) and obj != ground_m.FuelMaterial:
                selected_sets.append(fuel_materials)
            if issubclass(obj, ground_m.OreMaterial) and obj != ground_m.OreMaterial:
                selected_sets.append(ore_materials)
            if issubclass(obj, ground_m.FillerMaterial) and obj != ground_m.FillerMaterial:
                selected_sets.append(filler_materials)
            if issubclass(obj, flora_m.FloraMaterial) or issubclass(obj, flora_m.MultiFloraMaterial) and obj not in\
                    (flora_m.FloraMaterial, flora_m.MultiFloraMaterial):
                selected_sets.append(flora_materials)
            if len(selected_sets) > 0:
               [set_.add(obj) for set_ in selected_sets]
    __add_collection(flora_materials, flora_m.ShroomCollection())
    __add_collection(filler_materials, ground_m.StoneCollection())


def __add_collection(set_, *collections):
    for collection in collections:
        set_.add(collection)
        for elem in set_.copy():
            if elem in collection:
                set_.remove(elem)
