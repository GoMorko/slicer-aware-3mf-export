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
    # Define any dynamic vars here.
    # Using f-string for command results in need for werid backslash escapement.
    # This way script is basically same as one ran manually in cli.
    command = f"""
$zipFilePath = '{file_path_zip}';
$filesDirectory = '{catalog_path}';
"""

    # NOTE: only use block comments "<# some_comment #>"
    # otherwise after replace or split and join lists, the lines following single line comment are ignored.
    command += r"""
if (-not (Test-Path $filesDirectory)) {
    New-Item -ItemType Directory -Path $filesDirectory;
};

Add-Type -Assembly 'System.IO.Compression.FileSystem';

[System.IO.Compression.ZipFile]::ExtractToDirectory($zipFilePath, $filesDirectory);
"""

    return command

def archive_cmd(catalog_path: str, file_path_3mf: str):
    command = f"""
$zipFilePath = '{file_path_3mf}';
$filesDirectory = '{catalog_path}';
"""

    command += r"""
Add-Type -Assembly 'System.IO.Compression.FileSystem';
Remove-Item -Path $zipFilePath -ErrorAction SilentlyContinue;

$zip = [System.IO.Compression.ZipFile]::Open($zipFilePath, 'create');
$compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal;
$replaceFilesDirectory = "^$([regex]::Escape($filesDirectory))\\?";

Get-ChildItem -File -Recurse $filesDirectory | ForEach-Object {
    $relativeLeafPath = $_.FullName -replace $replaceFilesDirectory, "";
    $relativeLeafPath = $relativeLeafPath -replace "\\", "/";
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $relativeLeafPath, $compressionLevel);
};

$zip.Dispose();
"""

    return command

def run_command(command: str):
    process = run([
        'powershell', '-ExecutionPolicy', 'Bypass', '-Command',
        command.replace('\n', ''),
    ], capture_output=config.DEBUG, text=config.DEBUG, check=not config.DEBUG, shell=True)

    if config.DEBUG:
        print(f'    [powershell][zip][stdout]: {process.stdout}')
        print(f'    [powershell][zip][stderr]: {process.stderr}')
