import sys

sys.dont_write_bytecode = True  # Prevenir archivos de caché .pyc


def ejecutar_misión_compleja(orden_usuario: str, cerebro_ia):
    """
    Router liviano hacia el loop de herramientas de NimClient.

    ANTES: esta función tenía su propia lógica hardcodeada para UN SOLO
    caso ("investiga" + "guarda"/"escribe"), llamando directo a
    research_service.py y armando el flujo de investigación+guardado a
    mano, paso por paso.

    AHORA: con el tool-calling nativo de NimClient (buscar_informacion y
    guardar_nota son herramientas reales que el modelo puede invocar y
    encadenar por su cuenta), ya no hace falta reimplementar ese flujo
    aquí. El propio modelo decide qué herramientas usar y en qué orden,
    incluso para combinaciones que no anticipamos explícitamente (antes,
    "investiga X y avísame por escrito" no coincidía con el patrón exacto
    "investiga"+"guarda" y se perdía; ahora sí lo puede resolver).

    Esta función ahora solo decide SI algo suena a una "misión" que
    necesita herramientas de investigación/memoria, para mandarlo a
    NimClient en vez de que cayera por error en Gemini (que no tiene esas
    herramientas). Las acciones simples (crear carpeta, abrir Word, etc.)
    las deja pasar de largo — main.py ya las enruta a NimClient por su
    cuenta vía PALABRAS_CLAVE_ACCION.
    """
    orden = orden_usuario.lower().strip()

    # Acciones simples: no es responsabilidad de este router, main.py ya
    # las manda a NimClient por su cuenta.
    palabras_accion_simple = [
        "crea", "carpeta", "archivo", "word", "excel", "abre",
        "navegador", "video", "juego", "app", "monitor", "limpia",
    ]
    if any(k in orden for k in palabras_accion_simple):
        return None

    # Misiones que necesitan las herramientas de investigación/memoria de
    # NimClient (buscar_informacion, guardar_nota), sin importar si vienen
    # solas o combinadas de formas que no anticipamos explícitamente aquí.
    palabras_mision = [
        "investiga", "busca información", "busca informacion",
        "qué es", "que es", "quién es", "quien es",
        "recuerda", "guarda una nota", "guárdame", "guardame",
    ]
    if any(k in orden for k in palabras_mision):
        print(f"[Orchestrator]: Delegando misión a NimClient con herramientas: '{orden}'")
        return cerebro_ia.generar_respuesta(orden_usuario)

    return None