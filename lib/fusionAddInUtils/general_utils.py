#  Copyright 2022 by Autodesk, Inc.
#  Permission to use, copy, modify, and distribute this software in object code form
#  for any purpose and without fee is hereby granted, provided that the above copyright
#  notice appears in all copies and that both that copyright notice and the limited
#  warranty and restricted rights notice below appear in all supporting documentation.
#
#  AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS. AUTODESK SPECIFICALLY
#  DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE.
#  AUTODESK, INC. DOES NOT WARRANT THAT THE OPERATION OF THE PROGRAM WILL BE
#  UNINTERRUPTED OR ERROR FREE.

import adsk.core, adsk.fusion
import traceback
import os
import re
import json
import platform
from pathlib import Path
from functools import reduce

app = adsk.core.Application.get()
ui = app.userInterface

# Attempt to read DEBUG flag from parent config.
try:
    from ... import config
    DEBUG = config.DEBUG
except:
    DEBUG = False


def log(message: str, level: adsk.core.LogLevels = adsk.core.LogLevels.InfoLogLevel, force_console: bool = False):
    """Utility function to easily handle logging in your app.

    Arguments:
    message -- The message to log.
    level -- The logging severity level.
    force_console -- Forces the message to be written to the Text Command window.
    """
    # Always print to console, only seen through IDE.
    print(message)

    # Log all errors to Fusion log file.
    if level == adsk.core.LogLevels.ErrorLogLevel:
        log_type = adsk.core.LogTypes.FileLogType
        app.log(message, level, log_type)

    # If config.DEBUG is True write all log messages to the console.
    if DEBUG or force_console:
        log_type = adsk.core.LogTypes.ConsoleLogType
        app.log(message, level, log_type)


def handle_error(name: str, show_message_box: bool = False):
    """Utility function to simplify error handling.

    Arguments:
    name -- A name used to label the error.
    show_message_box -- Indicates if the error should be shown in the message box.
                        If False, it will only be shown in the Text Command window
                        and logged to the log file.
    """

    log('===== Error =====', adsk.core.LogLevels.ErrorLogLevel)
    log(f'{name}\n{traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)

    # If desired you could show an error as a message box.
    if show_message_box:
        ui.messageBox(f'{name}\n{traceback.format_exc()}')

def get_export_manager(app):
    # get active design
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    return design.exportManager

def get_file_name(selectedEntity):
    fileName = selectedEntity.name

    if type(selectedEntity) == adsk.fusion.Component:
        fileName = selectedEntity.name
    if type(selectedEntity) == adsk.fusion.BRepBody:
        fileName = f"{selectedEntity.parentComponent.name}__{selectedEntity.name}"

    return sanitize_filename(fileName)

def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\']', '', filename)
    sanitized = sanitized.strip().replace(' ', '_')

    return sanitized

def get_default_upload_directory() -> str:
    # Try to infer a suitable directory
    system = platform.system()
    if system == "Windows":
        # Use the user's Downloads folder
        upload_dir = Path(os.getenv("USERPROFILE", Path.home())) / "Downloads"
    elif system == "Darwin":  # macOS
        # Use the Downloads folder on macOS
        upload_dir = Path.home() / "Downloads"
    else:  # Assume Linux or other Unix-like OS
        # Use ~/Downloads if it exists, else fallback to ~/Documents
        possible_dir = Path.home() / "Downloads"
        upload_dir = possible_dir if possible_dir.exists() else Path.home() / "Documents"

    # Ensure the directory exists
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir)

def get_selected_button(buttons_row: adsk.core.ButtonRowCommandInput):
    return next(iter(list(filter(lambda x: x.isSelected, buttons_row.listItems))))

def get_selected_button_and_deselect(buttons_row: adsk.core.ButtonRowCommandInput):
    btn = get_selected_button(buttons_row)
    if btn:
        btn.isSelected = False

    return btn

def dump_to_json(dict: dict, path: str):
    with open(path, 'w') as outfile:
        json.dump(dict, outfile)

def open_json_to_dict(path: str):
    with open(path, 'r') as infile:
        return json.loads(infile.read())

def create_acronym(phrase: str):
    words = re.split(r'[;,\._\-\s]+', phrase)

    return reduce(lambda x, y: f'{x}{y[0].upper()}', [''] + words)
