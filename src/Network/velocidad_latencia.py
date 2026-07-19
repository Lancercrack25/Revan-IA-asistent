#este archivo se encarga de medir velocidad de internet y latencia (tiempo de respuesta) de la red
import subprocess
import platform
import re


def medir_latencia(host: str = "8.8.8.8", intentos: int = 4):
    """
    Mide la latencia (tiempo de ida y vuelta) hacia un host, usando el
    comando 'ping' nativo del sistema operativo (no requiere librerías
    extra ni privilegios especiales).
    Devuelve un dict con promedio/mínimo/máximo en ms, o None si falló.
    """
    sistema = platform.system().lower()
    if "windows" in sistema:
        cmd = ["ping", "-n", str(intentos), host]
    else:
        cmd = ["ping", "-c", str(intentos), host]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=intentos + 10)
        salida = resultado.stdout
    except Exception as e:
        print(f"[Latencia]: Error al ejecutar ping: {e}")
        return None

    # Soporta tanto "tiempo=Xms" (Windows en español) como "time=Xms" (Windows
    # en inglés / Linux / macOS)
    tiempos = [float(m) for m in re.findall(r"(?:tiempo|time)[=<]\s*(\d+(?:\.\d+)?)\s*ms", salida, re.IGNORECASE)]

    if not tiempos:
        return None

    return {
        "promedio_ms": sum(tiempos) / len(tiempos),
        "minimo_ms": min(tiempos),
        "maximo_ms": max(tiempos),
        "paquetes_recibidos": len(tiempos),
        "paquetes_enviados": intentos,
    }


def reportar_latencia(host: str = "8.8.8.8") -> str:
    """Versión hablable de medir_latencia()."""
    stats = medir_latencia(host)
    if not stats:
        return "No pude medir la latencia de su red, Señor. Verifique su conexión."

    perdidos = stats["paquetes_enviados"] - stats["paquetes_recibidos"]
    texto = f"Latencia promedio de {stats['promedio_ms']:.0f} milisegundos."

    if perdidos > 0:
        texto += f" Se perdieron {perdidos} de {stats['paquetes_enviados']} paquetes enviados."

    return texto


def probar_velocidad_internet() -> str:
    """
    Prueba de velocidad REAL de descarga/subida. Tarda entre 10 y 30
    segundos típicamente, así que solo debe llamarse cuando el usuario lo
    pide de forma explícita, nunca como parte de un chequeo rápido.
    Requiere: pip install speedtest-cli
    """
    try:
        import speedtest
    except ImportError:
        return ("No tengo instalada la herramienta de prueba de velocidad, Señor. "
                "Ejecute: pip install speedtest-cli")

    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        bajada_mbps = st.download() / 1_000_000
        subida_mbps = st.upload() / 1_000_000
        return (f"Su velocidad de descarga es de {bajada_mbps:.1f} megabits por segundo, "
                f"y de subida, {subida_mbps:.1f} megabits por segundo.")
    except Exception as e:
        return f"No pude completar la prueba de velocidad, Señor. Detalle: {e}"


if __name__ == "__main__":
    print(reportar_latencia())
    print(probar_velocidad_internet())