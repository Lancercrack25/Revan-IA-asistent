import os

def abrir_battlenet_escritorio():
    """Busca y ejecuta Battle.net usando la ruta exacta de OneDrive detectada en tu sistema."""
    ruta_usuario = os.environ.get("USERPROFILE")
    
    # Añadimos la ruta exacta con OneDrive que se ve en tu imagen
    posibles_rutas = [
        os.path.join(ruta_usuario, "OneDrive", "Escritorio", "Plataformas", "Battle.net.lnk"),
        os.path.join(ruta_usuario, "OneDrive", "Desktop", "Plataformas", "Battle.net.lnk"),
        os.path.join(ruta_usuario, "Desktop", "Plataformas", "Battle.net.lnk"),
        os.path.join(ruta_usuario, "Escritorio", "Plataformas", "Battle.net.lnk")
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                os.startfile(ruta)
                print(f"🎮 ¡Battle.net localizado y lanzado con éxito desde!: {ruta}")
                return True
            except Exception as e:
                print(f"⚠️ Error al intentar abrir el acceso directo: {e}")
                
    print("❌ REVAN Error: No se pudo mapear la ruta de Battle.net en el Escritorio sincronizado.")
    return False