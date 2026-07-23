#este sera el asistente que inspeccionara el proyecto y analizara los errores que hay en el mismo para asi poder dar un diagnostico de los mismos y poder corregirlos de manera eficiente y rapida
import os
import sys
import ast

sys.dont_write_bytecode = True
try:
    from pyflakes.api import check as pyflakes_check
    from pyflakes.reporter import Reporter
    HAS_PYFLAKES = True
except ImportError:
    HAS_PYFLAKES = False

# Carpetas que se ignoran siempre en la inspección (no son código propio del proyecto)
CARPETAS_IGNORADAS = {
    ".git", "__pycache__", "venv", ".venv", "env",
    "node_modules", "site-packages", "test", "tests",
}

def _listar_archivos_py(ruta_proyecto):
    for root, dirs, files in os.walk(ruta_proyecto):
        dirs[:] = [d for d in dirs if d not in CARPETAS_IGNORADAS]
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)

def _revisar_sintaxis(ruta_archivo, contenido):
    """Detecta errores de sintaxis (el proyecto ni siquiera podría arrancar con esto)."""
    try:
        ast.parse(contenido, filename=ruta_archivo)
        return None
    except SyntaxError as e:
        return f"SINTAXIS: línea {e.lineno}: {e.msg}"

def _revisar_pyflakes(ruta_archivo):
    if not HAS_PYFLAKES:
        return []

    class _CapturaReporter(Reporter):
        def __init__(self):
            self.mensajes = []
        def flake(self, message):
            self.mensajes.append(str(message))
        def syntaxError(self, filename, msg, lineno, offset, text):
            pass 
        def unexpectedError(self, filename, msg):
            self.mensajes.append(f"pyflakes error interno: {msg}")

    reporter = _CapturaReporter()
    with open(ruta_archivo, "r", encoding="utf-8", errors="replace") as f:
        codigo = f.read()
    pyflakes_check(codigo, ruta_archivo, reporter)
    return reporter.mensajes


def _extraer_nombres_definidos(ruta_archivo):
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="replace") as f:
            arbol = ast.parse(f.read(), filename=ruta_archivo)
    except SyntaxError:
        return None  # el propio archivo ya tiene error de sintaxis, se reporta aparte

    nombres = set()
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nombres.add(nodo.name)
        elif isinstance(nodo, ast.Assign):
            for target in nodo.targets:
                if isinstance(target, ast.Name):
                    nombres.add(target.id)
        elif isinstance(nodo, ast.ImportFrom) or isinstance(nodo, ast.Import):
            # Re-exportados: si el archivo importa algo y otro archivo lo
            # vuelve a importar de aquí, también cuenta como "existe".
            for alias in nodo.names:
                nombres.add(alias.asname or alias.name)
    return nombres

def _revisar_imports_locales(ruta_archivo, contenido, ruta_proyecto):
    problemas = []
    try:
        arbol = ast.parse(contenido, filename=ruta_archivo)
    except SyntaxError:
        return problemas  # ya se reporta en _revisar_sintaxis

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.startswith("src."):
            ruta_modulo = os.path.join(ruta_proyecto, *nodo.module.split(".")) + ".py"

            if not os.path.exists(ruta_modulo):
                problemas.append(
                    f"IMPORT ROTO: 'from {nodo.module} import ...' -> "
                    f"no existe el archivo {os.path.relpath(ruta_modulo, ruta_proyecto)}"
                )
                continue

            nombres_definidos = _extraer_nombres_definidos(ruta_modulo)
            if nombres_definidos is None:
                continue 

            for alias in nodo.names:
                nombre_buscado = alias.name
                if nombre_buscado != "*" and nombre_buscado not in nombres_definidos:
                    problemas.append(
                        f"IMPORT ROTO: 'from {nodo.module} import {nombre_buscado}' -> "
                        f"'{nombre_buscado}' no está definido en {os.path.relpath(ruta_modulo, ruta_proyecto)}"
                    )

    return problemas

def inspeccionar_proyecto(ruta_proyecto: str = None, verboso: bool = True) -> dict:
    if ruta_proyecto is None:
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_proyecto = os.path.abspath(os.path.join(ruta_actual, "..", ".."))

    resultado = {
        "archivos_revisados": 0,
        "errores_sintaxis": [],
        "imports_rotos": [],
        "avisos_pyflakes": [],
        "errores_lectura": [],
    }

    for ruta_archivo in _listar_archivos_py(ruta_proyecto):
        resultado["archivos_revisados"] += 1
        rel = os.path.relpath(ruta_archivo, ruta_proyecto)

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                contenido = f.read()
        except Exception as e:
            resultado["errores_lectura"].append((rel, str(e)))
            continue

        err_sintaxis = _revisar_sintaxis(ruta_archivo, contenido)
        if err_sintaxis:
            resultado["errores_sintaxis"].append((rel, err_sintaxis))
            continue  # si hay error de sintaxis, no tiene caso seguir analizando este archivo

        for problema in _revisar_imports_locales(ruta_archivo, contenido, ruta_proyecto):
            resultado["imports_rotos"].append((rel, problema))

        for aviso in _revisar_pyflakes(ruta_archivo):
            resultado["avisos_pyflakes"].append((rel, aviso))

    if verboso:
        _imprimir_reporte(resultado)

    return resultado

def _imprimir_reporte(resultado: dict):
    print(f"\n{'='*60}")
    print(f"[Inspector]: {resultado['archivos_revisados']} archivos .py revisados")
    print(f"{'='*60}")

    total_problemas = (
        len(resultado["errores_sintaxis"])
        + len(resultado["imports_rotos"])
        + len(resultado["avisos_pyflakes"])
        + len(resultado["errores_lectura"])
    )

    if total_problemas == 0:
        print("[Inspector]: No se encontraron problemas. Proyecto limpio.")
        return

    if resultado["errores_sintaxis"]:
        print(f"\nERRORES DE SINTAXIS ({len(resultado['errores_sintaxis'])}) — el proyecto NO puede arrancar con esto:")
        for archivo, msg in resultado["errores_sintaxis"]:
            print(f"   {archivo}: {msg}")

    if resultado["imports_rotos"]:
        print(f"\nIMPORTS ROTOS ({len(resultado['imports_rotos'])}) — van a tronar en cuanto se ejecuten:")
        for archivo, msg in resultado["imports_rotos"]:
            print(f"   {archivo}: {msg}")

    if resultado["avisos_pyflakes"]:
        print(f"\n AVISOS ({len(resultado['avisos_pyflakes'])}) — redefiniciones, imports sin usar, nombres indefinidos:")
        for archivo, msg in resultado["avisos_pyflakes"]:
            print(f"   {archivo}: {msg}")

    if resultado["errores_lectura"]:
        print(f"\n ARCHIVOS QUE NO SE PUDIERON LEER ({len(resultado['errores_lectura'])}):")
        for archivo, msg in resultado["errores_lectura"]:
            print(f"   {archivo}: {msg}")

    print(f"\n{'='*60}")
    print(f"[Inspector]: Total: {total_problemas} problema(s) encontrado(s).")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    inspeccionar_proyecto()