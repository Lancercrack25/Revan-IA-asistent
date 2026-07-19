#este archivo se encargara de realizar un analisis de la red y obtener informacion relevante sobre la misma
import socket
import psutil
import requests


def hay_conexion_internet(timeout: float = 3.0) -> bool:
    """
    Chequeo de conectividad con dos intentos:
    1. Socket directo a un DNS público (rápido, barato, pero algunos
       firewalls/redes corporativas bloquean el puerto 53 saliente).
    2. Si eso falla, respaldo vía HTTPS normal (puerto 443, casi nunca
       bloqueado), para no dar un falso "sin internet" en esos casos.
    """
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
    """Bytes enviados/recibidos por todas las interfaces desde que arrancó el sistema
    (no desde que arrancó REVAN, es un contador acumulado del propio sistema operativo)."""
    try:
        io = psutil.net_io_counters()
        return {
            "enviados_mb": io.bytes_sent / (1024 * 1024),
            "recibidos_mb": io.bytes_recv / (1024 * 1024),
        }
    except Exception:
        return None


def listar_interfaces_red():
    """Lista las interfaces de red disponibles (Wi-Fi, Ethernet, etc.) y si están activas.
    Pensado para depuración en consola, no para hablarse en voz alta (puede ser largo)."""
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


def analizar_red() -> str:
    """
    Resumen rápido y hablable del estado de la red. Pensado para responder
    en 1-2 segundos (nada de pruebas de velocidad aquí, esas tardan más y
    van en probar_velocidad_internet(), aparte, solo cuando se pide explícitamente).
    """
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