import os
import sys
import webbrowser
import subprocess
import urllib.parse

from src.Security.sanitizador import sanitizar_o_rechazar, EntradaNoSeguraError

sys.dont_write_bytecode = True


def desplegar_monitores_windows() -> bool:
    """Despliega la configuración de monitores nativos en Windows."""
    try:
        # Lista de argumentos, sin shell=True: displayswitch.exe /extend no
        # necesita ningún shell para ejecutarse.
        subprocess.Popen(["displayswitch.exe", "/extend"], shell=False)
        print("[SystemCommands]: Monitores de Windows configurados correctamente.")
        return True
    except Exception as e:
        print(f"[SystemCommands]: Error al desplegar monitores: {e}")
        return False


def buscar_en_navegador_sistema(consulta: str) -> str:
    """Abre el navegador predeterminado y busca en Google."""
    if not consulta:
        return "No se especificó ninguna consulta."
    try:
        query = urllib.parse.quote(consulta.strip())
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Buscando '{consulta}' en el navegador."
    except Exception as e:
        return f"Error abriendo navegador: {e}"


def reproducir_video_brave(busqueda: str) -> str:
    """Abre YouTube con la búsqueda solicitada."""
    if not busqueda:
        return "No se especificó búsqueda de video."
    try:
        query = urllib.parse.quote(busqueda.strip())
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Buscando video '{busqueda}' en YouTube."
    except Exception as e:
        return f"Error al abrir YouTube: {e}"


def _resolver_ruta_destino_segura(nombre_archivo: str, carpeta_destino: str, extension: str):
    """
    Lógica compartida por los generadores de Word/Excel: sanea el nombre
    de archivo, resuelve la carpeta destino, y RECHAZA cualquier ruta
    absoluta fuera del directorio del usuario (antes esto se aceptaba tal
    cual, sin ningún control -mismo hueco que se cerró en
    crear_carpeta_sistema, ahora también aquí-).

    Devuelve (ruta_completa, None) si todo bien, o (None, mensaje_error) si
    se rechazó.
    """
    from src.Security.sanitizador import es_ruta_segura

    nombre_archivo = "".join(c for c in nombre_archivo if c not in '<>:"/\\|?*').strip() or "Documento"
    if not nombre_archivo.endswith(extension):
        nombre_archivo += extension

    if carpeta_destino and os.path.isabs(carpeta_destino):
        if not es_ruta_segura(carpeta_destino):
            return None, (
                f"Señor, no voy a crear nada en '{carpeta_destino}' porque está fuera de su "
                f"carpeta de usuario. Dígame que lo cree en Escritorio, Documentos, o "
                f"déjeme usar la ubicación por defecto."
            )
        ruta_dir = carpeta_destino
    elif carpeta_destino:
        ruta_dir = os.path.join(os.path.expanduser("~"), "Desktop", carpeta_destino)
    else:
        ruta_dir = os.path.join(os.path.expanduser("~"), "Desktop")

    os.makedirs(ruta_dir, exist_ok=True)
    return os.path.join(ruta_dir, nombre_archivo), None


def crear_y_abrir_documento_word(nombre_archivo: str, contenido: str, carpeta_destino: str = None) -> str:
    """
    Crea un archivo .docx REAL con contenido ya redactado (no un tema
    suelto) y lo abre en Microsoft Word.

    'contenido' se espera ya escrito por el LLM, con esta convención
    simple de estructura (no es markdown completo, solo lo mínimo para
    dar formato real en vez de un solo párrafo plano):
      - Una línea que empiece con "# " se convierte en encabezado (H1).
      - Una línea que empiece con "## " se convierte en encabezado (H2).
      - Líneas en blanco separan párrafos.
      - Líneas que empiecen con "- " se convierten en viñetas.
    """
    try:
        ruta_completa, error = _resolver_ruta_destino_segura(nombre_archivo, carpeta_destino, ".docx")
        if error:
            return error

        try:
            import docx
            doc = docx.Document()

            for linea in (contenido or "").split("\n"):
                linea_limpia = linea.rstrip()
                if not linea_limpia.strip():
                    continue
                if linea_limpia.startswith("## "):
                    doc.add_heading(linea_limpia[3:].strip(), level=2)
                elif linea_limpia.startswith("# "):
                    doc.add_heading(linea_limpia[2:].strip(), level=1)
                elif linea_limpia.startswith("- "):
                    doc.add_paragraph(linea_limpia[2:].strip(), style="List Bullet")
                else:
                    doc.add_paragraph(linea_limpia.strip())

            doc.save(ruta_completa)
        except ImportError:
            ruta_completa = ruta_completa.replace(".docx", ".txt")
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido or "")

        os.startfile(ruta_completa)
        return f"Documento '{os.path.basename(ruta_completa)}' creado y abierto en pantalla, Señor."

    except Exception as e:
        return f"Error al crear el documento: {e}"


