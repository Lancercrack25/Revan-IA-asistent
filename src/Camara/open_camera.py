import cv2
import os
import sys

sys.dont_write_bytecode = True

def capturar_pantallazo_camara():
    """
    Enciende la cámara web, captura un único frame instantáneo,
    lo guarda en el disco y cierra el hardware de inmediato.
    """
    # Intentamos abrir la cámara predeterminada (ID 0)
    camara = cv2.VideoCapture(0)
    if not camara.isOpened():
        print("Error: No se pudo acceder a la cámara web.")
        return None
    # Dejamos que la cámara se calibre un milisegundo para evitar fotos oscuras
    for _ in range(5):
        camara.read()
        
    lectura_exitosa, frame = camara.read()
    camara.release()  # Liberamos el hardware de inmediato para ahorrar energía
    
    if not lectura_exitosa:
        print("Error: No se pudo leer el flujo de la cámara.")
        return None  
    # Guardamos la imagen de forma temporal en la raíz del proyecto
    ruta_guardado = os.path.join(os.path.dirname(__file__), "..", "..", "captura_tactica.jpg")
    ruta_abs = os.path.abspath(ruta_guardado)
    # Guardamos la imagen capturada en la ruta especificada
    cv2.imwrite(ruta_abs, frame)
    print(f"[Cámara]: Captura táctica resguardada en {ruta_abs}")
    return ruta_abs