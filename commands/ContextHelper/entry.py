import adsk.core, adsk.fusion, traceback
import os
import shutil
from ...lib import fusionAddInUtils as futil
from ...lib import postProcessUtils as pputil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = os.path.basename(os.path.dirname(__file__))
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_{CMD_NAME}'
CMD_Description = 'Shortcut actions applying structured context aware names to bodies.'
IS_PROMOTED = False

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

DIST_RESOURCES_FOLDER = config.DIST_RESOURCES_FOLDER
SOURCE_RESOURCES_FOLDER = config.SOURCE_RESOURCES_FOLDER

APPEARANCE_LIB_VERSION = 'v1'
APPEARANCE_LIB_NAME = f'ContextAwareSlicerAppearance_{APPEARANCE_LIB_VERSION}'
APPEARANCE_LIB_ICONS_FILENAME = f'{APPEARANCE_LIB_NAME}.json'

FAVORITES_LIB_NAME = 'Favorites Library'
FAVORITES_ICONS_FILENAME = f'{FAVORITES_LIB_NAME}.json'

OBJECT_TYPES = [
    'MAIN',
    'PART',
    'MODIFIER',
    'NEGATIVE',
]

# Holds references to event handlers
local_handlers = []

use_appearance = True
parts_appearance_settings = {
    'MAIN': {
        'id': None,
        'use_appearance': False,
    },
    'PART': {
        'id': None,
        'use_appearance': True,
    },
    'MODIFIER': {
        'id': None,
        'use_appearance': True,
    },
    'NEGATIVE': {
        'id': None,
        'use_appearance': True,
    },
}

class ModEntityStack:
    def __init__(self):
        self._entities = {}

    def append(self, entity, entity_tuple):
        self._entities[entity.entityToken] = entity_tuple

    def remove(self, entity):
        if self._entities.get(entity.entityToken):
            del self._entities[entity.entityToken]

    def clear(self):
        self._entities.clear()

    def get_stack(self):
        return list(self._entities.values())

mod_entities_stack = ModEntityStack()

################
## BOILERPLATE
################

# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******************************** Create Command Control ********************************
    # Get target workspace for the command.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get target panel for the command and and create the panel if necessary.
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    # Create the command control, i.e. a button in the UI.
    control = panel.controls.addCommand(cmd_def)

    # Now you can set various options on the control such as promoting it to always be shown.
    control.isPromoted = IS_PROMOTED

    try:
        load_plugin_materials()
    except Exception as err:
        unload_plugin_materials()
        raise err

# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the panel if it is empty
    if panel.controls.count == 0:
        panel.deleteMe()

    # Delete the tab if it is empty
    if toolbar_tab.toolbarPanels.count == 0:
        toolbar_tab.deleteMe()

    if config.F__UNLOAD_PLUGIN_MATERIAL_LIBRARY_ON_STOP:
        unload_plugin_materials()

# Function to be called when a user clicks the corresponding button in the UI.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    global mod_entities_stack

    futil.log(f'{CMD_NAME} Command Created Event')

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_execute_preview, local_handlers=local_handlers)

    inputs = args.command.commandInputs

    mod_entities_stack.clear()

    prepare_widget_view(inputs)

# This function will be called when the user clicks the OK button in the command dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs

    apply_context_to_bodies()

    save_plugin_settings()

def command_execute_preview(args: adsk.core.CommandEventArgs):
    apply_context_to_bodies()

# This function will be called when the user changes anything in the command dialog.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {args.input.id}')

    changed_input = args.input
    inputs = args.inputs

    handle_input_changed(changed_input, inputs)

# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers

    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

################
## VIEW
################

def prepare_widget_view(inputs: adsk.core.CommandInputs):
    helpers_tab(inputs)
    appearance_settings_tab(inputs)

