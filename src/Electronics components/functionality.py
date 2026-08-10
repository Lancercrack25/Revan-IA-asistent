"""
Electronics components — Detección EXCLUSIVA de microcontroladores y hardware de desarrollo.
Filtra periféricos comunes (teclados, mouses, webcams, hubs USB) para reportar solo devboards.
"""
import os
import asyncio
import serial.tools.list_ports

# 🎯 FIRMAS AMPLIADAS: Microcontroladores, adaptadores USB-TTL y DevBoards comunes
_FIRMAS_CONOCIDAS = {
    # Arduino Oficiales
    (0x2341, None): "Arduino (Oficial)",
    (0x2A03, None): "Arduino (Oficial Variante)",
    # ESP32 / ESP8266 / Clones (Chips USB-Serie más comunes)
    (0x1A86, 0x7523): "ESP32 / Arduino (CH340)",
    (0x1A86, 0x55D4): "ESP32-S3 / CH343",
    (0x10C4, 0xEA60): "ESP32 / ESP8266 (CP210x)",
    (0x0403, 0x6001): "DevBoard / Adaptador FTDI (FT232R)",
    (0x0403, 0x6015): "DevBoard / Adaptador FTDI (FT230X)",
    # Raspberry Pi Pico / STM32
    (0x2E8A, 0x0005): "Raspberry Pi Pico (MicroPython/C++)",
    (0x0483, 0x374B): "STM32 Nucleo / ST-Link",
}

# 🚫 Palabras clave a IGNORAR en WMI para evitar falsos positivos
_PALABRAS_IGNORAR = [
    "KEYBOARD", "MOUSE", "TECLADO", "RATON", "CAMERA", "CAMARA", "WEBCAM", 
    "AUDIO", "MICROPHONE", "MICROFONO", "SPEAKER", "HUB", "ROOT_HUB", 
    "HOST CONTROLLER", "BLUETOOTH", "MASS STORAGE", "ALMACENAMIENTO"
]

# ⚡ Palabras clave PERMITIDAS si se busca por USB WMI
_PALABRAS_ELECTRONICA = [
    "ESP32", "ARDUINO", "CH340", "CP210", "FTDI", "STM32", "PICO", 
    "RASPBERRY", "SILICON LABS", "SERIAL", "UART", "PROLIFIC"
]


def detectar_puertos_serie() -> list:
    """
    Devuelve ÚNICAMENTE puertos serie activos que correspondan a microcontroladores 
    o convertidores USB-UART conocidos.
    """
    resultados = []
    for puerto_info in serial.tools.list_ports.comports():
        identificado_como = None
        
        # 1. Comparar por Vendor ID (VID) y Product ID (PID)
        for (vid, pid), nombre in _FIRMAS_CONOCIDAS.items():
            if puerto_info.vid == vid and (pid is None or puerto_info.pid == pid):
                identificado_como = nombre
                break

        # 2. Si no coincide el VID/PID pero la descripción tiene pistas claras de electrónica
        desc_upper = (puerto_info.description or "").upper()
        if not identificado_como:
            for kw in _PALABRAS_ELECTRONICA:
                if kw in desc_upper:
                    identificado_como = f"Dispositivo Electrónico ({puerto_info.description})"
                    break

        # Omitir puertos serie integrados del sistema (ej. COM1 clásico de tarjeta madre) que no sean USB
        if puerto_info.vid is None and "USB" not in (puerto_info.hwid or "").upper():
            continue

        resultados.append({
            "puerto": puerto_info.device,
            "descripcion": puerto_info.description or "Sin descripción",
            "identificado_como": identificado_como or "Puerto Serie (Desconocido)",
        })
    return resultados


def detectar_dispositivos_usb_genericos() -> list:
    """
    Filtra estrictamente los dispositivos WMI en Windows para traer SOLO tarjetas 
    de desarrollo o componentes de electrónica, ignorando periféricos de PC.
    """
    if os.name != "nt":
        return []

    try:
        import wmi
    except ImportError:
        return []

    try:
        conexion_wmi = wmi.WMI()
        dispositivos = []
        for dispositivo in conexion_wmi.Win32_PnPEntity():
            nombre = (dispositivo.Name or "").upper()
            id_disp = (dispositivo.DeviceID or "").upper()
            
            if not nombre or "USB" not in id_disp:
                continue

            # Descartar periféricos comunes
            if any(ignorar in nombre for ignorar in _PALABRAS_IGNORAR):
                continue

            # Aceptar solo si coincide con hardware de electrónica
            if any(kw in nombre for kw in _PALABRAS_ELECTRONICA):
                dispositivos.append(dispositivo.Name)

        return dispositivos
    except Exception as e:
        print(f"[Electronics] Error consultando WMI: {e}")
        return []


def detectar_dispositivos_bluetooth(duracion_segundos: float = 3.0) -> list:
    """
    Escanea BLE pero filtrando únicamente dispositivos con nombres que sugieran 
    módulos electrónicos (ESP32, HC-05, etc.).
    """
    try:
        from bleak import BleakScanner
    except ImportError:
        return []

    async def _escanear():
        dispositivos = await BleakScanner.discover(timeout=duracion_segundos)
        filtrados = []
        for d in dispositivos:
            nombre = (d.name or "").upper()
            if any(kw in nombre for kw in _PALABRAS_ELECTRONICA) or "HC-" in nombre:
                filtrados.append(f"{d.name} ({d.address})")
        return filtrados

    try:
        return asyncio.run(_escanear())
    except Exception:
        return []


def detectar_componentes_electronicos(incluir_usb_genericos: bool = False,
                                       incluir_bluetooth: bool = False) -> str:
    """
    Punto de entrada principal para REVAN. Por defecto desactiva la búsqueda 
    USB genérica para enfocarse 100% en puertos COM/Serie activos (ESP32/Arduino).
    """
    partes_voz = []
    partes_consola = []

    # Detección por Puertos Serie (La más fiable para ESP32/Arduino)
    puertos = detectar_puertos_serie()
    if puertos:
        partes_voz.append(
            f"{len(puertos)} tarjeta(s) de desarrollo: " +
            "; ".join(f"{p['identificado_como']} en {p['puerto']}" for p in puertos)
        )
        partes_consola.extend(
            f"[Serie] {p['puerto']}: {p['identificado_como']} ({p['descripcion']})"
            for p in puertos
        )

    # Detección USB WMI Filtrada
    if incluir_usb_genericos:
        usb_electronica = detectar_dispositivos_usb_genericos()
        if usb_electronica:
            partes_voz.append(f"{len(usb_electronica)} componente(s) USB adicional(es)")
            partes_consola.extend(f"[USB Módulo] {d}" for d in usb_electronica)

    # Bluetooth BLE Filtrado
    if incluir_bluetooth:
        bt = detectar_dispositivos_bluetooth()
        if bt:
            partes_voz.append(f"{len(bt)} módulo(s) Bluetooth")
            partes_consola.extend(f"[Bluetooth BLE] {d}" for d in bt)

    if partes_consola:
        print("[Electronics] Hardware detectado:\n" + "\n".join(partes_consola))

    if not partes_voz:
        return "No detecté ninguna tarjeta de desarrollo ni microcontrolador conectado, Señor."

    return "Detecté: " + "; ".join(partes_voz) + "."


def obtener_puerto_mas_probable():
    """
    Devuelve el puerto COM del primer ESP32/Arduino reconocido.
    """
    puertos = detectar_puertos_serie()
    if puertos:
        return puertos[0]["puerto"]
    return None