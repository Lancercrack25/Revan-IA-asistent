import subprocess
import sys

def lanzar_bucle_terminal():
    """Lanza una ventana de CMD real que se llena de texto simulando un ataque."""
    # El comando abre un CMD nuevo, le cambia el color a verde hacker (color a) 
    # y ejecuta un bucle infinito que imprime el mensaje.
    comando_cmd = 'start cmd /k "color a && title REVAN CORRUPT SYSTEM && FOR /L %i IN () DO @echo ACTIVANDO HACKS... ACCEDIENDO AL NÚCLEO... BYPASSING FIREWALL... %i"'
    
    try:
        subprocess.Popen(comando_cmd, shell=True)
        print("💻 Consola de inyección de hacks desplegada.")
    except Exception as e:
        print(f"No se pudo abrir la terminal: {e}")