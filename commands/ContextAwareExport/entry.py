import adsk.core, adsk.fusion, traceback
import os
from ...lib import fusionAddInUtils as futil
from ...lib import postProcessUtils as pputil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
design = adsk.fusion.Design.cast(app.activeProduct)

units = design.unitsManager.defaultLengthUnits

CMD_NAME = os.path.basename(os.path.dirname(__file__))
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_{CMD_NAME}'
CMD_Description = 'Export selected component as 3MF and apply post processing scripts - to convert specific objects into special types interpretable by slicer.'
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

# Holds references to event handlers
local_handlers = []

selectedExportPath = futil.get_default_upload_directory()
defaultExportFileName = '_exports'

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

# Function to be called when a user clicks the corresponding button in the UI.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    inputs = args.command.commandInputs

    prepare_widget_view(inputs)

# This function will be called when the user clicks the OK button in the command dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs

    execute_export(inputs)

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
    export_tab_view(inputs)

def export_tab_view(parent_inputs: adsk.core.CommandInputs):
    # export_tab = parent_inputs.addTabCommandInput('export_tab', 'Export')
    # inputs = export_tab.children
    inputs = parent_inputs

    ### Export tab view

    ## Select export folder trigger button
    button_icons = os.path.join(ICON_FOLDER, 'buttons')

    inputs.addBoolValueInput('export_folder_button', 'Export to', False, button_icons)

    # export_folder_button = inputs.addButtonRowCommandInput('export_folder_button', 'Export to', True)
    # export_folder_button_list_items = export_folder_button.listItems
    # export_folder_button_list_items.add('Choose Export Folder', False, button_icons)

    ## Export folder selector field
    export_folder = inputs.addTextBoxCommandInput('export_folder', '', selectedExportPath, 1, True)
    export_folder.isFullWidth = True
    export_folder.isEnabled = False

    ## Exported model filename field
    file_name_string_value = inputs.addStringValueInput('file_name_string_value', 'Filename', defaultExportFileName)

    inputs.addSeparatorCommandInput('separator_2')

    ## Select objects to be exported
    export_selections = inputs.addSelectionInput('export_selections', 'Selected Component', '')

    export_selections.addSelectionFilter('SolidBodies')
    export_selections.addSelectionFilter('Occurrences')
    # export_selections.addSelectionFilter('RootComponents')

    export_selections.setSelectionLimits(1, 1)

    inputs.addSeparatorCommandInput('separator_3')

    ### Mesh Refinement settings
    refinement_group = inputs.addGroupCommandInput('refinement_group', 'Refinement Settings')
    refinement_group.isExpanded = False
    refinement_inputs = refinement_group.children

    ## Refinement settings preset
    refinement_dropdown = refinement_inputs.addDropDownCommandInput('refinement_dropdown', 'Refinement', adsk.core.DropDownStyles.TextListDropDownStyle)

    refinement_items = refinement_dropdown.listItems
    refinement_items.add('High', True)
    refinement_items.add('Medium', False)
    refinement_items.add('Low', False)

################
## BEHAVIOR
################

def execute_export(inputs: adsk.core.CommandInputs):
    export_mgr = futil.get_export_manager(app)

    export_selections = inputs.itemById('export_selections')
    file_name_string_value = inputs.itemById('file_name_string_value')

    selected_entity = export_selections.selection(0).entity
    output_path = f'{selectedExportPath}\\{file_name_string_value.value}'

    export_options = export_mgr.createC3MFExportOptions(selected_entity, output_path)

    export_options.sendToPrintUtility = False
    export_options.isOneFilePerBody = False
    export_options.meshRefinement = get_refinement_option_value(inputs)

    isExportSuccess = export_mgr.execute(export_options)

    if (isExportSuccess):
        try:
            pputil.process_file(f'{output_path}.3mf')
        except Exception as err:
            if config.DEBUG:
                raise err
            ui.messageBox(f'Error:\n"{err}"\n\n---------Trace:\n\n{traceback.format_exc()}')

################
## UTILS
################

def get_refinement_option_value(inputs: adsk.core.CommandInputs):
    refinement_group = inputs.itemById('refinement_group')
    refinement_inputs = refinement_group.children
    refinement_dropdown = refinement_inputs.itemById('refinement_dropdown')

    refinement_value = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh

    match refinement_dropdown.selectedItem.name:
        case 'High':
            refinement_value = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        case 'Medium':
            refinement_value = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
        case 'Low':
            refinement_value = adsk.fusion.MeshRefinementSettings.MeshRefinementLow

    return refinement_value

################
## LISTENERS
################

def handle_input_changed(changed_input: adsk.core.CommandInput, inputs: adsk.core.CommandInputs):
    if changed_input.id == 'export_selections':
        on_change_export_selections(inputs)

    if changed_input.id == 'export_folder_button':
        on_change_export_button(inputs)

def on_change_export_selections(inputs: adsk.core.CommandInputs):
    selectionInput = inputs.itemById('export_selections')
    selection = selectionInput.selection(0)
    if (not selection):
        return

    file_name_string_value = inputs.itemById('file_name_string_value')
    file_name_string_value.value = futil.get_file_name(selection.entity)

def on_change_export_button(inputs: adsk.core.CommandInputs):
    folder_dlg = ui.createFolderDialog()
    folder_dlg.title = 'Select export folder'

    dlg_result = folder_dlg.showDialog()
    if dlg_result == adsk.core.DialogResults.DialogOK:
        global selectedExportPath
        export_folder = inputs.itemById('export_folder')

        export_folder.text = folder_dlg.folder
        selectedExportPath = folder_dlg.folder
