import os
import json
from datetime import datetime, timedelta
# Ruta de almacenamiento local de eventos
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "..", "Database")
AGENDA_PATH = os.path.join(DATABASE_DIR, "agenda.json")

def _cargar_agenda() -> list:
    """Carga los eventos guardados en la base de datos local."""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)

    if os.path.exists(AGENDA_PATH):
        try:
            with open(AGENDA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[AGENDA ERROR]: Error al leer archivo de agenda -> {e}")

    return []

def _guardar_agenda(eventos: list) -> bool:
    """Guarda la lista de eventos en el archivo JSON."""
    try:
        if not os.path.exists(DATABASE_DIR):
            os.makedirs(DATABASE_DIR, exist_ok=True)

        with open(AGENDA_PATH, 'w', encoding='utf-8') as f:
            json.dump(eventos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[AGENDA ERROR]: Error al guardar evento -> {e}")
        return False

def agendar_evento(titulo: str, fecha_hora_str: str, duracion_minutos: int = 60, descripcion: str = "") -> str:
    try:
        dt_inicio = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M")
        dt_fin = dt_inicio + timedelta(minutes=duracion_minutos)

        nuevo_evento = {
            "id": int(datetime.now().timestamp()),
            "titulo": titulo,
            "inicio": dt_inicio.strftime("%Y-%m-%d %H:%M"),
            "fin": dt_fin.strftime("%Y-%m-%d %H:%M"),
            "descripcion": descripcion or "Agendado por REVAN Assistant"
        }

        eventos = _cargar_agenda()
        eventos.append(nuevo_evento)

        if _guardar_agenda(eventos):
            return f"Señor, he agendado '{titulo}' para el {dt_inicio.strftime('%d/%m/%Y a las %H:%M')}."
        return "No se pudo guardar el evento en la base de datos."

    except ValueError:
        return "Formato de fecha inválido. Use el formato 'YYYY-MM-DD HH:MM' (ej: 2026-07-30 15:30)."
    except Exception as e:
        return f"Error al agendar evento: {e}"

def consultar_agenda_hoy() -> str:
    """Muestra los eventos programados para la fecha actual."""
    eventos = _cargar_agenda()
    hoy_str = datetime.now().strftime("%Y-%m-%d")

    eventos_hoy = [e for e in eventos if e["inicio"].startswith(hoy_str)]

    if not eventos_hoy:
        return "Señor, no tiene ningún evento agendado para hoy."

    respuesta = "Sus eventos agendados para hoy son:\n"
    for ev in eventos_hoy:
        hora = ev["inicio"].split(" ")[1]
        respuesta += f"• {ev['titulo']} a las {hora}\n"
    return respuesta

if __name__ == "__main__":
    print("Prueba de agenda local...")
    print(consultar_agenda_hoy())