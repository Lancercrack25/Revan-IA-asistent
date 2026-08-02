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


def crear_y_abrir_documento_word(nombre_archivo: str, tema_o_contenido: str, carpeta_destino: str = None) -> str:
    """Crea un archivo .docx REAL con contenido sobre el tema solicitado y lo abre en Microsoft Word."""
    try:
        if carpeta_destino and os.path.isabs(carpeta_destino):
            ruta_dir = carpeta_destino
        elif carpeta_destino:
            ruta_dir = os.path.join(os.path.expanduser("~"), "Desktop", carpeta_destino)
        else:
            ruta_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        os.makedirs(ruta_dir, exist_ok=True)

        if not nombre_archivo.endswith(".docx"):
            nombre_archivo += ".docx"

        ruta_completa = os.path.join(ruta_dir, nombre_archivo)

        try:
            import docx
            doc = docx.Document()
            doc.add_heading(nombre_archivo.replace(".docx", ""), level=1)
            doc.add_paragraph(f"Documento generado por REVAN sobre la temática: {tema_o_contenido}\n")
            doc.add_paragraph(tema_o_contenido)
            doc.save(ruta_completa)
        except ImportError:
            with open(ruta_completa.replace(".docx", ".txt"), "w", encoding="utf-8") as f:
                f.write(f"--- {nombre_archivo} ---\n\nTema: {tema_o_contenido}")
            ruta_completa = ruta_completa.replace(".docx", ".txt")

        os.startfile(ruta_completa)
        return f"Archivo '{nombre_archivo}' creado con éxito con la información sobre '{tema_o_contenido}' y abierto en pantalla."

    except Exception as e:
        return f"Error al crear el documento: {e}"

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