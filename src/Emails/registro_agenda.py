from datetime import datetime, timedelta
from src.Emails.account_conection import obtener_servicio_calendar


def agendar_evento(titulo: str, fecha_inicio_iso: str, duracion_minutos: int = 60, descripcion: str = "") -> str:
    """
    Agenda un evento en Google Calendar.
    `fecha_inicio_iso` debe venir en formato ISO (ej: '2026-07-29T16:00:00').
    """
    try:
        service = obtener_servicio_calendar()
        
        inicio_dt = datetime.fromisoformat(fecha_inicio_iso)
        fin_dt = inicio_dt + timedelta(minutes=duracion_minutos)

        evento = {
            'summary': titulo,
            'description': descripcion or 'Agendado automáticamente por REVAN AI',
            'start': {
                'dateTime': inicio_dt.isoformat(),
                'timeZone': 'America/Mexico_City',  # Ajusta según tu zona horaria
            },
            'end': {
                'dateTime': fin_dt.isoformat(),
                'timeZone': 'America/Mexico_City',
            },
        }

        evento_creado = service.events().insert(calendarId='primary', body=evento).execute()
        link = evento_creado.get('htmlLink')
        print(f"[CALENDAR]: Evento '{titulo}' agendado con éxito. Link: {link}")
        return f"Evento '{titulo}' agendado para el {inicio_dt.strftime('%d/%m/%Y a las %H:%M')}."

    except Exception as e:
        print(f"[CALENDAR]: Error al agendar evento -> {e}")
        return f"No se pudo agendar el evento debido a un error: {e}"


def consultar_agenda_hoy() -> str:
    """Consulta los eventos agendados para el día de hoy."""
    try:
        service = obtener_servicio_calendar()
        ahora = datetime.utcnow()
        inicio_dia = ahora.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        fin_dia = ahora.replace(hour=23, minute=59, second=59).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary', timeMin=inicio_dia, timeMax=fin_dia,
            singleEvents=True, orderBy='startTime'
        ).execute()

        eventos = events_result.get('items', [])

        if not eventos:
            return "No tienes ningún evento agendado para hoy."

        resumen = "Tus eventos para hoy son:\n"
        for event in eventos:
            inicio = event['start'].get('dateTime', event['start'].get('date'))
            hora = datetime.fromisoformat(inicio).strftime('%H:%M')
            resumen += f"- {event['summary']} a las {hora}\n"

        return resumen

    except Exception as e:
        print(f"[CALENDAR]: Error al consultar la agenda -> {e}")
        return "Hubo un error al intentar consultar tu agenda."


if __name__ == "__main__":
    print("Prueba de consulta de agenda...")
    print(consultar_agenda_hoy())