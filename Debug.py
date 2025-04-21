# Debug.py - Script para lanzar PrintSplitterTaskPanel manualmente

import sys
import os
import FreeCAD
import FreeCADGui
import traceback
import importlib # Necesario para recargar módulos

print("\n--- Iniciando script Debug.py ---")

# --- Configuración ---
# ASUNCIÓN: La carpeta 'PrintSplitterAddon' con el código más reciente
# (incluyendo __init__.py) está directamente dentro de tu carpeta Mod:
# /home/dgmtnz/.local/share/FreeCAD/Mod/PrintSplitterAddon/
#
# FreeCAD debería encontrarlo automáticamente si está ahí y si se reinició
# después de copiar los archivos.
# --- Fin Configuración ---

# Nombre completo del módulo del panel
panel_module_name = "PrintSplitterAddon.PrintSplitterTaskPanel"

try:
    # --- Recargar Módulos (¡Importante para desarrollo!) ---
    # Intenta recargar el módulo del panel si ya fue importado en esta sesión de FreeCAD.
    # Esto asegura que se usa la última versión del código CADA VEZ que ejecutas el script.
    if panel_module_name in sys.modules:
        print(f"Recargando módulo existente: {panel_module_name}")
        # Recargamos el módulo específico del panel
        module_obj = importlib.reload(sys.modules[panel_module_name])
        # También podríamos recargar el paquete base si fuera necesario
        # if "PrintSplitterAddon" in sys.modules:
        #    importlib.reload(sys.modules["PrintSplitterAddon"])
    else:
        print(f"Importando módulo por primera vez: {panel_module_name}")
        # Si no estaba cargado, lo importamos normalmente la primera vez
        module_obj = __import__(panel_module_name, fromlist=["PrintSplitterTaskPanel"])

    # Obtenemos la clase DESPUÉS de importar/recargar
    PrintSplitterTaskPanel = module_obj.PrintSplitterTaskPanel
    print("Clase PrintSplitterTaskPanel lista.")

    # --- Preparación y Lanzamiento del Panel ---
    print("Obteniendo selección...")
    sel = FreeCADGui.Selection.getSelection()

    if not sel:
        msg = "ERROR: Por favor, selecciona un objeto sólido en la vista 3D antes de ejecutar este script."
        print(msg)
        # Opcional: Mostrar mensaje emergente
        # from PySide import QtGui
        # QtGui.QMessageBox.warning(None, "Selección Requerida", msg)

    elif len(sel) > 1:
        msg = f"ERROR: Has seleccionado {len(sel)} objetos. Por favor, selecciona solo uno."
        print(msg)

    elif not hasattr(sel[0], "Shape") or not sel[0].Shape or sel[0].Shape.isNull():
        msg = f"ERROR: El objeto seleccionado '{sel[0].Label}' no tiene una geometría (Shape) válida o está vacío."
        print(msg)

    else:
        selected_object = sel[0]
        print(f"Objeto seleccionado válido: {selected_object.Label}")

        # Crear instancia del panel
        print("Creando instancia del panel...")
        panel_instance = PrintSplitterTaskPanel(selected_object)
        print("Instancia creada.")

        # Mostrar el panel usando showDialog (método correcto para Task Panels)
        print("Mostrando el panel (usando showDialog)...")
        FreeCADGui.Control.showDialog(panel_instance)
        print("Llamada a showDialog() completada. ¿Apareció el panel?")

except ImportError as ie:
    print(f"\nERROR DE IMPORTACIÓN: {ie}")
    print(f"No se pudo importar '{panel_module_name}'.")
    print("Verifica:")
    print("  1. Que la carpeta 'PrintSplitterAddon' está en '/home/dgmtnz/.local/share/FreeCAD/Mod/'.")
    print("  2. Que esa carpeta contiene un archivo '__init__.py' (puede estar vacío).")
    print("  3. Que el archivo 'PrintSplitterTaskPanel.py' existe dentro y no tiene errores de sintaxis.")
    print("  4. Que reiniciaste FreeCAD después de copiar los archivos.")
    traceback.print_exc()
except AttributeError as ae:
     print(f"\nERROR DE ATRIBUTO: {ae}")
     print("Esto suele indicar un problema en el código del panel (PrintSplitterTaskPanel.py) o un objeto incorrecto.")
     traceback.print_exc()
except Exception as e:
    print(f"\nERROR INESPERADO: {e}")
    traceback.print_exc()

print("\n--- Script Debug.py finalizado ---")