import os
import sys
import webbrowser
import subprocess
import urllib.parse

sys.dont_write_bytecode = True


def desplegar_monitores_windows() -> bool:
    """Despliega la configuración de monitores nativos en Windows."""
    try:
        subprocess.Popen("displayswitch.exe /extend", shell=True)
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

    try:
        # 1. Aplicaciones conocidas / URIs / Protocolos
        if any(k in nombre_clean for k in ["calc", "calculadora"]):
            subprocess.Popen("calc.exe")
            return "Calculadora abierta, Señor."

        elif any(k in nombre_clean for k in ["bloc", "notepad", "notas"]):
            subprocess.Popen("notepad.exe")
            return "Bloc de notas abierto, Señor."

        elif any(k in nombre_clean for k in ["brave", "chrome", "navegador", "internet"]):
            webbrowser.open("https://www.google.com")
            return "Navegador abierto, Señor."

        elif "discord" in nombre_clean:
            # Comando nativo exacto para Discord en Windows
            subprocess.Popen(r'start "" "%LocalAppData%\Discord\Update.exe" --processStart Discord.exe', shell=True)
            return "Desplegando Discord, Señor."

        elif "whatsapp" in nombre_clean:
            subprocess.Popen("start whatsapp:", shell=True)
            return "Desplegando WhatsApp, Señor."

        elif "steam" in nombre_clean:
            subprocess.Popen("start steam:", shell=True)
            return "Iniciando Steam, Señor."

        elif "xbox" in nombre_clean:
            subprocess.Popen("start xbox:", shell=True)
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

        # 3. Intento de fallback mediante 'start' nativo
        res = os.system(f'start "" "{nombre}"')
        if res == 0:
            return f"Ejecutando {nombre}, Señor."

        return f"No se encontró la aplicación {nombre} en el equipo, Señor."

    except Exception as e:
        return f"Error al lanzar la aplicación {nombre}: {e}"

def lanzar_videojuego(nombre_juego: str) -> str:
    nombre = nombre_juego.lower().strip()
    try:
        if "minecraft" in nombre:
            os.system("start minecraft:")
            return "Iniciando Minecraft."
        else:
            os.system(f"start {nombre_juego}")
            return f"Iniciando {nombre_juego}."
    except Exception as e:
        return f"Error al intentar abrir el juego: {e}"

def ejecutar_aplicacion_office(app: str) -> str:
    """Abre aplicaciones de la suite Microsoft Office."""
    nombre = app.lower().strip()
    try:
        if "word" in nombre:
            subprocess.Popen("winword.exe")
            return "Microsoft Word iniciado."
        elif "excel" in nombre:
            subprocess.Popen("excel.exe")
            return "Microsoft Excel iniciado."
        elif "powerpoint" in nombre or "ppt" in nombre:
            subprocess.Popen("powerpnt.exe")
            return "Microsoft PowerPoint iniciado."
        else:
            os.system(f"start {app}")
            return f"Ejecutando {app}."
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