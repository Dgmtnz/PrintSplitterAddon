# PrintSplitterAddon/Init.py
import FreeCAD # Make sure FreeCAD module is accessible

def init():
    """
    Este archivo se ejecuta cuando FreeCAD carga el módulo,
    incluso en modo consola sin GUI.
    """
    # Check if running in GUI mode before printing GUI-related messages
    if FreeCAD.GuiUp:
        FreeCAD.Console.PrintMessage("Initializing PrintSplitter Addon (GUI mode)...\n")
    else:
        FreeCAD.Console.PrintMessage("Initializing PrintSplitter Addon (Console mode)...\n")

# init() # Generally not called directly here for addons loaded by Addon Manager

# Optional: Define paths or variables needed by other modules
# import os
# ADDON_PATH = os.path.dirname(__file__) 