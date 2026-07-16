#este sera el asistente que inspeccionara el proyecto y analizara los errores que hay en el mismo para asi poder dar un diagnostico de los mismos y poder corregirlos de manera eficiente y rapida
import os
import sys

sys.dont_write_bytecode = True

def inspeccionar_proyecto():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_proyecto = os.path.abspath(os.path.join(ruta_actual, "../.."))  # Subimos dos niveles para llegar a la raíz del proyecto

    errores = []

    for root, dirs, files in os.walk(ruta_proyecto):
        for file in files:
            if file.endswith(".py"):
                ruta_archivo = os.path.join(root, file)
                try:
                    with open(ruta_archivo, "r", encoding="utf-8") as f:
                        contenido = f.read()
                        # Aquí podrías agregar análisis más complejos, como buscar patrones de errores comunes
                except Exception as e:
                    errores.append(f"Error al leer {ruta_archivo}: {str(e)}")

    if errores:
        print("Se encontraron los siguientes errores durante la inspección del proyecto:")
        for error in errores:
            print(error)
    else:
        print("No se encontraron errores durante la inspección del proyecto.")