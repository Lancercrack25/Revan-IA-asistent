import sys
sys.dont_write_bytecode = True  # Prevenir archivos de caché .pyc

def ejecutar_misión_compleja(orden_usuario: str, cerebro_ia):
    orden = orden_usuario.lower().strip()
    palabras_accion_simple = [
        "crea", "carpeta", "archivo", "word", "excel", "abre",
        "navegador", "video", "juego", "app", "monitor", "limpia",
    ]
    if any(k in orden for k in palabras_accion_simple):
        return None
    palabras_mision = [
        "investiga", "busca información", "busca informacion",
        "qué es", "que es", "quién es", "quien es",
        "recuerda", "guarda una nota", "guárdame", "guardame",
    ]
    if any(k in orden for k in palabras_mision):
        print(f"[Orchestrator]: Delegando misión a NimClient con herramientas: '{orden}'")
        return cerebro_ia.generar_respuesta(orden_usuario)
    return None