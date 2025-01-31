import os
import sys
import subprocess
import pathlib
from config import *

def mkdir_deps():
    deps_paths = [
        os.path.join(ADDIN_ROOT_PATH, 'dist'),
        os.path.join(ADDIN_ROOT_PATH, 'dist/packages'),
        DIST_RESOURCES_FOLDER,
    ]

    for path in deps_paths:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def install_requirements():
    target_dir = os.path.join(ADDIN_ROOT_PATH, 'dist/packages')

    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--target", target_dir, "-r", "requirements.txt"
    ])

if __name__ == "__main__":
    mkdir_deps()
    install_requirements()