def helpers_tab(parent_inputs: adsk.core.CommandInputs):
    ### Helpers tab view
    inputs = parent_inputs.addTabCommandInput('helpers_tab', 'Helpers').children

    ## Select objects to be renamed
    mod_selections = inputs.addSelectionInput('mod_selections', 'Select Body', '')

    mod_selections.addSelectionFilter('SolidBodies')

    mod_selections.setSelectionLimits(0, 0)

    ## separator
    inputs.addSeparatorCommandInput('helpers_separator_1')

    ## Select export folder trigger button
    mod_buttons_icons = os.path.join(ICON_FOLDER, 'mod_buttons')

    mod_body_buttons = inputs.addButtonRowCommandInput('mod_body_buttons', 'Change Selected to:', True)
    mod_body_buttons_list_items = mod_body_buttons.listItems

    for o_type in OBJECT_TYPES:
        mod_body_buttons_list_items.add(o_type, False, os.path.join(mod_buttons_icons, o_type.lower()))

    mod_body_buttons_list_items.add('Reset Body', False, os.path.join(mod_buttons_icons, '_reset'))

    ## Should apply configured appearance for each type of body (based on parts_appearance_settings)
    inputs.addBoolValueInput('use_appearance', 'Apply Appearance', True, '', use_appearance)

