# https://forums.autodesk.com/t5/fusion-api-and-scripts/accessing-appearance-thumbnails/m-p/10592886/highlight/true#M14219

import adsk.core
import adsk.fusion
import adsk.cam
import traceback

import os
import re
import io
import zipfile
import pathlib
import shutil

from ...dist.packages.PIL import Image

MAIN_RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources')

def getFavoritesAdsklibPath() -> list:
    app: adsk.core.Application = adsk.core.Application.get()

    materialPath = pathlib.Path(
        app.executeTextCommand(f'Materials.MaterialLibraryPath'))

    return os.path.join(materialPath, 'Favorites.adsklib')

def createIcon(zipPath: str, basePath: str):
    iconPaths = {}

    with zipfile.ZipFile(zipPath) as myzip:
        # get png file path
        paths = [f for f in myzip.namelist() if re.search('._png', f) != None]

        for path in paths:
            # open Byte stream
            with myzip.open(path) as img_file:
                img_bin = io.BytesIO(img_file.read())
                img = Image.open(img_bin)

                # get  material id
                path = pathlib.Path(path)
                id = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', str(path.parts[2]))
                iconPath = os.path.join(basePath, id)

                # resize
                for width, height in [(32, 32), (16, 16)]:
                    # create icon folder
                    pathlib.Path(iconPath).mkdir(parents=True, exist_ok=True)

                    savePath = os.path.join(iconPath, f'{width}x{height}.png')

                    clone = img.copy()
                    img_resize_lanczos = clone.resize(
                        (width, height), Image.LANCZOS)

                    # save png
                    img_resize_lanczos.save(str(savePath))

                iconPaths[id] = str(iconPath)

    return iconPaths
