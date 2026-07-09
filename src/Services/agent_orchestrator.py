import sys
import os

sys.dont_write_bytecode = True  # Prevenir archivos de caché .pyc

def ejecutar_misión_compleja(orden_usuario: str, cerebro_ia):
    """
    Evalúa si la orden requiere un flujo multi-paso avanzado.
    Si es una orden simple o conversación común, retorna None de inmediato
    para que el flujo siga su curso normal con Ollama sin congelar la GUI.
    """
    # 1. Normalizamos la cadena para evaluar
    orden = orden_usuario.lower().strip()
    
    # 2. FILTRO TÁCTICO: Si es una orden común de automatización, NO la tocamos aquí.
    # Dejamos que Ollama_client la procese con su lógica experta de JSON.
    palabras_clave_simples = ["crea", "carpeta", "archivo", "word", "excel", "abre", "busca", "navegador"]
    if any(keyword in orden for keyword in palabras_clave_simples):
        return None

    # 3. ZONA DE MISIONES COMPLEJAS (Solo entra aquí si coincide exactamente)
    # Ejemplo de misión compleja: "investiga profundamente sobre..."
    if "investiga" in orden and ("guarda" in orden or "escribe" in orden):
        print(f"[Orchestrator]: Ejecutando protocolo de investigación avanzada para: '{orden}'")
        
        # Importamos aquí dentro para evitar referencias circulares lentas al arrancar
        from src.Services.research_service import buscar_y_resumir_tema
        from src.Services.os_service import registrar_accion_sistema
        
        tema = orden.replace("investiga sobre", "").replace("y guárdalo", "").strip()
        datos_encontrados = buscar_y_resumir_tema(tema)
        
        if "Error" in datos_encontrados or "No logré" in datos_encontrados:
            return "Misión abortada. No se pudo recolectar información de la red principal."
            
        prompt_refinado = f"Redacta un resumen ejecutivo breve basado en estos datos:\n{datos_encontrados}"
        resumen_ia = cerebro_ia.generar_respuesta(prompt_refinado)
        
        registrar_accion_sistema(
            orden=f"Investigación de {tema}",
            respuesta=resumen_ia,
            accion_tipo="RESEARCH_TASK"
        )
        return f"Misión completada, Señor. Datos de {tema} procesados y registrados en PostgreSQL."
    return None