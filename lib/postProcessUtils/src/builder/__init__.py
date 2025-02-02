from .model_components import *
from .slicer_settings import *

__all__ = [
    'rebuild_files',
]

def rebuild_files(catalog_path: str):
    model_dict = build_model_components(catalog_path)
    create_model_settings(catalog_path, model_dict)