def appearance_settings_tab(parent_inputs: adsk.core.CommandInputs):
    ### Helpers tab view
    inputs = parent_inputs.addTabCommandInput('appearance_settings_tab', 'Appearance').children

    ## table definition and style
    table = inputs.addTableCommandInput('appearance_table', 'Appearances', 6, '2:1:3')

    table.minimumVisibleRows = 3
    table.maximumVisibleRows = 6
    table.columnSpacing = 1
    table.rowSpacing = 3
    table.tablePresentationStyle = adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
    table.hasGrid = False

    # get reference to plugin materials that should have had loaded during plugin boot.
    a_m = get_plugin_materials()

    a_lib = a_m.get('a_lib')
    a_icons_dict = a_m.get('a_icons_dict', {})
    f_lib = a_m.get('f_lib')
    f_icons_dict = a_m.get('f_icons_dict', {})

    ## make the first headers row
    table_headers = [
        'Type',
        'Use',
        'Appearance',
    ]
    for [h_i, header_name] in enumerate(table_headers):
        table.addCommandInput(inputs.addTextBoxCommandInput(f'header_{header_name}', header_name, header_name.capitalize(), 1, True), 0, h_i, 0, 0)

    ## under each header, populate appearance selection for every object type
    i = len(table_headers)
    for o_type in OBJECT_TYPES:
        material_row_title = inputs.addTextBoxCommandInput(f'material_row_title_{o_type}', o_type, o_type.capitalize(), 1, True)
        material_drop_down = inputs.addDropDownCommandInput(f'material_drop_down_{o_type}', '', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
        material_should_apply = inputs.addBoolValueInput(f'use_material_appearance_{o_type}', 'Use Appearance', True, '', parts_appearance_settings[o_type].get('use_appearance', False))

        types_current_appearance_id = parts_appearance_settings.get(o_type, {}).get('id', None)

        material_drop_down.listItems.add('---', False)

        for aIdx in range(a_lib.appearances.count):
            a = a_lib.appearances.item(aIdx)
            is_selected = types_current_appearance_id == a.id
            material_drop_down.listItems.add(a.name, is_selected, a_icons_dict.get(a.id, ''))

        material_drop_down.listItems.add('---', False)

        for fIdx in range(a_lib.appearances.count):
            try:
                f = f_lib.appearances.item(fIdx)
                is_selected = types_current_appearance_id == f.id
                material_drop_down.listItems.add(f.name, is_selected, f_icons_dict.get(f.id, ''))
            except:
                pass

        table.addCommandInput(material_row_title, i, 0, 0, 0)
        table.addCommandInput(material_drop_down, i, 2, 0, 0)
        table.addCommandInput(material_should_apply, i, 1, 0, 0)

        i += 2

################
## BEHAVIOR
################

def add_context_to_bodies(mod_selections: adsk.core.SelectionCommandInput, object_type: str):
    global mod_entities_stack
    m_libs = get_plugin_materials().get('libs', [])

    for s_idx in range(mod_selections.selectionCount):
        selection = mod_selections.selection(s_idx)
        entity = selection.entity

        parent_name = entity.parentComponent.name
        obj_name = entity.name

        new_name = to_context_aware_format(parent_name, get_shorthand_object_type(object_type), obj_name)
        new_appearance = None

        a_id = parts_appearance_settings.get(object_type, {}).get('id')
        a_use = parts_appearance_settings.get(object_type, {}).get('use_appearance')
        if a_id and a_use and use_appearance:
            new_appearance = find_appearance_in_material_libraries(a_id, m_libs)

        mod_entities_stack.append(entity, [entity, new_name, new_appearance])

    mod_selections.clearSelection()

def apply_context_to_bodies():
    for [entity, name, appearance] in mod_entities_stack.get_stack():
        entity.name = name

        if appearance:
            entity.appearance = appearance

def clear_context_from_stack(mod_selections: adsk.core.SelectionCommandInput):
    global mod_entities_stack

    for s_idx in range(mod_selections.selectionCount):
        selection = mod_selections.selection(s_idx)
        entity = selection.entity

        mod_entities_stack.remove(entity)

    mod_selections.clearSelection()

def load_plugin_settings(a_lib: adsk.core.MaterialLibrary):
    global parts_appearance_settings
    parts_settings_json_path = os.path.join(DIST_RESOURCES_FOLDER, 'parts_appearance_settings.json')

    try:
        parts_appearance_settings = futil.open_json_to_dict(parts_settings_json_path)

        return
    except:
        pass

    for aIdx in range(a_lib.appearances.count):
        a = a_lib.appearances.item(aIdx)
        appearance_name = (a.name.split('_', 1))[0]

        default_setting = parts_appearance_settings.get(appearance_name)
        if default_setting:
            default_setting['id'] = a.id

    save_plugin_settings()

def save_plugin_settings():
    global parts_appearance_settings
    parts_settings_json_path = os.path.join(DIST_RESOURCES_FOLDER, 'parts_appearance_settings.json')

    futil.dump_to_json(parts_appearance_settings, parts_settings_json_path)

def load_plugin_materials():
    a_lib = app.materialLibraries.itemByName(APPEARANCE_LIB_NAME)
    f_lib = app.materialLibraries.itemByName(FAVORITES_LIB_NAME)

    a_icons_json_path = os.path.join(DIST_RESOURCES_FOLDER, f'{APPEARANCE_LIB_ICONS_FILENAME}')
    f_icons_json_path = os.path.join(DIST_RESOURCES_FOLDER, f'{FAVORITES_ICONS_FILENAME}')

    if a_lib:
        a_icons_dict = futil.open_json_to_dict(a_icons_json_path)
        f_icons_dict = futil.open_json_to_dict(f_icons_json_path)

        load_plugin_settings(a_lib)

        return {
            'a_lib': a_lib,
            'a_icons_dict': a_icons_dict,
            'f_lib': app.materialLibraries.itemByName(FAVORITES_LIB_NAME),
            'f_icons_dict': f_icons_dict,
        }

    a_lib_path = os.path.join(SOURCE_RESOURCES_FOLDER, f'{APPEARANCE_LIB_NAME}.adsklib')

    a_lib = app.materialLibraries.load(a_lib_path)

    a_icons_path = os.path.join(DIST_RESOURCES_FOLDER, f'{APPEARANCE_LIB_NAME}')
    a_icons_dict = futil.createIcon(a_lib_path, a_icons_path)

    f_icons_path = os.path.join(DIST_RESOURCES_FOLDER, f'{FAVORITES_LIB_NAME}')
    f_icons_dict = futil.createIcon(futil.getFavoritesAdsklibPath(), f_icons_path)

    futil.dump_to_json(a_icons_dict, a_icons_json_path)
    futil.dump_to_json(f_icons_dict, f_icons_json_path)

    load_plugin_settings(a_lib)

def get_plugin_materials() -> list[adsk.core.MaterialLibrary]:
    a_lib = app.materialLibraries.itemByName(APPEARANCE_LIB_NAME)
    f_lib = app.materialLibraries.itemByName(FAVORITES_LIB_NAME)

    a_icons_json_path = os.path.join(DIST_RESOURCES_FOLDER, f'{APPEARANCE_LIB_ICONS_FILENAME}')
    f_icons_json_path = os.path.join(DIST_RESOURCES_FOLDER, f'{FAVORITES_ICONS_FILENAME}')

    a_icons_dict = futil.open_json_to_dict(a_icons_json_path)
    f_icons_dict = futil.open_json_to_dict(f_icons_json_path)

    return {
        'a_lib': a_lib,
        'a_icons_dict': a_icons_dict,
        'f_lib': app.materialLibraries.itemByName(FAVORITES_LIB_NAME),
        'f_icons_dict': f_icons_dict,
        'libs': [
            a_lib,
            f_lib,
        ]
    }

def unload_plugin_materials():
    app.materialLibraries.itemByName(APPEARANCE_LIB_NAME).unload()

    a_icons_path = os.path.join(DIST_RESOURCES_FOLDER, f'{APPEARANCE_LIB_NAME}')
    f_icons_path = os.path.join(DIST_RESOURCES_FOLDER, f'{FAVORITES_LIB_NAME}')

    shutil.rmtree(a_icons_path, ignore_errors=True)
    shutil.rmtree(f_icons_path, ignore_errors=True)

################
## UTILS
################

def to_context_aware_format(parent_name: str, obj_type: str, obj_name: str):
    acronym_parent = futil.create_acronym(parent_name)
    context_prefix = f'${acronym_parent}__{obj_type}_'

    if obj_name.startswith(f'${acronym_parent}'):
        obj_name = next(iter(obj_name.split('_')[::-1]), obj_name)

    return f'{context_prefix}{obj_name}'

def get_shorthand_object_type(o_type: str):
    # MAIN
    # PART
    # MODIFIER
    # NEGATIVE

    match(o_type):
        case 'MODIFIER':
            return 'MOD'
        case 'NEGATIVE':
            return 'NEG'

    return o_type

def find_appearance_in_material_libraries(id: str, m_libs: list[adsk.core.MaterialLibrary]):
    for lib in m_libs:
        a = lib.appearances.itemById(id)
        if a:
            return a

################
## LISTENERS
################

def handle_input_changed(changed_input: adsk.core.CommandInput, inputs: adsk.core.CommandInputs):
    if changed_input.id == 'mod_body_buttons':
        on_change_mod_body_buttons(inputs)

    if changed_input.id == 'use_appearance':
        on_change_use_appearance(inputs)

    if changed_input.id.startswith('use_material_appearance'):
        on_change_use_material_appearance(inputs, changed_input)

    if changed_input.id.startswith('material_drop_down'):
        on_change_material_appearance_drop_down(inputs, changed_input)

def on_change_mod_body_buttons(inputs: adsk.core.CommandInputs):
    btn = futil.get_selected_button_and_deselect(inputs.itemById('mod_body_buttons'))
    mod_selections: adsk.core.SelectionCommandInput = inputs.itemById('mod_selections')

    if not mod_selections.selectionCount:
        return

    if btn.name == 'Reset Body':
        clear_context_from_stack(mod_selections)
        return

    add_context_to_bodies(mod_selections, btn.name)

def on_change_use_appearance(inputs: adsk.core.CommandInputs):
    global use_appearance
    checkbox: adsk.core.BoolValueCommandInput = inputs.itemById('use_appearance')

    use_appearance = checkbox.value

def on_change_use_material_appearance(inputs: adsk.core.CommandInputs, changed_input: adsk.core.CommandInput):
    global parts_appearance_settings

    object_type = changed_input.id.split('use_material_appearance_')[1]

    type_setting = parts_appearance_settings.get(object_type)
    if type_setting:
        type_setting['use_appearance'] = changed_input.value

def on_change_material_appearance_drop_down(inputs: adsk.core.CommandInputs, changed_input: adsk.core.CommandInput):
    global parts_appearance_settings

    object_type = changed_input.id.split('material_drop_down_')[1]

    type_setting = parts_appearance_settings.get(object_type)
    if type_setting:
        if changed_input.selectedItem.name == '---' or not changed_input.selectedItem.icon:
            type_setting['id'] = None
            # disable use material checkbox next to the "changed_input" drop down
            inputs.itemById('appearance_table').parentCommandInput.commandInputs.itemById(f'use_material_appearance_{object_type}').value = False
            return

        # this is incredibly silly; but we can't assign name and value independently to a drop down item(?).
        # gotta keep using appearance id as catalog name.
        type_setting['id'] = os.path.split(changed_input.selectedItem.icon)[1]
