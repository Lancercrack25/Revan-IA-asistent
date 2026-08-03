import re
import unicodedata
from datetime import datetime, timedelta

_DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
    "viernes": 4, "sabado": 5, "domingo": 6,
}


def _quitar_acentos(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def _resolver_dia_semana(texto_sin_acentos: str, ahora: datetime):
    """
    Busca un nombre de día de la semana en el texto y devuelve cuántos días
    hay que sumar a 'ahora' para llegar a ese día, o None si no encontró
    ninguno.

    ANTES: esta función no existía. Si decías "el viernes" o "el próximo
    lunes", el parser no reconocía nada y fecha_base se quedaba en el valor
    por defecto (HOY), agendando el evento para el día equivocado SIN
    avisar de ningún error. Ahora se detecta explícitamente y, si de
    verdad no encuentra ninguna fecha reconocible, quien llame a
    parsear_fecha_natural puede saberlo (ver 'fecha_reconocida' más abajo).
    """
    es_proximo = bool(re.search(r'\bproximo\b|\bproxima\b|\bque viene\b', texto_sin_acentos))

    for nombre_dia, indice_objetivo in _DIAS_SEMANA.items():
        if re.search(rf'\b{nombre_dia}\b', texto_sin_acentos):
            indice_hoy = ahora.weekday()
            delta = (indice_objetivo - indice_hoy) % 7

            # Si hoy mismo es ese día de la semana:
            #   - "el próximo lunes" (dicho un lunes) -> se refiere al de la
            #     semana que viene, no a hoy -> delta = 7.
            #   - "el lunes" a secas (dicho un lunes) -> se asume que es hoy
            #     -> delta = 0 (comportamiento natural/coloquial).
            if delta == 0 and es_proximo:
                delta = 7

            return delta

    return None


def _resolver_en_n_dias(texto_sin_acentos: str):
    """Reconoce patrones tipo 'en 3 dias' / 'en 2 semanas'."""
    match_dias = re.search(r'\ben\s+(\d+)\s+dias?\b', texto_sin_acentos)
    if match_dias:
        return int(match_dias.group(1))

    match_semanas = re.search(r'\ben\s+(\d+)\s+semanas?\b', texto_sin_acentos)
    if match_semanas:
        return int(match_semanas.group(1)) * 7

    return None


def parsear_fecha_natural(texto: str, devolver_estado: bool = False):
    """
    Convierte una expresión de fecha en lenguaje natural a 'YYYY-MM-DD HH:MM'.

    Reconoce: "hoy", "mañana", "pasado mañana", nombres de día de la semana
    (con o sin "próximo"), y "en N días"/"en N semanas".

    Si 'devolver_estado' es True, devuelve una tupla
    (fecha_str, fecha_reconocida: bool) en vez de solo el string. Esto
    permite que quien llame a esta función sepa si realmente se reconoció
    una fecha o si se usó el valor por defecto (hoy) por no encontrar nada
    -para poder avisarle al usuario en vez de agendar en silencio el día
    equivocado-.
    """
    ahora = datetime.now()
    texto_original = texto.lower().strip()
    texto_sin_acentos = _quitar_acentos(texto_original)
    fecha_base = ahora.date()
    fecha_reconocida = True

    if "pasado manana" in texto_sin_acentos:
        fecha_base += timedelta(days=2)
    elif "manana" in texto_sin_acentos:
        fecha_base += timedelta(days=1)
    elif "hoy" in texto_sin_acentos:
        fecha_base = ahora.date()
    else:
        delta_dia_semana = _resolver_dia_semana(texto_sin_acentos, ahora)
        delta_en_n = _resolver_en_n_dias(texto_sin_acentos)

        if delta_dia_semana is not None:
            fecha_base += timedelta(days=delta_dia_semana)
        elif delta_en_n is not None:
            fecha_base += timedelta(days=delta_en_n)
        else:
            # No se reconoció ninguna fecha explícita: se usa HOY como
            # antes, pero ahora queda marcado como no reconocida para que
            # quien llame pueda advertir al usuario en vez de agendar en
            # silencio para el día equivocado.
            fecha_reconocida = False

    hora = 10
    minuto = 0
    # Buscar patrón de horas con am/pm (ej: 4 pm, 4:30 pm)
    match_ampm = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', texto_sin_acentos)
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
        match_24h = re.search(r'(\d{1,2}):(\d{2})', texto_sin_acentos)
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
    resultado_str = dt_resultado.strftime("%Y-%m-%d %H:%M")

    if devolver_estado:
        return resultado_str, fecha_reconocida
    return resultado_str


if __name__ == "__main__":
    print("🧪 Probando parser de lenguaje natural...")

    ejemplos = [
        "Reunión mañana a las 4 pm",
        "Revisión de código hoy a las 18:30",
        "Cita médica pasado mañana a las 10 am",
        "Junta el viernes a las 10 am",
        "Revisión el próximo lunes a las 4pm",
        "Entrega en 3 dias a las 9 am",
        "Algo sin fecha reconocible a las 5 pm",
    ]

    for ej in ejemplos:
        fecha_parsed, reconocida = parsear_fecha_natural(ej, devolver_estado=True)
        estado = "✅ reconocida" if reconocida else "⚠️ NO reconocida (usó hoy por defecto)"
        print(f"Texto: '{ej}' -> {fecha_parsed}  [{estado}]")