def crear_y_abrir_hoja_excel(nombre_archivo: str, titulo: str, encabezados: list,
                              filas: list, carpeta_destino: str = None) -> str:
    """
    Crea un archivo .xlsx REAL con una tabla de datos (encabezados en
    negrita + filas), lo formatea con ancho de columna razonable, y lo
    abre en Excel.

    encabezados: lista de strings, ej. ["Producto", "Precio A", "Precio B"]
    filas: lista de listas, ej. [["Laptop X", "18000", "17500"], ...]
    """
    try:
        ruta_completa, error = _resolver_ruta_destino_segura(nombre_archivo, carpeta_destino, ".xlsx")
        if error:
            return error

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Datos"

            fila_actual = 1
            if titulo:
                ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(1, len(encabezados)))
                celda_titulo = ws.cell(row=1, column=1, value=titulo)
                celda_titulo.font = Font(bold=True, size=14)
                celda_titulo.alignment = Alignment(horizontal="center")
                fila_actual = 3

            for col_idx, encabezado in enumerate(encabezados or [], start=1):
                celda = ws.cell(row=fila_actual, column=col_idx, value=encabezado)
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
                celda.alignment = Alignment(horizontal="center")

            for offset_fila, fila_datos in enumerate(filas or [], start=1):
                for col_idx, valor in enumerate(fila_datos, start=1):
                    ws.cell(row=fila_actual + offset_fila, column=col_idx, value=valor)

            # Ancho de columna aproximado según el contenido más largo
            for col_idx, encabezado in enumerate(encabezados or [], start=1):
                letra_col = openpyxl.utils.get_column_letter(col_idx)
                largo_max = len(str(encabezado))
                for fila_datos in (filas or []):
                    if col_idx <= len(fila_datos):
                        largo_max = max(largo_max, len(str(fila_datos[col_idx - 1])))
                ws.column_dimensions[letra_col].width = min(largo_max + 4, 40)

            wb.save(ruta_completa)
        except ImportError:
            # Sin openpyxl instalado: CSV como respaldo, para que igual
            # obtengas los datos aunque sin el formato visual de Excel.
            import csv
            ruta_completa = ruta_completa.replace(".xlsx", ".csv")
            with open(ruta_completa, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if encabezados:
                    writer.writerow(encabezados)
                for fila_datos in (filas or []):
                    writer.writerow(fila_datos)

        os.startfile(ruta_completa)
        return f"Hoja de cálculo '{os.path.basename(ruta_completa)}' creada y abierta en pantalla, Señor."

    except Exception as e:
        return f"Error al crear la hoja de cálculo: {e}"

def lanzar_aplicacion_usuario(nombre_app: str) -> str:
    """Lanza aplicaciones populares, accesos directos o ejecutables de Windows."""
    if isinstance(nombre_app, dict):
        nombre = str(nombre_app.get("nombre", nombre_app.get("app", nombre_app.get("aplicacion", ""))))
    else:
        nombre = str(nombre_app)

    nombre_clean = nombre.lower().strip()
    if not nombre_clean:
        return "Señor, no se especificó el nombre de ninguna aplicación."

    # Primera línea de defensa: si el nombre trae caracteres que no pintan
    # nada en un nombre de app legítimo (&, |, ;, backticks, etc.), se
    # rechaza aquí mismo, antes de intentar abrir nada.
    try:
        nombre = sanitizar_o_rechazar(nombre, contexto="nombre de aplicación")
    except EntradaNoSeguraError as err_sanit:
        return f"Señor, no puedo procesar ese nombre de aplicación: {err_sanit}"

    try:
        # 1. Aplicaciones conocidas / URIs / Protocolos
        if any(k in nombre_clean for k in ["calc", "calculadora"]):
            subprocess.Popen(["calc.exe"], shell=False)
            return "Calculadora abierta, Señor."

        elif any(k in nombre_clean for k in ["bloc", "notepad", "notas"]):
            subprocess.Popen(["notepad.exe"], shell=False)
            return "Bloc de notas abierto, Señor."

        elif any(k in nombre_clean for k in ["brave", "chrome", "navegador", "internet"]):
            webbrowser.open("https://www.google.com")
            return "Navegador abierto, Señor."

        elif "discord" in nombre_clean:
            # os.startfile no soporta pasar argumentos extra, así que aquí
            # sí necesitamos subprocess -pero como LISTA de argumentos, sin
            # pasar nunca por un shell que interprete '&', '|', etc.
            discord_exe = os.path.expandvars(r"%LocalAppData%\Discord\Update.exe")
            subprocess.Popen([discord_exe, "--processStart", "Discord.exe"], shell=False)
            return "Desplegando Discord, Señor."

        elif "whatsapp" in nombre_clean:
            os.startfile("whatsapp:")
            return "Desplegando WhatsApp, Señor."

        elif "steam" in nombre_clean:
            os.startfile("steam:")
            return "Iniciando Steam, Señor."

        elif "xbox" in nombre_clean:
            os.startfile("xbox:")
            return "Iniciando xbox, Señor."

        # 2. Búsqueda automática de accesos directos (.lnk) en el Menú Inicio de Windows
        rutas_menu_inicio = [
            os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"),
            "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
            os.path.join(os.path.expanduser("~"), "Desktop")  # Escritorio
        ]

        for ruta in rutas_menu_inicio:
            if os.path.exists(ruta):
                for root, _, files in os.walk(ruta):
                    for file in files:
                        if nombre_clean in file.lower() and file.endswith((".lnk", ".exe")):
                            ruta_completa = os.path.join(root, file)
                            os.startfile(ruta_completa)
                            return f"Ejecutando {nombre} desde su sistema, Señor."

        # 3. Intento de fallback: os.startfile invoca ShellExecute
        # directamente (sin pasar por cmd.exe/shell), a diferencia de
        # os.system('start ...') que sí interpreta la cadena con un shell.
        try:
            os.startfile(nombre)
            return f"Ejecutando {nombre}, Señor."
        except OSError:
            return f"No se encontró la aplicación {nombre} en el equipo, Señor."

    except Exception as e:
        return f"Error al lanzar la aplicación {nombre}: {e}"

def lanzar_videojuego(nombre_juego: str) -> str:
    try:
        nombre_juego = sanitizar_o_rechazar(nombre_juego, contexto="nombre de videojuego")
    except EntradaNoSeguraError as err_sanit:
        return f"Señor, no puedo procesar ese nombre de juego: {err_sanit}"

    nombre = nombre_juego.lower().strip()
    try:
        if "minecraft" in nombre:
            os.startfile("minecraft:")
            return "Iniciando Minecraft."
        else:
            try:
                os.startfile(nombre_juego)
                return f"Iniciando {nombre_juego}."
            except OSError:
                return f"No se encontró el juego {nombre_juego}, Señor."
    except Exception as e:
        return f"Error al intentar abrir el juego: {e}"

def ejecutar_aplicacion_office(app: str) -> str:
    """Abre aplicaciones de la suite Microsoft Office."""
    try:
        app = sanitizar_o_rechazar(app, contexto="nombre de aplicación de Office")
    except EntradaNoSeguraError as err_sanit:
        return f"Señor, no puedo procesar esa entrada: {err_sanit}"

    nombre = app.lower().strip()
    try:
        if "word" in nombre:
            subprocess.Popen(["winword.exe"], shell=False)
            return "Microsoft Word iniciado."
        elif "excel" in nombre:
            subprocess.Popen(["excel.exe"], shell=False)
            return "Microsoft Excel iniciado."
        elif "powerpoint" in nombre or "ppt" in nombre:
            subprocess.Popen(["powerpnt.exe"], shell=False)
            return "Microsoft PowerPoint iniciado."
        else:
            try:
                os.startfile(app)
                return f"Ejecutando {app}."
            except OSError:
                return f"No se encontró la aplicación de Office '{app}', Señor."
    except Exception as e:
        return f"Error al abrir la aplicación de Office '{app}': {e}"

__all__ = [
    "buscar_en_navegador_sistema",
    "reproducir_video_brave",
    "lanzar_aplicacion_usuario",
    "lanzar_videojuego",
    "desplegar_monitores_windows",
    "ejecutar_aplicacion_office",
    "crear_y_abrir_documento_word",
]