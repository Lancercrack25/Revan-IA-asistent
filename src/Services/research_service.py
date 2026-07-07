import sys
import os
import requests
from bs4 import BeautifulSoup

sys.dont_write_bytecode = True

def buscar_y_resumir_tema(termino_busqueda: str):
    """
    Realiza una consulta rápida en la web, extrae el contenido de texto 
    esencial y prepara los datos para que Ollama los sintetice.
    """
    if not termino_busqueda.strip():
        return "No se especificó ningún término de investigación, Señor."

    print(f"[Research Service]: Buscando información sobre '{termino_busqueda}'...")
    
    # Usamos un motor de búsqueda libre como Wikipedia o DuckDuckGo HTML para no requerir API Keys pagadas
    url = f"https://es.wikipedia.org/wiki/{termino_busqueda.replace(' ', '_')}"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        respuesta = requests.get(url, headers=headers, timeout=5)
        
        if respuesta.status_code != 200:
            return f"No logré encontrar un artículo directo para '{termino_busqueda}' en la red principal."
            
        # Parseamos el HTML de forma ultra veloz
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        párrafos = soup.find_all('p')
        
        # Juntamos los primeros 3 párrafos informativos para no saturar el contexto de Ollama
        texto_limpio = "\n".join([p.text for p in párrafos[:3] if p.text.strip()])
        
        if not texto_limpio.strip():
            return "La estructura del sitio web no permitió extraer texto legible."
            
        return texto_limpio
        
    except Exception as e:
        return f"Error en la interconexión con el módulo de red: {e}"