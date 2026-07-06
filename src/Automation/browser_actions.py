import subprocess

def reproducir_video_brave(url_o_busqueda):
    """Abre una URL o busca un video en YouTube forzando el navegador Brave."""
    try:
        if not url_o_busqueda.startswith("http"):
            url_final = f"https://www.youtube.com/results?search_query={url_o_busqueda.replace(' ', '+')}"
        else:
            url_final = url_o_busqueda

        subprocess.Popen(f'start brave "{url_final}"', shell=True)
        return "Abriendo la transmisión solicitada en el navegador Brave, Señor."
    except Exception as e:
        return f"Error al abrir Brave: {str(e)}"