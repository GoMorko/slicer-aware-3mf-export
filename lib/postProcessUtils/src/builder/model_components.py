from os.path import join
from uuid import uuid4
from itertools import chain

from ..utils.xml_utils import *
from ..common.models import ModelDict
from ..common.types import ObjectContext
from ..errors import BusinessException

__all__ = [
    'build_model_components',
]

def build_model_components(catalog_path: str) -> ModelDict:
    src_path = join(catalog_path, "3D/3dmodel.model")
    tree = ET.parse(src_path)
    root = tree.getroot()
    model_dict: ModelDict = ModelDict()

    process_3d_model(model_dict, root)
    create_components_groups(model_dict)
    build_components(model_dict, root)

    tree.write(src_path, xml_declaration=True, encoding='UTF-8')

    return model_dict

# extract data and update ./3D/3dmodel.model
def process_3d_model(model_dict: ModelDict, root):
    extract_color_info(root, model_dict)

    for object_element in root.findall('.//core:object', ns):
        object_name = str(object_element.get('name'))
        object_context = get_context_from_name(object_name)

        extract_object_info(object_element, object_context, model_dict)

        apply_basic_modifications(object_element, object_context)

def extract_color_info(root, model_dict: ModelDict):
    # In 3MF file exported from Fusion360 (in ./3D/3dmodel.model),
    # multiple objects with the same appearance will have their colors
    # show up multiple times as separate <colorgroup> linked to specific <object>
    #
    # The uniq_colors are needed to create extruder_color_idx
    #
    # When Fusion360 body has a single appearance attached, the <colorgroup> for that object will hold only a single element.
    for color_group in root.findall('.//material:colorgroup', ns):
        # <object pid="n">
        # <colorgroup id="n">
        # where "n" is the group_id
        group_id = color_group.get('id')
        model_dict.colors[group_id] = []

        for color in color_group.findall('material:color', ns):
            color_hex = color.get('color')

            # <object pindex="n"> where "n" will match the order in which color values show up in each <colorgroup>
            # eg. model_dict.colors[group_id][pindex] = color_hex
            model_dict.colors[group_id].append(color_hex)
            model_dict.uniq_colors.add(color_hex)

def extract_object_info(object_element, object_context: ObjectContext, model_dict: ModelDict):
    # <object id="1" name="ModelName" type="model" p:UUID="efe0e7c7-8a1e-4151-8da4-67c23539341b" pid="2" pindex="1">
    object_id = str(object_element.get('id'))
    # puuid = str(object_element.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID'))
    puuid = str(object_element.get('p:UUID'))
    pid = str(object_element.get('pid'))
    pindex = object_element.get('pindex')
    name = str(object_element.get('name'))
    object_color = model_dict.colors[pid][int(pindex)]

    model_dict.objects.append({
        'id': object_id,
        'name': name,
        'puuid': puuid,
        'pid': pid,
        'pindex': pindex,
        'color': object_color,
        # numeric id (starting from 1)
        'extruder_color_idx': str(model_dict.uniq_colors_ref().index(object_color) + 1),
        'component_name': object_context['component_name'],
        'type': object_context['type'],
        'name': object_context['name'],
    })

def get_context_from_name(name: str) -> ObjectContext:
    tokens = name.split('_')

    try:
        parent_name = tokens[0].lstrip('$')
        object_type = tokens[2]
        object_name = ' '.join(tokens[3:])

        return {
            "component_name": parent_name,
            "type": object_type,
            "name": object_name
        }
    except Exception as err:
        raise BusinessException(f'Unable to parse object name into context: "{name}"\n\nOriginal message: "{err}"\n')

def apply_basic_modifications(object_element, object_context: ObjectContext):
    # remove attributes slicer usually removes on file save
    object_element.attrib.pop('name', None)
    object_element.attrib.pop('pid', None)
    object_element.attrib.pop('pindex', None)

    if object_context['type'] != 'MAIN':
        # all sub types are denoted as "other"
        # the specific info on model parts sub types are stored in ./Metadata/model_settings.config
        object_element.set('type', 'other')

"""
# example:
model_dict.components = {
    '$CompA': {
        'main': ObjectModel,
        'sub_types': {
            'MOD': [ ObjectModel, ObjectModel, ... ],
            'NEG': [ ... ],
            'PART': [ ... ],
            ...
        },
    },.
    '$CompB': { ... },
}
"""
def create_components_groups(model_dict: ModelDict):
    components = model_dict.components

    for obj in model_dict.objects:
        type_name = obj['type']
        component_name = obj['component_name']

        if component_name not in components:
            components[component_name] = {
                'main': {},
                'sub_types': {},
                'wrapping_component': {
                    'id': str(uuid4()),
                    'type': 'model',
                    'namespace': component_name,
                    'name': obj['name'],
                }
            }

        component_objects_group = components[component_name]

        if type_name == 'MAIN':
            component_objects_group['main'] = obj

        else:
            if type_name not in component_objects_group['sub_types']:
                component_objects_group['sub_types'][type_name] = []

            component_objects_group['sub_types'][type_name].append(obj)

    for component_name, component_objects_group in components.items():
        if not bool(component_objects_group['main']):
          raise BusinessException(f'Missing MAIN object for component_objects_group {component_name} - did you forget to name one body "${component_name}__MAIN_(...)"?')

# Now we create a new (virtual) object with <components> list where each <component> refers to one <object>
# Then this one (virtal) object will be placed under <build> as printable <item>
#
# This basically replicates what saving 3MF file in slicer does to its internal structure.
# With some simplifications, like applying all above changes in the same 3dmodel.model file,
# rather than creating new set of separate files:
#   - "./3D/Objects/object_{n}.model" (.model per each object)
#   - "./3D/rels/3dmodel.model.rels" (.rels to atttach 3dmodel schema relantionship to those objects)
def build_components(model_dict: ModelDict, root):
    resources = root.find('core:resources', ns)
    build = root.find('core:build', ns)

    # clear the <build> from original object items
    for item in build.findall('core:item', ns):
        build.remove(item)

    for component_name, component_objects_group in model_dict.components.items():
        id = component_objects_group['wrapping_component']['id']
        main_object = component_objects_group['main']

        obj = ET.SubElement(resources, 'object', {
            'id': id,
            'p:UUID': str(uuid4()),
            'type': 'model',
        })

        components = ET.SubElement(obj, 'components')

        # add main object as component
        ET.SubElement(components, 'component', {
            'objectid': main_object['id'],
            'p:UUID': str(uuid4()),
            # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
        })

        # add all sub types object as components
        for sub_object in list(chain.from_iterable(component_objects_group['sub_types'].values())):
            ET.SubElement(components, 'component', {
                'objectid': sub_object['id'],
                'p:UUID': str(uuid4()),
                # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
            })

        # make newly created components object a build item
        ET.SubElement(build, 'item', {
            'objectid': id,
            'p:UUID': str(uuid4()),
            'printable': '1',
            # 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'
        })
