# PrintSplitterAddon/PrintSplitter.py

import FreeCAD
import FreeCADGui
import Part # Needed for checking object type
from PySide import QtGui, QtCore # Needed for messages and translation

# Import the task panel class using direct import
from PrintSplitterTaskPanel import PrintSplitterTaskPanel

class PrintSplitterCommand:
    """
    Defines the command that gets activated from the menu or toolbar.
    It checks the selection and opens the task panel.
    """
    def GetResources(self):
        """ Returns command resources (icon, text) """
        # Use QT_TRANSLATE_NOOP for potential internationalization
        # Ensure the icon path matches the one in InitGui.py or is correct
        return {
            'Pixmap': 'icons/print_splitter_icon.svg',
            'MenuText': QtCore.QT_TRANSLATE_NOOP("PrintSplitterCommand", "Split Object for Printing..."),
            'ToolTip': QtCore.QT_TRANSLATE_NOOP("PrintSplitterCommand", "Opens the Print Splitter tool to divide the selected object based on printer volume and add connectors.")
        }

    def Activated(self):
        """ Executed when the command is clicked """
        FreeCAD.Console.PrintMessage("PrintSplitter Command Activated\n")

        # 1. Check Selection
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            msg = "Please select exactly one solid object to split."
            FreeCAD.Console.PrintError(msg + "\n")
            QtGui.QMessageBox.warning(None, "Selection Error", msg)
            return

        if len(selection) > 1:
            msg = "Please select only one solid object."
            FreeCAD.Console.PrintError(msg + "\n")
            QtGui.QMessageBox.warning(None, "Selection Error", msg)
            return

        selected_obj = selection[0]

        # 2. Check Object Type (must be a Part::Feature or similar with a valid Shape)
        if not hasattr(selected_obj, "Shape") or not isinstance(selected_obj.Shape, Part.Shape):
             msg = f"Selected object '{selected_obj.Label}' is not a valid Part object."
             FreeCAD.Console.PrintError(msg + "\n")
             QtGui.QMessageBox.warning(None,"Selection Error", msg)
             return

        # 3. Check if the Shape is valid (not Null, has volume for solids)
        try:
            if selected_obj.Shape.isNull():
                msg = f"Selected object '{selected_obj.Label}' has invalid geometry (Shape is Null)."
                FreeCAD.Console.PrintError(msg + "\n")
                QtGui.QMessageBox.warning(None,"Selection Error", msg)
                return
            # Optional: Check if it's a solid (might allow splitting shells later?)
            if not isinstance(selected_obj.Shape, Part.Solid):
                 # For now, only support solids
                 # We could check for CompSolid or Shell here if needed
                 if isinstance(selected_obj.Shape, Part.Compound):
                      # Allow compounds if they contain at least one solid?
                      if not any(isinstance(s, Part.Solid) for s in selected_obj.Shape.Solids):
                           raise TypeError("Compound does not contain solids")
                 else:
                      raise TypeError("Shape is not a Solid")
            # Check volume as a basic validity check for solids
            if selected_obj.Shape.Volume < 1e-9:
                 msg = f"Selected object '{selected_obj.Label}' has zero or negligible volume."
                 FreeCAD.Console.PrintWarning(msg + "\n") # Warning instead of error?
                 # QtGui.QMessageBox.warning(None,"Selection Error", msg)
                 # return # Allow processing zero volume solids? Maybe not.
                 # Let's treat it as an error for splitting
                 raise ValueError("Shape has zero volume")

        except Exception as e:
            msg = f"Selected object '{selected_obj.Label}' has invalid or unsupported geometry type ({e})."
            FreeCAD.Console.PrintError(msg + "\n")
            QtGui.QMessageBox.warning(None,"Selection Error", msg)
            return

        # 4. Create and show the task panel, passing the selected object
        try:
            # Keep track of the panel instance if needed, otherwise just show
            panel = PrintSplitterTaskPanel(selected_obj)
            panel.show() # Use the show method defined in the panel class
            # FreeCADGui.Control.showDialog(panel) # Older method, createDialog is preferred
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create or show the Task Panel: {e}\n")
            import traceback
            traceback.print_exc()
            QtGui.QMessageBox.critical(None, "Error", "Could not open the PrintSplitter panel.")

    def IsActive(self):
        """ Defines when the command is active (clickable) """
        # Active if there is an open document
        return FreeCAD.ActiveDocument is not None

# Command registration is typically done in InitGui.py
# Do not register it here unless InitGui.py doesn't exist or isn't used. 