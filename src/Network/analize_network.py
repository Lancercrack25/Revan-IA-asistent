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