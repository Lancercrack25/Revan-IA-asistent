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
    

