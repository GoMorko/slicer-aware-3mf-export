import os
import json
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
import time
from pathlib import (PurePath)
from uuid import uuid4
import shutil
import argparse

ET.register_namespace('', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
ET.register_namespace('m', 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02')
ET.register_namespace('p', 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06')

ns = {
    'core': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02',
    'material': 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02',
    'production': 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06',
}

types_to_parts = {
    'MAIN': 'normal_part',
    'MOD': 'modifier_part',
    'NEG': 'negative_part',
}

##############
##############
##############


def translate_type_to_part(type_name):
    part_name = types_to_parts.get(type_name)
    if part_name == None:
        part_name = 'normal_part'

    return part_name

def create_part_in_config(model):
    part = ET.Element('part', {
        'id': model['id'],
        'subtype': translate_type_to_part(model['type']),
    })

    ET.SubElement(part, 'metadata', {
        'key': 'name',
        'value': model['name'],
    })

    if (model['color'] != ''):
        ET.SubElement(part, 'metadata', {
            'key': 'extruder',
            'value': model['extruder_color_idx'],
        })

    return part

def create_model_settings(catalog_path, model_dict):
    config_root = ET.Element('config')

    for key, value in model_dict['groups'].items():
        main_obj = value['main']
        wrapping_component = value['wrappingComponent']

        object = ET.SubElement(config_root, 'object', {
            'id': wrapping_component['id'],
        })

        ET.SubElement(object, 'metadata', {
            'key': 'name',
            'value': f"{wrapping_component['namespace']}_{wrapping_component['name']}"
        })

        object.append(create_part_in_config(main_obj))

        for sub_types in value['sub_types'].items():
            for sub_type in sub_types[1]:
                object.append(create_part_in_config(sub_type))

    tree = ET.ElementTree(config_root)

    with open (os.path.join(catalog_path, "Metadata/model_settings.config"), "wb") as file:
        tree.write(file, xml_declaration=True, encoding='UTF-8')

def create_project_settings_stub(catalog_path, model_dict):
    repeat_count = len(model_dict['uniq_colors'])

    project_settings_config__json = {
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

    for color in model_dict['uniq_colors']:
        project_settings_config__json['filament_colour'].append(color)

    with open(os.path.join(catalog_path, "Metadata/project_settings.config"), "w") as file:
        json.dump(project_settings_config__json, file, indent=4)

def create_settings(catalog_path, model_dict):
    create_model_settings(catalog_path, model_dict)
    # create_project_settings_stub(catalog_path, model_dict)

def create_components(catalog_path, model_dict):
    src_path = os.path.join(catalog_path, "3D/3dmodel.model")
    tree = ET.parse(src_path)
    root = tree.getroot()

    resources = root.find('core:resources', ns)

    for key, value in model_dict['groups'].items():
        id = str(uuid4())
        main_obj = value['main']
        value['wrappingComponent'] = {
            'id': id,
            'type': 'model',
            'namespace': key,
            'name': main_obj['name'],
        }

        obj = ET.SubElement(resources, 'object', {
            'id': id,
            '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID': str(uuid4()),
            'type': 'model',
        })

        components = ET.SubElement(obj, 'components')

        ET.SubElement(components, 'component', {
            'objectid': main_obj['id'],
            '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID': str(uuid4()),
            # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
        })

        for sub_types in value['sub_types'].items():
            for sub_type in sub_types[1]:
                ET.SubElement(components, 'component', {
                    'objectid': sub_type['id'],
                    '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID': str(uuid4()),
                    # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
                })

        build = root.find('core:build', ns)
        for item in build.findall('core:item', ns):
            build.remove(item)

        ET.SubElement(build, 'item', {
            'objectid': id,
            '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID': str(uuid4()),
            'printable': '1',
            # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
        })

        tree.write(src_path, xml_declaration=True, encoding='UTF-8')
        # tree.write(os.path.join(catalog_path, "3D/_0_3dmodel.xml"), xml_declaration=True, encoding='UTF-8')

    return model_dict

def group_objects(model_dict):
    grouped_objects = {}

    for obj in model_dict['objects']:
        component = obj['component']
        type_name = obj['type']

        if component not in grouped_objects:
            grouped_objects[component] = {'main': {}, 'sub_types': {}}

        if type_name == 'MAIN':
            grouped_objects[component]['main'] = obj
        else:
            if type_name not in grouped_objects[component]['sub_types']:
                grouped_objects[component]['sub_types'][type_name] = []
            grouped_objects[component]['sub_types'][type_name].append(obj)

    model_dict['groups'] = grouped_objects

    return model_dict

def parse_name_to_meta(name):
    tokens = name.split('_')

    component = tokens[0].lstrip('$')
    type_ = tokens[2]
    name = ' '.join(tokens[3:])

    return {
        "component": component,
        "type": type_,
        "name": name
    }

def process_3d_model(catalog_path):
    src_path = os.path.join(catalog_path, "3D/3dmodel.model")
    tree = ET.parse(src_path)
    root = tree.getroot()

    model_dict = {
        'colors': {},
        'uniq_colors': [],
        'objects': [],
    }

    for color_group in root.findall('.//material:colorgroup', ns):
        group_id = color_group.get('id')
        model_dict['colors'][group_id] = []

        for color in color_group.findall('material:color', ns):
            model_dict['colors'][group_id].append(color.get('color'))

    seen_colors = set()
    for group_colors in model_dict['colors'].values():
        for color in group_colors:
            if color not in seen_colors:
                seen_colors.add(color)
                model_dict['uniq_colors'].append(color)

    for object in root.findall('.//core:object', ns):
        # <object id="1" name="WetInsert" type="model" p:UUID="efe0e7c7-8a1e-4151-8da4-67c23539341b" pid="2" pindex="1">
        id = str(object.get('id'))
        puuid = str(object.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID'))
        pid = str(object.get('pid'))
        pindex = object.get('pindex')
        name = str(object.get('name'))

        name_meta = parse_name_to_meta(name)

        model_dict['objects'].append({
            'id': id,
            'name': name,
            'puuid': puuid,
            'pid': pid,
            'pindex': pindex,
            'color': model_dict['colors'][pid][int(pindex)],
            'extruder_color_idx': str(model_dict['uniq_colors'].index(model_dict['colors'][pid][int(pindex)]) + 1),
            'component': name_meta['component'],
            'type': name_meta['type'],
            'name': name_meta['name'],
        })

        object.attrib.pop('name', None)
        object.attrib.pop('pid', None)
        object.attrib.pop('pindex', None)

        if name_meta['type'] != 'MAIN':
            object.set('type', 'other')

    tree.write(src_path, xml_declaration=True, encoding='UTF-8')
    # tree.write(os.path.join(catalog_path, "3D/_0_3dmodel.xml"), xml_declaration=True, encoding='UTF-8')

    return model_dict

def process_extracted(catalog_path):
    model_dict = process_3d_model(catalog_path)
    model_dict = group_objects(model_dict)
    create_components(catalog_path, model_dict)
    create_settings(catalog_path, model_dict)

    print(model_dict)

def extract(file_path):
    with ZipFile(file_path, 'r') as zObject:
        ppath = PurePath(file_path)
        extract_path = os.path.join(ppath.parent, f"{ppath.stem}")
        zObject.extractall(path=extract_path)

        return extract_path

def zip_extracted_as_3mf(catalog_path):
    ppath = PurePath(catalog_path)
    zip_file_path = os.path.join(ppath.parent, f"{ppath.stem}_processed.3mf")

    with ZipFile(zip_file_path, 'w', ZIP_DEFLATED, strict_timestamps=False) as zipf:
        for root, _, files in os.walk(catalog_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, catalog_path)
                zipf.write(file_path, arcname)

def remove_unpacked_folder(catalog_path):
    shutil.rmtree(catalog_path)

def main():
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('input_path', type=str, help='Path to the input 3MF file')
    args = parser.parse_args()

    process_file(args.input_path)

def process_file(path):
    catalog_path = extract(path)
    process_extracted(catalog_path)

    zip_extracted_as_3mf(catalog_path)

    remove_unpacked_folder(catalog_path)

if __name__ == "__main__":
    main()
