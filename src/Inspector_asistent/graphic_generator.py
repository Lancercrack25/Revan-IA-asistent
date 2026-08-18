import os
import json
import threading
import matplotlib.pyplot as plt

# Aplicar estilo oscuro base
plt.style.use('dark_background')
# Ruta para guardar el historial de análisis en JSON
HISTORIAL_PATH = os.path.join(os.path.dirname(__file__), "historial_telemetria.json")

def _cargar_historial() -> dict:
    """Carga el historial guardado o genera una estructura inicial."""
    if os.path.exists(HISTORIAL_PATH):
        try:
            with open(HISTORIAL_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[INSPECTOR GRAPHIC]: Error al leer historial: {e}")
    
    return {
        "labels": ["Escan 1", "Escan 2", "Escan 3"],
        "errores": [12, 8, 5],
        "warnings": [18, 12, 9]
    }

def registrar_nuevo_escaneo(errores: int, warnings: int, max_puntos: int = 7) -> dict:
    """Registra los resultados de una nueva inspección en el JSON local."""
    historial = _cargar_historial()
    num_escaneo = len(historial["labels"]) + 1
    historial["labels"].append(f"Escan {num_escaneo}")
    historial["errores"].append(errores)
    historial["warnings"].append(warnings)
    # Limitar la cantidad de puntos en el eje X para mantener la gráfica scannable
    if len(historial["labels"]) > max_puntos:
        historial["labels"] = historial["labels"][-max_puntos:]
        historial["errores"] = historial["errores"][-max_puntos:]
        historial["warnings"] = historial["warnings"][-max_puntos:]

    try:
        with open(HISTORIAL_PATH, 'w', encoding='utf-8') as f:
            json.dump(historial, f, indent=4)
    except Exception as e:
        print(f"[INSPECTOR GRAPHIC]: Error al guardar historial: {e}")
    return historial

def _renderizar_y_mostrar(historico_labels, historico_errores, historico_warnings, guardar_en_disco, mostrar_pantalla, ruta_salida):
    """Función interna que crea la figura de Matplotlib."""
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)
    fig.patch.set_facecolor('#0a0f19')  # Fondo externo muy oscuro
    ax.set_facecolor('#0d1322')         # Fondo interno del plot
    # Trazar líneas de neón
    ax.plot(
        historico_labels, historico_errores, 
        color='#ff0055', marker='o', linewidth=2.5, markersize=6, 
        label='Errores Críticos'
    )
    ax.plot(
        historico_labels, historico_warnings, 
        color='#ffcc00', marker='s', linewidth=2.5, markersize=6, 
        label='Advertencias / Warnings'
    )

    # Sombras bajo la curva
    ax.fill_between(historico_labels, historico_errores, color='#ff0055', alpha=0.15)
    ax.fill_between(historico_labels, historico_warnings, color='#ffcc00', alpha=0.1)

    # Estilos del HUD
    ax.set_title("REVAN // TELEMETRÍA DE SALUD DEL CÓDIGO", color='#00ff88', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Histórico de Escaneos Tácticos", color='#888888', fontsize=9)
    ax.set_ylabel("Fallas Detectadas", color='#888888', fontsize=9)

    ax.grid(True, linestyle='--', alpha=0.15, color='#ffffff')

    for spine in ax.spines.values():
        spine.set_color('#00ff88')
        spine.set_linewidth(0.8)

    ax.tick_params(colors='#aaaaaa', labelsize=8)

    legend = ax.legend(facecolor='#0a0f19', edgecolor='#00ff88', fontsize=9)
    for text in legend.get_texts():
        text.set_color('#ffffff')

    plt.tight_layout()

    if guardar_en_disco:
        plt.savefig(ruta_salida, facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"[INSPECTOR GRAPHIC]: Gráfica guardada en -> {ruta_salida}")

    if mostrar_pantalla:
        plt.show()

    plt.close(fig)


def generar_grafica_telemetria_inspector(
    historico_labels=None, 
    historico_errores=None, 
    historico_warnings=None, 
    guardar_en_disco=True,
    mostrar_pantalla=False,
    en_segundo_plano=True
) -> str:
    """Genera la gráfica de telemetría táctica."""
    
    # Cargar datos si no se especifican directamente
    if not historico_labels or not historico_errores or not historico_warnings:
        datos = _cargar_historial()
        historico_labels = datos["labels"]
        historico_errores = datos["errores"]
        historico_warnings = datos["warnings"]

    ruta_salida = os.path.join(os.path.dirname(__file__), "telemetria_inspector.png")

    args_render = (
        historico_labels, historico_errores, historico_warnings,
        guardar_en_disco, mostrar_pantalla, ruta_salida
    )

    if en_segundo_plano and mostrar_pantalla:
        hilo = threading.Thread(target=_renderizar_y_mostrar, args=args_render, daemon=True)
        hilo.start()
    else:
        _renderizar_y_mostrar(*args_render)

    return ruta_salida 

if __name__ == "__main__":
    print("Prueba directa del módulo gráfico...")
    generar_grafica_telemetria_inspector(mostrar_pantalla=True, en_segundo_plano=False)