from os import walk
from os.path import join, relpath

from zipfile import ZipFile, ZIP_DEFLATED

__all__ = [
    "extract",
    "archive",
]

def extract(catalog_path: str, file_path_zip: str):
    with ZipFile(file_path_zip, 'r') as zip_file:
        zip_file.extractall(path=catalog_path)

def archive(catalog_path: str, file_path_3mf: str):
    with ZipFile(file_path_3mf, 'w', ZIP_DEFLATED, strict_timestamps=False) as zip_file:
        for sub_catalog, _, files in walk(catalog_path):
            for file in files:
                file_path = join(sub_catalog, file)
                arcname = relpath(file_path, catalog_path)

                zip_file.write(file_path, arcname)
