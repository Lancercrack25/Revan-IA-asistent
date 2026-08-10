"""
Electronics components — detección REAL de hardware conectado.

ANTES: detectar_componentes_electronicos() devolvía una lista fija
hardcodeada ("Arduino", "ESP32", "Raspberry Pi", "Jetson Nano") sin tocar
el sistema para nada -pura decoración que "detectaba" hardware aunque no
hubiera nada conectado-. Ahora usa pyserial para enumerar los puertos
serie REALES del sistema e identificar, por VID/PID y descripción,
cuáles corresponden a chips típicos de Arduino/ESP32.
"""
import serial
# VID:PID y nombres típicos de chips USB-serial usados por Arduino/ESP32
# y clones. No es una lista exhaustiva -el universo de clones chinos con
# VID/PID genéricos es enorme-, pero cubre los casos más comunes.
_FIRMAS_CONOCIDAS = {
    (0x2341, None): "Arduino (oficial)",
    (0x2A03, None): "Arduino (oficial, variante)",
    (0x1A86, 0x7523): "CH340 (Arduino clon / ESP32 genérico)",
    (0x10C4, 0xEA60): "CP210x (ESP32 / ESP8266 típico)",
    (0x0403, 0x6001): "FTDI FT232 (Arduino / otros)",
}


def detectar_puertos_serie() -> list:
    """
    Devuelve una lista de dicts con los puertos serie REALES detectados
    en el sistema ahora mismo:
      {'puerto': 'COM3', 'descripcion': '...', 'identificado_como': str|None}
    """
    resultados = []
    for puerto_info in serial.tools.list_ports.comports():
        identificado_como = None
        for (vid, pid), nombre in _FIRMAS_CONOCIDAS.items():
            if puerto_info.vid == vid and (pid is None or puerto_info.pid == pid):
                identificado_como = nombre
                break

        resultados.append({
            "puerto": puerto_info.device,
            "descripcion": puerto_info.description or "Sin descripción",
            "identificado_como": identificado_como,
        })
    return resultados


def detectar_componentes_electronicos() -> str:
    """
    Punto de entrada para REVAN: texto listo para hablar/mostrar con lo
    que de verdad está conectado ahora mismo, o un aviso claro si no hay
    nada -nunca inventa hardware que no está ahí-.
    """
    puertos = detectar_puertos_serie()

    if not puertos:
        return "No detecté ningún dispositivo electrónico conectado por USB en este momento, Señor."

    lineas_consola = [
        f"{p['puerto']}: {p['identificado_como'] or 'dispositivo no identificado'} ({p['descripcion']})"
        for p in puertos
    ]
    print("[Electronics] Puertos detectados:\n" + "\n".join(lineas_consola))

    resumen_voz = f"Detecté {len(puertos)} dispositivo(s) conectado(s): " + "; ".join(
        f"{p['identificado_como'] or 'algo no identificado'} en {p['puerto']}" for p in puertos
    )
    return resumen_voz


def obtener_puerto_mas_probable():
    """
    Devuelve el puerto del primer dispositivo identificado como
    Arduino/ESP32/similar, o None si no hay ninguno reconocible. Pensado
    para que Coder_agent (u otras funciones de este módulo) lo usen como
    sugerencia real en vez de un placeholder como 'COM3'.
    """
    for p in detectar_puertos_serie():
        if p["identificado_como"]:
            return p["puerto"]
    return None