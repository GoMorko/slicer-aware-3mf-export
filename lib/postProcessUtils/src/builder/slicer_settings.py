import json
from os.path import join
from itertools import chain

from ..utils.xml_utils import *
from ..common.consts import types_to_parts
from ..common.types import ObjectModel

__all__ = [
    'create_model_settings',
]

# create XML config file: "./Metadata/model_settings.config"
def create_model_settings(catalog_path: str, model_dict):
    config_root = ET.Element('config')

    for _component_name, component_objects_group in model_dict.components.items():
        # there must be at least one "real" config->object.
        # which is the actual object on a plate, and works as group for all other parts
        # (printed 3d models - "normal_part" sub type; and other ephemeral models like "modifier_part" and "negative_part")
        main_obj = component_objects_group['main']
        wrapping_component = component_objects_group['wrapping_component']

        # config->object
        object_element = ET.SubElement(config_root, 'object', {
            'id': wrapping_component['id'],
        })

        # config->object->metadata
        ET.SubElement(object_element, 'metadata', {
            'key': 'name',
            'value': f"{wrapping_component['namespace']}_{wrapping_component['name']}"
        })

        # config->object->part w/ its metadata for the main object
        object_element.append(create_part_config(main_obj))

        # config->object->part w/ its metadata for rest of the parts
        for sub_object in list(chain.from_iterable(component_objects_group['sub_types'].values())):
            object_element.append(create_part_config(sub_object))

    with open (join(catalog_path, "Metadata/model_settings.config"), "wb") as file:
        ET.ElementTree(config_root).write(file, xml_declaration=True, encoding='UTF-8')

def type_to_part_name(type_name: str) -> str:
    return types_to_parts.get(type_name, 'normal_part')

# ./Metadata/model_settings.config
# config->object->part
def create_part_config(model: ObjectModel) -> ET.Element:
    # part element
    part = ET.Element('part', {
        'id': model['id'],
        # subtype - eg. modifier_part, negative_part; interpreted accordingly as such by the slicer.
        'subtype': type_to_part_name(model['type']),
    })

    # displayed object name
    ET.SubElement(part, 'metadata', {
        'key': 'name',
        'value': model['name'],
    })

    # set filament color (in Orca/BambuStudio)
    if (model['color'] != ''):
        ET.SubElement(part, 'metadata', {
            'key': 'extruder',
            'value': model['extruder_color_idx'],
        })

    # we can omit rest of the metadata,
    # that's usually added upon saving 3MF directly in the slicer.

    return part

# create JSON config file: "./Metadata/project_settings.config"
def create_project_settings_stub(catalog_path, model_dict):
    repeat_count = len(model_dict.uniq_colors)

    # unused stub for the time being.
    # These settings are usually more specific and include things like filament config, nozzle temperature, bed temperature, fans speed, gcode snippets and more.
    # As the filament -> part assignment is correctly interpreted by the slicers without this config it's not needed now.

    # We can get away with this stub to at least pass Filament color w/ some stub data.
    # But then we'd have to overwrite these manually by selecting preset from a dropdown.
    # And the colors weren't always displaying as expected - for example OrcaSlicer loads the correct amount of filament and color; while BambuStudio tends to display previously used ones.

    project_settings_config__json = {
        # should match uniq_colors order
        "filament_colour": [
        ],

        ### default
        "fan_cooling_layer_time": [
            "80"
        ] * repeat_count,
        "fan_max_speed": [
            "80"
        ] * repeat_count,
        "fan_min_speed": [
            "60"
        ] * repeat_count,
        "filament_cost": [
            "20"
        ] * repeat_count,
        "filament_density": [
            "1.24"
        ] * repeat_count,
        "filament_deretraction_speed": [
            "nil"
        ] * repeat_count,
        "filament_diameter": [
            "1.75"
        ] * repeat_count,
        "filament_end_gcode": [
            "; filament end gcode \nM106 P3 S0\n"
        ] * repeat_count,
        "filament_flow_ratio": [
            "0.98"
        ] * repeat_count,
        "filament_ids": [
            "GFL99"
        ] * repeat_count,
        "filament_is_support": [
            "0"
        ] * repeat_count,
        "filament_long_retractions_when_cut": [
            "nil"
        ] * repeat_count,
        "filament_max_volumetric_speed": [
            "12"
        ] * repeat_count,
        "filament_minimal_purge_on_wipe_tower": [
            "15"
        ] * repeat_count,
        "filament_notes": "",
        "filament_retract_before_wipe": [
            "nil"
        ] * repeat_count,
        "filament_retract_restart_extra": [
            "nil"
        ] * repeat_count,
        "filament_retract_when_changing_layer": [
            "nil"
        ] * repeat_count,
        "filament_retraction_distances_when_cut": [
            "nil"
        ] * repeat_count,
        "filament_retraction_length": [
            "nil"
        ] * repeat_count,
        "filament_retraction_minimum_travel": [
            "nil"
        ] * repeat_count,
        "filament_retraction_speed": [
            "nil"
        ] * repeat_count,
        "filament_scarf_gap": [
            "15%"
        ] * repeat_count,
        "filament_scarf_height": [
            "10%"
        ] * repeat_count,
        "filament_scarf_length": [
            "10"
        ] * repeat_count,
        "filament_scarf_seam_type": [
            "none"
        ] * repeat_count,
        "filament_settings_id": [
            "Generic PLA @BBL A1"
        ] * repeat_count,
        "filament_shrink": [
            "100%"
        ] * repeat_count,
        "filament_soluble": [
            "0"
        ] * repeat_count,
        "filament_start_gcode": [
            "; filament start gcode\n{if  (bed_temperature[current_extruder] >45)||(bed_temperature_initial_layer[current_extruder] >45)}M106 P3 S255\n{elsif(bed_temperature[current_extruder] >35)||(bed_temperature_initial_layer[current_extruder] >35)}M106 P3 S180\n{endif};Prevent PLA from jamming\n\n\n{if activate_air_filtration[current_extruder] && support_air_filtration}\nM106 P3 S{during_print_exhaust_fan_speed_num[current_extruder]} \n{endif}"
        ] * repeat_count,
        "filament_type": [
            "PLA"
        ] * repeat_count,
        "filament_vendor": [
            "Generic"
        ] * repeat_count,
        "filament_wipe": [
            "nil"
        ] * repeat_count,
        "filament_wipe_distance": [
            "nil"
        ] * repeat_count,
        "filament_z_hop": [
            "nil"
        ] * repeat_count,
        "filament_z_hop_types": [
            "nil"
        ] * repeat_count
    }

    # just repeat stub values for every unique color used in 3MF file.
    for color in model_dict.uniq_colors:
        project_settings_config__json['filament_colour'].append(color)

    with open(join(catalog_path, "Metadata/project_settings.config"), "w") as file:
        json.dump(project_settings_config__json, file, indent=4)
