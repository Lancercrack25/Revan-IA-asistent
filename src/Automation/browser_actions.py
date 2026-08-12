import subprocess
import urllib.parse

def reproducir_video_brave(url_o_busqueda):
    """Abre una URL o busca un video en YouTube forzando el navegador Brave."""
    try:
        if not url_o_busqueda.startswith("http"):
            consulta = urllib.parse.quote_plus(url_o_busqueda)
            url_final = f"https://www.youtube.com/results?search_query={consulta}"
        else:
            url_final = url_o_busqueda
        subprocess.Popen(["cmd", "/c", "start", "brave", url_final], shell=False)
        return "Abriendo la transmisión solicitada en el navegador Brave, Señor."
    except Exception as e:
        return f"Error al abrir Brave: {str(e)}"