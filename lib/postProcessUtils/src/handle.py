import shutil
import argparse

from .builder import rebuild_files
from .utils import extract_from_archive, archive_as_3mf

# as cli command
def main():
    parser = argparse.ArgumentParser(description='Process 3d models from a 3MF file into context aware, sub typed objects understood by some slicers (OrcaSlicer, BambuStudio).')
    parser.add_argument('input_path', type=str, help='Path to the input 3MF file')
    args = parser.parse_args()

    process_file(args.input_path)

# as function
def process_file(path: str):
    catalog_path = extract_from_archive(path)

    rebuild_files(catalog_path)

    archive_as_3mf(catalog_path)

    shutil.rmtree(catalog_path)

if __name__ == "__main__":
    main()
