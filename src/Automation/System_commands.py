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
    absoluta fuera del directorio del usuario.

    ANTES: usaba os.path.join(home, "Desktop") a lo bruto. Si el Escritorio
    real del usuario está redirigido por OneDrive (muy común en Windows 11
    con cuenta Microsoft: el Escritorio real vive en
    "OneDrive\\Escritorio", no en "Desktop"), los archivos terminaban en
    una carpeta "Desktop" que el usuario nunca ve -mientras que
    crear_carpeta_sistema en os_service.py sí detectaba esto
    correctamente con obtener_ruta_escritorio()-. Ahora reutiliza esa
    misma función, una sola fuente de verdad para "dónde está el
    Escritorio de verdad".

    Devuelve (ruta_completa, None) si todo bien, o (None, mensaje_error) si
    se rechazó.
    """
    from src.Security.sanitizador import es_ruta_segura
    from src.Services.os_service import obtener_ruta_escritorio, normalizar_si_apunta_a_escritorio

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
        # Si la ruta absoluta que armó el modelo apunta a una carpeta
        # 'Desktop'/'Escritorio' literal, se redirige a la ubicación REAL
        # (que puede estar en OneDrive) en vez de crear una carpeta
        # huérfana con ese nombre.
        ruta_dir = normalizar_si_apunta_a_escritorio(carpeta_destino)
    elif carpeta_destino:
        ruta_dir = os.path.join(obtener_ruta_escritorio(), carpeta_destino)
    else:
        ruta_dir = obtener_ruta_escritorio()

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


def crear_y_abrir_hoja_excel(nombre_archivo: str, titulo: str, datos_csv: str,
                              carpeta_destino: str = None) -> str:
    """
    Crea un archivo .xlsx REAL a partir de datos en formato CSV simple
    (una fila por línea, valores separados por comas, primera línea =
    encabezados), lo formatea con encabezados en negrita y ancho de
    columna automático, y lo abre en Excel.

    ANTES: recibía 'encabezados' y 'filas' como parámetros separados,
    'filas' siendo una lista de listas (JSON anidado). Un modelo de
    function-calling chico (Llama 3.1 8B) es notablemente menos confiable
    generando arrays anidados correctamente -en la práctica, la tool
    fallaba en silencio o el modelo ni la invocaba-. Un solo string en
    formato CSV es tan simple de generar como el 'contenido' de Word (que
    sí funciona bien), así que se unificó a ese patrón.

    Ejemplo de datos_csv esperado:
        "Producto,Precio Tienda A,Precio Tienda B
Laptop X,18000,17500
Mouse Y,350,400"
    """
    try:
        import csv
        import io

        filas_parseadas = list(csv.reader(io.StringIO(datos_csv or "")))
        if not filas_parseadas:
            return "Señor, no recibí datos utilizables para construir la hoja de cálculo."

        encabezados = filas_parseadas[0]
        filas = filas_parseadas[1:]

        ruta_completa, error = _resolver_ruta_destino_segura(nombre_archivo, carpeta_destino, ".xlsx")
        if error:
            return error

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter

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

            for col_idx, encabezado in enumerate(encabezados, start=1):
                celda = ws.cell(row=fila_actual, column=col_idx, value=encabezado)
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
                celda.alignment = Alignment(horizontal="center")

            for offset_fila, fila_datos in enumerate(filas, start=1):
                for col_idx, valor in enumerate(fila_datos, start=1):
                    ws.cell(row=fila_actual + offset_fila, column=col_idx, value=valor)

            for col_idx, encabezado in enumerate(encabezados, start=1):
                letra_col = get_column_letter(col_idx)
                largo_max = len(str(encabezado))
                for fila_datos in filas:
                    if col_idx <= len(fila_datos):
                        largo_max = max(largo_max, len(str(fila_datos[col_idx - 1])))
                ws.column_dimensions[letra_col].width = min(largo_max + 4, 40)

            wb.save(ruta_completa)
        except ImportError:
            ruta_completa = ruta_completa.replace(".xlsx", ".csv")
            with open(ruta_completa, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(encabezados)
                writer.writerows(filas)

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
            # os.startfile invoca ShellExecute directamente, sin pasar por
            # cmd.exe -es la forma más segura de abrir un protocolo/URI.
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