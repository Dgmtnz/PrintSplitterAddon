# PrintSplitter

PrintSplitter es un Addon (complemento) de código abierto para FreeCAD diseñado para dividir modelos 3D grandes en partes más pequeñas que se ajusten al volumen de impresión de tu impresora 3D.

## Descripción

PrintSplitter permite a los usuarios tomar un objeto sólido grande dentro de FreeCAD y dividirlo automáticamente en múltiples piezas basándose en las dimensiones (ancho, profundidad, alto) de una impresora 3D específica. El objetivo es facilitar la impresión de modelos que exceden el volumen de construcción disponible.

### Características principales:
- Integración como Workbench (Entorno de Trabajo) en FreeCAD.
- División de objetos sólidos basada en las dimensiones X, Y, Z de la impresora proporcionadas.
- Interfaz de usuario (Panel de Tareas) para introducir las dimensiones y seleccionar el objeto.
- Cálculo automático de las herramientas de corte necesarias.
- Creación de nuevos objetos `Part::Feature` para cada pieza resultante.
- Agrupación de los resultados y ocultación del objeto original.
- **Funcionalidad de Conectores (EN DESARROLLO):** El código incluye lógica para intentar añadir conectores (pines/agujeros) entre las piezas cortadas. **Actualmente, esta funcionalidad no está operativa y los conectores no se añaden correctamente a las piezas finales.** Mejorar y arreglar esta característica es la principal prioridad de desarrollo pendiente.

## Capturas de pantalla

*(Se añadirán capturas de pantalla del workbench y del panel de tareas)*

<table>
  <tr>
    <td>[Interfaz del Workbench - Próximamente]</td>
    <td>[Panel de Tareas - Próximamente]</td>
    <td>[Ejemplo de Corte - Próximamente]</td>
  </tr>
</table>

## Requisitos

- FreeCAD (Probado en versión 1.0, podría funcionar en otras versiones)
- Python 3 (Normalmente incluido con FreeCAD)

## Instalación

La instalación actualmente es manual:

1.  Localiza tu directorio `Mod` de FreeCAD. Puedes encontrar la ruta base escribiendo `App.getUserAppDataDir()` en la consola de Python de FreeCAD. El directorio `Mod` suele estar dentro de esa ruta (p. ej., `~/.local/share/FreeCAD/Mod` en Linux, `%APPDATA%\\FreeCAD\\Mod` en Windows).
2.  Clona este repositorio o descarga el código fuente.
3.  Copia la carpeta completa `PrintSplitterAddon` (con todos sus archivos `.py`, `package.xml` y la subcarpeta `icons`) dentro de tu directorio `Mod`.
4.  **Importante:** Elimina cualquier subcarpeta `__pycache__` que pueda existir dentro de `PrintSplitterAddon` si has ejecutado versiones anteriores.
5.  Reinicia FreeCAD. El workbench "PrintSplitter" debería aparecer en el menú desplegable de entornos de trabajo.

## Uso

1.  Inicia FreeCAD.
2.  Selecciona el entorno de trabajo "PrintSplitter" en el menú desplegable.
3.  Selecciona el objeto sólido que deseas dividir en la vista de árbol o en la vista 3D.
4.  Haz clic en el botón "Split Object for Printing..." en la barra de herramientas (el icono es un cubo siendo cortado).
5.  Aparecerá el panel de tareas "Print Splitter Settings".
6.  Introduce las dimensiones máximas (Ancho X, Profundidad Y, Alto Z) de tu impresora en milímetros.
7.  La casilla "Connector Options" está presente pero **actualmente no tiene efecto funcional** ya que la lógica de conectores no está finalizada. Puedes dejarla marcada o desmarcada.
8.  Haz clic en el botón "Split Object".
9.  El proceso de corte se ejecutará. Revisa la "Vista de informe" de FreeCAD para ver mensajes de progreso y posibles errores.
10. Si el corte tiene éxito, el objeto original se ocultará y aparecerá un nuevo grupo en la vista de árbol (ej: `TuObjeto_SplitResult`) conteniendo las piezas resultantes.

## Licencia

Este proyecto se ha creado de manera Open-Source bajo la licencia GPL v3 (Licencia Pública General de GNU v3). Puedes copiar, modificar y distribuir el código, siempre y cuando mantengas la misma licencia y hagas públicos cualquier cambio que realices. *(Nota: Se debe añadir un archivo LICENSE formal al repositorio).*

## Soporte

Si tienes algún problema, encuentras errores (especialmente con diferentes tipos de geometrías) o tienes sugerencias para mejorar PrintSplitter (¡sobre todo para la funcionalidad de conectores!), no dudes en abrir un 'issue' en este repositorio (si aplica) o contactar al desarrollador.

## Créditos

-   Este proyecto ha sido desarrollado por Diego Martínez Fernández (@Dgmtnz)
-   Construido utilizando la API de Python de FreeCAD.

Gracias por probar PrintSplitter. ¡Esperamos que la funcionalidad de división sea útil y que los conectores automáticos puedan implementarse pronto!
