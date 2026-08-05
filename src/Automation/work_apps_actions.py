#este archivo se encargara de que revan peuda abrir aplicaciones y cosas relacionadas al trabajo
#tales como teams, meeet, outlook, gmail, drive, etc.
import os
import subprocess
import webbrowser


def abrir_teams() -> str:
    """Abre Microsoft Teams vía su protocolo registrado; si no está
    registrado, intenta el ejecutable directo como respaldo."""
    try:
        os.startfile("msteams:")
        return "Abriendo Microsoft Teams, Señor."
    except OSError:
        try:
            subprocess.Popen(["Teams.exe"], shell=False)
            return "Abriendo Microsoft Teams, Señor."
        except Exception:
            return "No pude abrir Teams, Señor. Verifique que esté instalado."


def abrir_outlook() -> str:
    """Abre Outlook de escritorio (no la versión web)."""
    try:
        subprocess.Popen(["OUTLOOK.EXE"], shell=False)
        return "Abriendo Outlook, Señor."
    except Exception:
        try:
            os.startfile("outlook:")
            return "Abriendo Outlook, Señor."
        except OSError:
            return "No pude abrir Outlook, Señor. Verifique que esté instalado en este equipo."


def abrir_vscode() -> str:
    """Abre Visual Studio Code. Intenta el comando 'code' (si está en el
    PATH, que es la instalación por defecto), y si no, la ruta típica de
    instalación por usuario en Windows."""
    try:
        subprocess.Popen(["code"], shell=False)
        return "Abriendo Visual Studio Code, Señor."
    except Exception:
        try:
            ruta_code = os.path.expandvars(r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe")
            os.startfile(ruta_code)
            return "Abriendo Visual Studio Code, Señor."
        except OSError:
            return "No pude abrir VS Code, Señor. Verifique que esté instalado."


def abrir_google_meet() -> str:
    """Abre una reunión nueva de Google Meet en el navegador por defecto."""
    webbrowser.open("https://meet.google.com/new")
    return "Abriendo una nueva reunión de Google Meet, Señor."


def abrir_google_drive() -> str:
    """Abre Google Drive en el navegador por defecto."""
    webbrowser.open("https://drive.google.com")
    return "Abriendo Google Drive, Señor."