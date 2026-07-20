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


def _ruta_carpeta_reportes() -> str:
    """Carpeta 'Reportes' dentro de src/Network, junto a este mismo archivo."""
    carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Reportes")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def generar_reporte_seguridad(encontrados: list, desconocidos: list) -> str:
    """
    Genera un archivo .txt con el detalle completo del escaneo (todos los
    dispositivos, cuáles son desconocidos, y el veredicto), y devuelve la
    ruta del archivo generado.
    """
    from datetime import datetime

    carpeta = _ruta_carpeta_reportes()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta_archivo = os.path.join(carpeta, f"reporte_red_{timestamp}.txt")

    macs_desconocidas = {d["mac"] for d in desconocidos}

    lineas = [
        "REPORTE DE SEGURIDAD DE RED - REVAN",
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "=" * 50,
        "",
        f"Total de dispositivos conectados: {len(encontrados)}",
        f"Dispositivos desconocidos: {len(desconocidos)}",
        "",
        "--- DETALLE DE TODOS LOS DISPOSITIVOS ---",
    ]

    for d in encontrados:
        estado = "DESCONOCIDO" if d["mac"] in macs_desconocidas else "conocido"
        lineas.append(f"  IP: {d['ip']:<16} MAC: {d['mac']:<20} Estado: {estado}")

    lineas.append("")
    if desconocidos:
        lineas.append("--- ATENCIÓN: DISPOSITIVOS DESCONOCIDOS DETECTADOS ---")
        for d in desconocidos:
            lineas.append(f"  IP: {d['ip']}   MAC: {d['mac']}")
        lineas.append("")
        lineas.append("VEREDICTO: Su red podría estar comprometida. Revise estos dispositivos.")
    else:
        lineas.append("VEREDICTO: Su red está segura. Todos los dispositivos son reconocidos.")

    try:
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
        return ruta_archivo
    except Exception as e:
        print(f"[BusquedaIntrusos]: Error al generar el reporte: {e}")
        return ""


def detectar_intrusos() -> str:
    """
    Escanea la red, compara contra dispositivos conocidos, genera un
    reporte en archivo, y da un VEREDICTO claro (segura / posiblemente
    comprometida) además de los detalles.
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

    ruta_reporte = generar_reporte_seguridad(encontrados, desconocidos)
    nombre_reporte = os.path.basename(ruta_reporte) if ruta_reporte else None

    if not desconocidos:
        texto = (f"Su red está segura, Señor. Los {len(encontrados)} dispositivos conectados "
                  f"son reconocidos.")
    else:
        ips_desconocidos = ", ".join(d["ip"] for d in desconocidos)
        texto = (f"Atención, Señor. Su red podría estar comprometida. Detecté "
                  f"{len(desconocidos)} dispositivo(s) desconocido(s) de {len(encontrados)} "
                  f"conectados, en las direcciones: {ips_desconocidos}.")

    if nombre_reporte:
        texto += f" Generé un reporte detallado: {nombre_reporte}."

    return texto


if __name__ == "__main__":
    print("Escaneando red local...")
    dispositivos = escanear_red_local()
    print(f"Encontrados: {len(dispositivos)}")
    for d in dispositivos:
        print(f"  {d['ip']}  ->  {d['mac']}")