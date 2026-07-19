#este archivo se encarga de escanear la red local y detectar dispositivos desconocidos conectados
import os
import re
import json
import socket
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor

def _obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def _ping_host(ip: str, timeout_ms: int = 300) -> bool:
    """Ping silencioso de un solo intento, solo para saber si el host responde."""
    sistema = platform.system().lower()
    if "windows" in sistema:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]

    try:
        resultado = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=(timeout_ms / 1000) + 1
        )
        return resultado.returncode == 0
    except Exception:
        return False

def _leer_tabla_arp():
    """Lee la tabla ARP del sistema (IP <-> MAC de dispositivos con los que
    esta PC ya intercambió tráfico), usando el comando nativo 'arp -a'."""
    dispositivos = []
    try:
        salida = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, timeout=10
        ).stdout

        for linea in salida.splitlines():
            # Formato típico de Windows: "  192.168.1.1     00-11-22-33-44-55     dinámico"
            # Formato típico de Linux/macOS: "? (192.168.1.1) at 00:11:22:33:44:55 ..."
            match_win = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}[-:][0-9a-fA-F-:]{14,16})", linea)
            if match_win:
                ip = match_win.group(1)
                mac = match_win.group(2).replace("-", ":").lower()
                dispositivos.append({"ip": ip, "mac": mac})

    except Exception as e:
        print(f"[BusquedaIntrusos]: Error al leer tabla ARP: {e}")

    return dispositivos


def escanear_red_local(timeout_ms: int = 300, max_hilos: int = 60):
    """
    Hace un barrido de ping sobre todo el rango /24 de tu red local (ej.
    192.168.1.1 al 192.168.1.254) para forzar que los dispositivos activos
    aparezcan en la tabla ARP, y luego lee esa tabla para obtener sus IP y
    MAC. Tarda unos segundos (paralelizado con hilos, no secuencial).
    Devuelve una lista de dicts: [{"ip": ..., "mac": ...}, ...]
    """
    ip_local = _obtener_ip_local()
    if not ip_local:
        print("[BusquedaIntrusos]: No se pudo determinar la IP local, no se puede escanear.")
        return []

    partes = ip_local.split(".")
    base = ".".join(partes[:3])

    with ThreadPoolExecutor(max_workers=max_hilos) as executor:
        list(executor.map(lambda i: _ping_host(f"{base}.{i}", timeout_ms), range(1, 255)))

    return _leer_tabla_arp()


def _ruta_dispositivos_conocidos() -> str:
    """Ruta al archivo config/dispositivos_conocidos.json, junto a tus
    otros archivos de configuración (credentials.json, settings.json)."""
    raiz_proyecto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(raiz_proyecto, "config", "dispositivos_conocidos.json")


def cargar_dispositivos_conocidos() -> dict:
    """Devuelve {mac: nombre_asignado} de los dispositivos ya marcados como conocidos."""
    ruta = _ruta_dispositivos_conocidos()
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[BusquedaIntrusos]: Error al leer dispositivos conocidos: {e}")
        return {}


def guardar_dispositivos_conocidos(dispositivos: dict):
    ruta = _ruta_dispositivos_conocidos()
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(dispositivos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[BusquedaIntrusos]: Error al guardar dispositivos conocidos: {e}")


def marcar_todos_como_conocidos() -> str:
    """
    Escanea la red AHORA y guarda todo lo que encuentra como 'conocido'.
    Pensado para correr una vez al principio (baseline), para que la
    primera vez que uses detectar_intrusos() no te marque tu propio celular,
    laptop, smart TV, etc. como 'intrusos' solo por ser la primera vez que
    se ven.
    """
    encontrados = escanear_red_local()
    if not encontrados:
        return "No se encontraron dispositivos para guardar, Señor."

    conocidos = cargar_dispositivos_conocidos()
    for d in encontrados:
        conocidos.setdefault(d["mac"], f"Dispositivo en {d['ip']}")
    guardar_dispositivos_conocidos(conocidos)

    return f"Se guardaron {len(encontrados)} dispositivos como conocidos, Señor."


def detectar_intrusos() -> str:
    """
    Escanea la red y compara contra la lista de dispositivos conocidos.
    Reporta cualquier dispositivo que NO esté en esa lista.
    """
    conocidos = cargar_dispositivos_conocidos()

    if not conocidos:
        return ("Aún no tengo una lista de dispositivos conocidos, Señor. "
                "Dígame 'marca los dispositivos actuales como conocidos' primero, "
                "para tener una base de referencia.")

    encontrados = escanear_red_local()
    if not encontrados:
        return "No pude escanear la red en este momento, Señor."

    desconocidos = [d for d in encontrados if d["mac"] not in conocidos]

    if not desconocidos:
        return f"Todo en orden, Señor. Los {len(encontrados)} dispositivos conectados son reconocidos."

    ips_desconocidos = ", ".join(d["ip"] for d in desconocidos)
    return (f"Atención, Señor. Detecté {len(desconocidos)} dispositivo(s) desconocido(s) "
            f"de un total de {len(encontrados)} conectados. Direcciones: {ips_desconocidos}.")


if __name__ == "__main__":
    print("Escaneando red local...")
    dispositivos = escanear_red_local()
    print(f"Encontrados: {len(dispositivos)}")
    for d in dispositivos:
        print(f"  {d['ip']}  ->  {d['mac']}")