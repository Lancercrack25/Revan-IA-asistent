import re
from datetime import datetime, timedelta

def parsear_fecha_natural(texto: str) -> str:
    ahora = datetime.now()
    texto = texto.lower().strip()
    fecha_base = ahora.date()
    
    if "pasado mañana" in texto:
        fecha_base += timedelta(days=2)
    elif "mañana" in texto:
        fecha_base += timedelta(days=1)
    elif "hoy" in texto:
        fecha_base = ahora.date()

    hora = 10  # Hora por defecto (10:00 AM) si no especifica
    minuto = 0
    # Buscar patrón de horas con am/pm (ej: 4 pm, 4:30 pm)
    match_ampm = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', texto)
    if match_ampm:
        h = int(match_ampm.group(1))
        m = int(match_ampm.group(2)) if match_ampm.group(2) else 0
        meridiano = match_ampm.group(3)

        if meridiano == "pm" and h < 12:
            h += 12
        elif meridiano == "am" and h == 12:
            h = 0
        hora, minuto = h, m

    else:
        # Buscar formato 24 horas (ej: 16:30 o 16:00)
        match_24h = re.search(r'(\d{1,2}):(\d{2})', texto)
        if match_24h:
            hora = int(match_24h.group(1))
            minuto = int(match_24h.group(2))
    # Construir objeto datetime completo
    dt_resultado = datetime(
        year=fecha_base.year,
        month=fecha_base.month,
        day=fecha_base.day,
        hour=hora,
        minute=minuto
    )

    return dt_resultado.strftime("%Y-%m-%d %H:%M")

if __name__ == "__main__":
    print("🧪 Probando parser de lenguaje natural...")
    
    ejemplos = [
        "Reunión mañana a las 4 pm",
        "Revisión de código hoy a las 18:30",
        "Cita médica pasado mañana a las 10 am"
    ]

    for ej in ejemplos:
        fecha_parsed = parsear_fecha_natural(ej)
        print(f"Texto: '{ej}' ➔ Interpretado como: {fecha_parsed}")