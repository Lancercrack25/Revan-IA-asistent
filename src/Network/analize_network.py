import socket
import psutil
import requests
import os
import subprocess

from src.Security.sanitizador import sanitizar_o_rechazar, EntradaNoSeguraError

# Ruta absoluta a la carpeta de scripts .bat
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

def hay_conexion_internet(timeout: float = 3.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        pass

    try:
        requests.head("https://www.google.com", timeout=timeout)
        return True
    except Exception:
        return False

def obtener_ip_local():
    """IP dentro de tu red local (la que te asigna tu router)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def obtener_ip_publica():
    """IP con la que te ve el resto de internet. Requiere conexión real a internet."""
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        if r.status_code == 200:
            return r.json().get("ip")
        return None
    except Exception:
        return None

def obtener_estadisticas_trafico():
    """Bytes enviados/recibidos por todas las interfaces desde que arrancó el sistema."""
    try:
        io = psutil.net_io_counters()
        return {
            "enviados_mb": io.bytes_sent / (1024 * 1024),
            "recibidos_mb": io.bytes_recv / (1024 * 1024),
        }
    except Exception:
        return None

def listar_interfaces_red():
    """Lista las interfaces de red disponibles (Wi-Fi, Ethernet, etc.) y si están activas."""
    try:
        interfaces = {}
        direcciones = psutil.net_if_addrs()
        estados = psutil.net_if_stats()
        for nombre, addrs in direcciones.items():
            activa = estados[nombre].isup if nombre in estados else None
            ips = [a.address for a in addrs if a.family == socket.AF_INET]
            interfaces[nombre] = {"activa": activa, "ips": ips}
        return interfaces
    except Exception as e:
        print(f"[Red]: Error al listar interfaces: {e}")
        return {}

def abrir_terminal_ping(target: str = "8.8.8.8") -> str:
    """Ejecuta el script net_ping.bat en una terminal externa.

    'target' llega desde lo que dice el usuario/LLM. Antes se interpolaba
    directo en un string con shell=True: un target como
    '8.8.8.8 & del /f /q C:\\algo' se habría ejecutado tal cual. Ahora se
    valida contra caracteres de shell y se pasa como argv separado (nunca
    shell=True), así que aunque contuviera esos caracteres no tendrían
    efecto especial.
    """
    bat_path = os.path.join(SCRIPTS_DIR, "net_ping.bat")
    try:
        target_seguro = sanitizar_o_rechazar(target, contexto="target de ping")
    except EntradaNoSeguraError:
        return "Señor, ese destino contiene caracteres no permitidos. Indíqueme una IP o dominio válido."
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "REVAN - Ping", "cmd", "/k", bat_path, target_seguro],
            shell=False,
        )
        return f"Desplegando diagnóstico de Ping hacia {target_seguro}."
    except Exception as e:
        return f"Error al abrir la terminal de Ping: {e}"

def abrir_terminal_scan() -> str:
    """Ejecuta el script net_scan.bat en una terminal externa."""
    bat_path = os.path.join(SCRIPTS_DIR, "net_scan.bat")
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "REVAN - Scan", "cmd", "/k", bat_path],
            shell=False,
        )
        return "Desplegando escaneo de sockets y puertos en terminal externa."
    except Exception as e:
        return f"Error al abrir la terminal de escaneo: {e}"

def analizar_red() -> str:
    if not hay_conexion_internet():
        return "Señor, no detecto conexión a internet en este momento. Revise su router o adaptador de red."

    ip_local = obtener_ip_local()
    ip_publica = obtener_ip_publica()
    trafico = obtener_estadisticas_trafico()

    partes = ["Conexión a internet activa."]

    if ip_local:
        partes.append(f"Su IP local es {ip_local}.")

    if ip_publica:
        partes.append(f"Su IP pública es {ip_publica}.")

    if trafico:
        partes.append(
            f"Ha transferido {trafico['recibidos_mb']:.0f} megabytes recibidos "
            f"y {trafico['enviados_mb']:.0f} enviados en esta sesión del sistema."
        )

    return " ".join(partes)

if __name__ == "__main__":
    print(analizar_red())
    print(listar_interfaces_red())