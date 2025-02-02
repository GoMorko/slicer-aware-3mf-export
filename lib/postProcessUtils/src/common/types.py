from typing import Dict, List, Set, Tuple, Literal, NotRequired, TypedDict

class ObjectContext(TypedDict): {
    "component_name": str,
    "type": str,
    "name": str,
}

class ObjectModel(TypedDict): {
    'id': str,
    'name': str,
    'puuid': str,
    'pid': str,
    'pindex': str,
    'color': str,
    'extruder_color_idx': str,
    'component': str,
    'type': str,
    'name': str,
}

class WrappingComponent(TypedDict): {
    'id': str,
    'type': str,
    'namespace': str,
    'name': str,
}

class ComponentObjectsGroup(TypedDict): {
    'main': ObjectModel,
    'sub_types': Dict[str, List[ObjectModel]],
    'wrapping_component': WrappingComponent,
}
