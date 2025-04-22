# PrintSplitterAddon/InitGui.py

import FreeCAD
import FreeCADGui

# Importa el módulo donde definirás el comando y la lógica principal
# Use a relative import if PrintSplitter.py is in the same directory
# REMOVED: from . import PrintSplitter

class PrintSplitterWorkbench (FreeCADGui.Workbench):
    """
    Define el Workbench personalizado para PrintSplitter.
    """
    MenuText = "PrintSplitter"
    ToolTip = "Tools for splitting objects for 3D printing"
    # Provide a path to your icon file.
    # Using Qt resource path (requires compiling resources) or direct path.
    # Example direct path (adjust relative path if needed):
    Icon = "icons/print_splitter_icon.svg"
    # If the icon is in the same directory as InitGui.py:
    # import os
    # Icon = os.path.join(os.path.dirname(__file__), "print_splitter_icon.svg")

    def Initialize(self):
        """
        Se llama cuando el workbench se activa por primera vez.
        Crea los comandos, menús y barras de herramientas.
        """
        FreeCAD.Console.PrintMessage("Initializing PrintSplitter Workbench UI...\n")

        # Importa el comando definido en PrintSplitter.py
        # REMOVED: from .PrintSplitter import PrintSplitterCommand

        # Lista de nombres de comandos (strings)
        self.list = ["PrintSplitter_Command"]

        # Crea una instancia del comando
        import PrintSplitter # ADDED
        cmd = PrintSplitter.PrintSplitterCommand() # MODIFIED

        # Añade el comando a FreeCAD con su nombre
        FreeCADGui.addCommand('PrintSplitter_Command', cmd)

        # Crea la barra de herramientas
        # El segundo argumento debe ser la lista de nombres de comandos (strings)
        self.toolbar = self.appendToolbar("Print Splitting Tools", self.list)

        # Crea el menú
        # El segundo argumento debe ser la lista de nombres de comandos (strings)
        self.menu = self.appendMenu(self.MenuText, self.list)

        FreeCAD.Console.PrintMessage("PrintSplitter Workbench UI initialized.\n")

    def Activated(self):
        """ Se llama cuando el usuario cambia a este workbench """
        FreeCAD.Console.PrintMessage("PrintSplitter Workbench activated.\n")

    def Deactivated(self):
        """ Se llama cuando el usuario cambia a otro workbench """
        FreeCAD.Console.PrintMessage("PrintSplitter Workbench deactivated.\n")

# Registra el workbench en FreeCAD
# Ensure this code runs only once
if not hasattr(FreeCADGui, "PrintSplitterWorkbenchInstance"): # Check if already added
    FreeCADGui.addWorkbench(PrintSplitterWorkbench)
    FreeCADGui.PrintSplitterWorkbenchInstance = True # Mark as added
    print("PrintSplitter GUI initialized (Workbench registered).")
else:
    print("PrintSplitter GUI already initialized.") 