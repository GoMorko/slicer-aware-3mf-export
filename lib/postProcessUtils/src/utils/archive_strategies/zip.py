from subprocess import run

from ...... import config

__all__ = [
    "extract",
    "archive",
]

def extract(catalog_path: str, file_path_zip: str):
    run_command(extract_cmd(catalog_path, file_path_zip))

def archive(catalog_path: str, file_path_3mf: str):
    run_command(archive_cmd(catalog_path, file_path_3mf))

def extract_cmd(catalog_path: str, file_path_zip: str):
    return f'unzip {file_path_zip} -d {catalog_path}';

def archive_cmd(catalog_path: str, file_path_3mf: str):
    return f'cd {catalog_path} && zip {file_path_3mf} .';

def run_command(command: str):
    process = run([
        command.replace('\n', ''),
    ], capture_output=config.DEBUG, text=config.DEBUG, check=not config.DEBUG, shell=True)

    if config.DEBUG:
        print(f'    [shell][unzip][stdout]: {process.stdout}')
        print(f'    [shell][unzip][stderr]: {process.stderr}')
