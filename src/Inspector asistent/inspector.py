#este sera el asistente que inspeccionara el proyecto y analizara los errores que hay en el mismo para asi poder dar un diagnostico de los mismos y poder corregirlos de manera eficiente y rapida
import os
import sys
sys.dont_write_bytecode = True

def inspeccionar_proyecto():
    # Verificar si el proyecto tiene errores de sintaxis
    errores_sintaxis = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                ruta_archivo = os.path.join(root, file)
                try:
                    with open(ruta_archivo, "r", encoding="utf-8") as f:
                        contenido = f.read()
                    compile(contenido, ruta_archivo, "exec")
                except SyntaxError as e:
                    errores_sintaxis.append((ruta_archivo, e))

    # Verificar si el proyecto tiene errores de importación
    errores_importacion = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                ruta_archivo = os.path.join(root, file)
                try:
                    with open(ruta_archivo, "r", encoding="utf-8") as f:
                        contenido = f.read()
                    exec(contenido, {})
                except ImportError as e:
                    errores_importacion.append((ruta_archivo, e))

    # Generar un informe de los errores encontrados
    informe_errores = ""
    if errores_sintaxis:
        informe_errores += "Errores de sintaxis:\n"
        for archivo, error in errores_sintaxis:
            informe_errores += f"- {archivo}: {error}\n"
    else:
        informe_errores += "No se encontraron errores de sintaxis.\n"

    if errores_importacion:
        informe_errores += "\nErrores de importación:\n"
        for archivo, error in errores_importacion:
            informe_errores += f"- {archivo}: {error}\n"
    else:
        informe_errores += "\nNo se encontraron errores de importación.\n"

    return informe_errores

informe = inspeccionar_proyecto()