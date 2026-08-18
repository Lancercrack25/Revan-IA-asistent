import os
import ast
from src.Inspector_asistent.graphic_generator import (
    registrar_nuevo_escaneo, 
    generar_grafica_telemetria_inspector
)

def escanear_archivo_python(ruta_archivo: str) -> tuple[int, int]:
    errores = 0
    warnings = 0

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        # Comprobar sintaxis
        try:
            tree = ast.parse(contenido)
        except SyntaxError:
            errores += 1
            return errores, warnings
        # Análisis ligero de advertencias (ej. funciones demasiado largas o bloques try vacíos)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                warnings += 1  # except genérico sin especificar la excepción
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) > 50:
                    warnings += 1  # Función demasiado extensa (deuda técnica)
    except Exception:
        errores += 1
    return errores, warnings

def ejecutar_inspeccion_proyecto(ruta_proyecto: str = None) -> str:
    if not ruta_proyecto or not os.path.exists(ruta_proyecto):
        # Si no se pasa ruta, se analiza el directorio raíz del proyecto
        ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    print(f"[INSPECTOR]: Iniciando escaneo en: {ruta_proyecto}...")
    total_errores = 0
    total_warnings = 0
    archivos_analizados = 0
    # Recorrer árbol de carpetas ignorando directorios de entorno virtual o git
    carpetas_ignorar = {'.git', '__pycache__', 'venv', '.venv', 'env'}
    for root, dirs, files in os.walk(ruta_proyecto):
        dirs[:] = [d for d in dirs if d not in carpetas_ignorar]
        for file in files:
            if file.endswith('.py'):
                ruta_completa = os.path.join(root, file)
                e, w = escanear_archivo_python(ruta_completa)
                total_errores += e
                total_warnings += w
                archivos_analizados += 1
    print(f"[INSPECTOR]: Escaneo finalizado ({archivos_analizados} archivos .py). Errores: {total_errores} | Warnings: {total_warnings}")
    # 1. Registrar el resultado en la base de datos JSON local
    historial = registrar_nuevo_escaneo(errores=total_errores, warnings=total_warnings)
    # 2. Desplegar la gráfica de telemetría de líneas en segundo plano
    generar_grafica_telemetria_inspector(
        historico_labels=historial["labels"],
        historico_errores=historial["errores"],
        historico_warnings=historial["warnings"],
        mostrar_pantalla=True,
        en_segundo_plano=True
    )

    return f"Inspección completada en {archivos_analizados} módulos. Detectados {total_errores} errores y {total_warnings} advertencias."

if __name__ == "__main__":
    # Prueba de escaneo directo sobre el proyecto
    resultado = ejecutar_inspeccion_proyecto()
    print(resultado)