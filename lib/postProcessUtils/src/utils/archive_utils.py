import platform
from re import findall
from time import time
from os.path import join
from pathlib import PurePath

from ..... import config
from ..errors import BusinessException
from .archive_strategies import Zip, ZipFile, Powershell

__all__ = [
    'extract_from_archive',
    'archive_as_3mf',
]

SYSTEM_PLATFORM = platform.system().lower()
IS_WINDOWS = SYSTEM_PLATFORM == 'windows'
IS_UNIX_LIKE = SYSTEM_PLATFORM in ['linux', 'darwin']

def extract_from_archive(file_path_zip: str) -> str:
    ppath = PurePath(file_path_zip)
    if ppath.suffix not in ['.3mf', '.zip']:
        raise BusinessException(f'Unknown file extension, got: "{ppath.suffix}"')

    invalid_filename = ppath.stem.strip() == '' or len(findall(r'(\.|\/|\\)', ppath.stem))
    if invalid_filename:
        ppath = PurePath(str(join(ppath.parent, f'export_{int(time())}.3mf')))

    catalog_path = str(join(ppath.parent, ppath.stem))

    do_extract(catalog_path, file_path_zip)

    return catalog_path

def do_extract(catalog_path: str, file_path_zip: str):
    try:
        if IS_WINDOWS:
            return Powershell.extract(catalog_path, file_path_zip)
        elif IS_UNIX_LIKE:
            return Zip.extract(catalog_path, file_path_zip)

        raise BusinessException(f'OS "{SYSTEM_PLATFORM}" extraction strategy not implemented. Falling back to ZipFile.')

    except BusinessException as err:
        if config.DEBUG:
            raise err

        return ZipFile.extract(catalog_path, file_path_zip)

def archive_as_3mf(catalog_path: str) -> str:
    ppath = PurePath(catalog_path)
    file_path_3mf = str(join(ppath.parent, f'{ppath.stem}_processed.3mf'))

    do_archive(catalog_path, file_path_3mf)

    return file_path_3mf

def do_archive(catalog_path: str, file_path_3mf: str):
    try:
        if IS_WINDOWS:
            return Powershell.archive(catalog_path, file_path_3mf)
        elif IS_UNIX_LIKE:
            return Zip.archive(catalog_path, file_path_3mf)

        raise BusinessException(f'OS "{SYSTEM_PLATFORM}" archiving strategy not implemented. Falling back to ZipFile.')

    except BusinessException as err:
        if config.DEBUG:
            raise err

        return ZipFile.archive(catalog_path, file_path_3mf)
