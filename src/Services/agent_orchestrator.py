import sys
import os
# Importamos los otros servicios que ya tienen lógica real
from src.Services.os_service import registrar_accion_sistema
from src.Services.research_service import buscar_y_resumir_tema

sys.dont_write_bytecode = True

def ejecutar_misión_compleja(orden_usuario: str, cerebro_ia):
    """
    Orquesta flujos de trabajo multi-paso analizando la orden del usuario 
    y coordinando los servicios disponibles.
    """
    print(f"[Orchestrator]: Analizando viabilidad de la misión: '{orden_usuario}'")
    
    # EJEMPLO DE FLUJO MULTI-PASO: "Investiga sobre Marte y guárdalo"
    if "investiga" in orden_usuario.lower() and ("guarda" in orden_usuario.lower() or "escribe" in orden_usuario.lower()):
        # Paso 1: Extraer qué quiere investigar (ej. quitarle la palabra investiga)
        tema = orden_usuario.lower().replace("investiga sobre", "").replace("y guárdalo", "").strip()
        
        # Paso 2: Lanzar el Research Service
        datos_encontrados = buscar_y_resumir_tema(tema)
        
        if "Error" in datos_encontrados or "No logré" in datos_encontrados:
            return "Misión abortada en Fase de Investigación. " + datos_encontrados
            
        # Paso 3: Pedirle a Ollama que redacte un resumen ejecutivo refinado con esos datos raw
        prompt_refinado = f"Redacta un resumen ejecutivo muy breve (máximo 2 párrafos) basado en estos datos duros:\n{datos_encontrados}"
        resumen_ia = cerebro_ia.generar_respuesta(prompt_refinado)
        
        # Paso 4: Mandar a guardar la bitácora en PostgreSQL usando el OS Service
        registrar_accion_sistema(
            orden=f"Investigación automatizada de {tema}",
            respuesta=resumen_ia,
            accion_tipo="RESEARCH_TASK"
        )
        
        return f"Misión completada, Señor. He investigado sobre {tema}, procesé los datos de forma local y registré el reporte ejecutivo en su base de datos PostgreSQL."