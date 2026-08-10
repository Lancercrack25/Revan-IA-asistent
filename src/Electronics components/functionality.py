"""
Electronics components — detección REAL de hardware conectado.
Tres capas de detección, cada una opcional/independiente:
  1. Puertos serie (Arduino/ESP32/clones) vía pyserial.
  2. Dispositivos USB genéricos -CUALQUIER periférico, no solo los de
     puerto serie- vía WMI (solo funciona en Windows; en otros sistemas
     devuelve lista vacía sin fallar).
  3. Dispositivos Bluetooth (BLE) cercanos vía bleak.

ANTES: detectar_componentes_electronicos() devolvía una lista fija
hardcodeada ("Arduino", "ESP32", "Raspberry Pi", "Jetson Nano") sin tocar
el sistema para nada. Ahora todo lo que reporta viene de una consulta
real al sistema operativo o al hardware.
"""

import os
import asyncio
import serial.tools.list_ports

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


def detectar_dispositivos_usb_genericos() -> list:
    """
    Lista TODOS los dispositivos USB conectados (no solo los de puerto
    serie: sensores, módulos, periféricos sin puerto COM) usando WMI.
    Solo funciona en Windows -requiere 'pip install wmi pywin32'-; en
    cualquier otro sistema, o si no está instalado, devuelve lista vacía
    sin fallar.
    """
    if os.name != "nt":
        return []

    try:
        import wmi
    except ImportError:
        print("[Electronics] Módulo 'wmi' no instalado (pip install wmi pywin32) -detección USB genérica desactivada-.")
        return []

    try:
        conexion_wmi = wmi.WMI()
        dispositivos = []
        for dispositivo in conexion_wmi.Win32_PnPEntity():
            nombre = dispositivo.Name
            id_dispositivo = (dispositivo.DeviceID or "").upper()
            if nombre and "USB" in id_dispositivo:
                dispositivos.append(nombre)
        return dispositivos
    except Exception as e:
        print(f"[Electronics] Error consultando WMI: {e}")
        return []


def detectar_dispositivos_bluetooth(duracion_segundos: float = 5.0) -> list:
    """
    Escanea dispositivos Bluetooth (BLE) cercanos durante
    'duracion_segundos'. Requiere Bluetooth activo en el equipo y la
    librería 'bleak' instalada.
    """
    try:
        from bleak import BleakScanner
    except ImportError:
        print("[Electronics] Módulo 'bleak' no instalado -detección Bluetooth desactivada-.")
        return []

    async def _escanear():
        dispositivos = await BleakScanner.discover(timeout=duracion_segundos)
        return [f"{d.name or 'Desconocido'} ({d.address})" for d in dispositivos]

    try:
        return asyncio.run(_escanear())
    except Exception as e:
        print(f"[Electronics] Error escaneando Bluetooth: {e}")
        return []


def detectar_componentes_electronicos(incluir_usb_genericos: bool = True,
                                       incluir_bluetooth: bool = False) -> str:
    """
    Punto de entrada para REVAN: texto listo para hablar/mostrar con lo
    que de verdad está conectado ahora mismo, o un aviso claro si no hay
    nada -nunca inventa hardware que no está ahí-.

    Por defecto incluye puertos serie + USB genéricos (rápido, <1s).
    Bluetooth queda desactivado por defecto porque el escaneo tarda
    varios segundos -actívalo con incluir_bluetooth=True cuando de verdad
    lo necesites-.
    """
    partes_voz = []
    partes_consola = []

    puertos = detectar_puertos_serie()
    if puertos:
        partes_voz.append(
            f"{len(puertos)} dispositivo(s) por puerto serie: " +
            "; ".join(f"{p['identificado_como'] or 'no identificado'} en {p['puerto']}" for p in puertos)
        )
        partes_consola.extend(
            f"[Serie] {p['puerto']}: {p['identificado_como'] or 'no identificado'} ({p['descripcion']})"
            for p in puertos
        )

    if incluir_usb_genericos:
        usb_genericos = detectar_dispositivos_usb_genericos()
        if usb_genericos:
            partes_voz.append(f"{len(usb_genericos)} dispositivo(s) USB adicionales")
            partes_consola.extend(f"[USB] {d}" for d in usb_genericos)

    if incluir_bluetooth:
        bt = detectar_dispositivos_bluetooth()
        if bt:
            partes_voz.append(f"{len(bt)} dispositivo(s) Bluetooth cercanos")
            partes_consola.extend(f"[Bluetooth] {d}" for d in bt)

    if partes_consola:
        print("[Electronics] Detección completa:\n" + "\n".join(partes_consola))

    if not partes_voz:
        return "No detecté ningún dispositivo electrónico conectado en este momento, Señor."

    return "Detecté: " + "; ".join(partes_voz) + ". Revise la consola de REVAN para el detalle completo."


def obtener_puerto_mas_probable():
    """
    Devuelve el puerto del primer dispositivo identificado como
    Arduino/ESP32/similar, o None si no hay ninguno reconocible.
    """
    for p in detectar_puertos_serie():
        if p["identificado_como"]:
            return p["puerto"]
    return None