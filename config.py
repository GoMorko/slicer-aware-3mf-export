# Application Global Variables
# Adding application wide global variables here is a convenient technique
# It allows for access across multiple event handlers and modules

# Set to False to remove most log messages from text palette
import os

DEBUG = True

ADDIN_NAME = os.path.basename(os.path.dirname(__file__))

ADDIN_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

SOURCE_RESOURCES_FOLDER = os.path.join(ADDIN_ROOT_PATH, 'resources')
DIST_RESOURCES_FOLDER = os.path.join(ADDIN_ROOT_PATH, 'dist', 'resources')

COMPANY_NAME = 'WillowBranch'

design_workspace = 'FusionSolidEnvironment'
tools_tab_id = "ToolsTab"
my_tab_name = "test"  # Only used if creating a custom Tab

my_panel_id = f'{ADDIN_NAME}_panel_987'
my_panel_name = ADDIN_NAME
my_panel_after = ''
