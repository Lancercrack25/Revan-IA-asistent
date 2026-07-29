import os
import json


def cargar_configuracion_json() -> dict:
    """
    Busca y carga las credenciales desde el archivo de configuración JSON 
    en las rutas más comunes del proyecto REVAN.
    """
    # Rutas donde REVAN buscará tu archivo de claves
    posibles_rutas = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config.json")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "keys.json")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.json")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "keys.json")),
    ]

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    print(f"[ACCOUNT CONNECTION]: Configuración cargada desde -> {os.path.basename(ruta)}")
                    return datos
            except Exception as e:
                print(f"[ACCOUNT CONNECTION ERROR]: Error al leer {ruta} -> {e}")

    print("[ACCOUNT CONNECTION WARNING]: No se encontró ningún archivo JSON de configuración válido.")
    return {}

def obtener_credenciales_email() -> tuple[str, str]:
    """
    Extrae la cuenta de correo y la contraseña de aplicación de 16 caracteres.
    Retorna: (EMAIL_USER, EMAIL_PASSWORD)
    """
    config = cargar_configuracion_json()

    # Soporta varios nombres de llaves comunes por si cambiaste la etiqueta en el JSON
    user = (
        config.get("EMAIL_USER") 
        or config.get("EMAIL") 
        or config.get("REVAN_EMAIL_USER") 
        or os.getenv("EMAIL_USER", "")
    )
    
    password = (
        config.get("EMAIL_PASSWORD") 
        or config.get("EMAIL_PASS") 
        or config.get("REVAN_EMAIL_PASS") 
        or os.getenv("EMAIL_PASSWORD", "")
    )

    return user, password
if __name__ == "__main__":
    print("[GOOGLE CONNECTION]: Comprobando lectura de credenciales desde el JSON...")
    usuario, clave = obtener_credenciales_email()

    if usuario and clave:
        # Muestra los primeros 3 caracteres por seguridad
        clave_oculta = clave[:3] + "*" * (len(clave) - 3)
        print(f"[GOOGLE CONNECTION]: ✅ Credenciales detectadas con éxito.")
        print(f" -> Usuario: {usuario}")
        print(f" -> Clave: {clave_oculta}")
    else:
        print("[GOOGLE CONNECTION]: ❌ No se pudieron cargar las credenciales. Revisa tu archivo JSON porfavor.")