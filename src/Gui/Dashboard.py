import customtkinter as ctk
import tkinter as tk
import math
from src.Gui.styles.css import *

class RevanGUI:
    def __init__(self, titulo_usuario="Maestro"):
        self.titulo_usuario = titulo_usuario
        
        # 1. Configuración de la Ventana Principal
        self.app = ctk.CTk()
        self.app.title("REVAN - Interface")
        self.app.geometry("480x680")
        self.app.resizable(False, False)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # 2. Contenedor Principal (Tarjeta estilo Web)
        self.card = ctk.CTkFrame(master=self.app, corner_radius=16, fg_color=COLOR_TARJETA, border_width=1, border_color=COLOR_BORDE)
        self.card.pack(pady=15, padx=20, fill="both", expand=True)

        # Título del Sistema
        self.lbl_titulo = ctk.CTkLabel(master=self.card, text="🌌 REVAN V1.0", font=("Segoe UI", 20, "bold"), text_color=COLOR_TEXTO_AZUL)
        self.lbl_titulo.pack(pady=(15, 2))

        # Subtítulo de Usuario
        self.lbl_subtitulo = ctk.CTkLabel(master=self.card, text=f"Operador: {self.titulo_usuario}", font=("Segoe UI", 12), text_color=COLOR_TEXTO_GRIS)
        self.lbl_subtitulo.pack(pady=(0, 10))

        # -------------------------------------------------------------
        # 🛸 EL NÚCLEO HOLOGRÁFICO DINÁMICO (CANVAS ANIMADO)
        # -------------------------------------------------------------
        self.canvas_size = 140
        self.canvas = tk.Canvas(
            self.card, 
            width=self.canvas_size, 
            height=self.canvas_size, 
            bg=COLOR_TARJETA, 
            highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Variables de control de la animación del arco y pulso
        self.angulo_rotacion = 0
        self.radio_pulso = 45
        self.direccion_pulso = 0.5
        self.estado_actual = "espera"  # "espera", "escuchando", "pensando", "hablando"
        
        # Arrancar el bucle de renderizado del núcleo
        self.animar_nucleo()
        # -------------------------------------------------------------

        # Indicador de Estado estilo Píldora
        self.lbl_status = ctk.CTkLabel(
            master=self.card, 
            text="⚡ SISTEMAS EN ESPERA", 
            font=("Consolas", 11, "bold"),
            text_color=COLOR_CYAN_STATUS,
            fg_color=COLOR_FONDO_STATUS,
            corner_radius=20,
            height=28,
            width=180
        )
        self.lbl_status.pack(pady=5)

        # 3. Área de Chat
        self.txt_chat = ctk.CTkTextbox(
            master=self.card, 
            font=("Segoe UI", 12),
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDE,
            fg_color=COLOR_FONDO_PRINCIPAL,
            text_color="#c9d1d9",
            wrap="word"
        )
        self.txt_chat.pack(pady=10, padx=20, fill="both", expand=True)
        self.txt_chat.configure(state="disabled")

        # 4. Botón de Apagado de Emergencia
        self.btn_control = ctk.CTkButton(
            master=self.card, 
            text="APAGAR SISTEMAS", 
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_BOTON_BG,
            hover_color=COLOR_ROJO_PELIGRO,
            text_color=COLOR_ROJO_PELIGRO,
            border_width=1,
            border_color=COLOR_ROJO_PELIGRO,
            corner_radius=8,
            height=35,
            cursor="hand2",
            command=self.solicitar_cierre
        )
        self.btn_control.pack(pady=15, padx=20, fill="x")
        
        self.debe_cerrar = False

    def animar_nucleo(self):
        """Dibuja y actualiza los gráficos vectoriales del núcleo al estilo JARVIS."""
        self.canvas.delete("all")
        cx, cy = self.canvas_size // 2, self.canvas_size // 2

        # 1. Modificar físicas de la animación según el estado de REVAN
        velocidad_rotacion = 2
        if self.estado_actual == "escuchando":
            velocidad_rotacion = 6
            # Efecto latido rápido
            self.radio_pulso += self.direccion_pulso * 2
            if self.radio_pulso > 52 or self.radio_pulso < 42:
                self.direccion_pulso *= -1
        elif self.estado_actual == "pensando":
            velocidad_rotacion = 12  # Giro ultra rápido de procesamiento
        elif self.estado_actual == "hablando":
            velocidad_rotacion = 4
            # Latido constante y expansivo al hablar
            self.radio_pulso += self.direccion_pulso * 1.5
            if self.radio_pulso > 55 or self.radio_pulso < 40:
                self.direccion_pulso *= -1
        else:  # Modo espera
            velocidad_rotacion = 1
            # Latido lento de "respiración"
            self.radio_pulso += self.direccion_pulso * 0.3
            if self.radio_pulso > 47 or self.radio_pulso < 43:
                self.direccion_pulso *= -1

        self.angulo_rotacion = (self.angulo_rotacion + velocidad_rotacion) % 360

        # 2. Renderizar Anillo Base de Fondo (Atenuado)
        self.canvas.create_oval(cx-55, cy-55, cx+55, cy+55, outline=COLOR_NUCLEO_ATENUADO, width=1, dash=(4, 4))

        # 3. Renderizar el Anillo Central de Pulso Vibratorio
        color_pulso = COLOR_ROJO_PELIGRO if self.estado_actual == "error" else COLOR_NUCLEO_PRINCIPAL
        self.canvas.create_oval(cx-self.radio_pulso, cy-self.radio_pulso, cx+self.radio_pulso, cy+self.radio_pulso, outline=color_pulso, width=2)

        # 4. Renderizar Arcos Holográficos Giratorios (Estilo Jarvis/Líneas de Círculo)
        # Convertimos ángulos a radianes para dibujar las líneas segmentadas giratorias
        for i in range(0, 360, 60):
            ang = math.radians(self.angulo_rotacion + i)
            x1 = cx + 58 * math.cos(ang)
            y1 = cy + 58 * math.sin(ang)
            x2 = cx + 64 * math.cos(ang)
            y2 = cy + 64 * math.sin(ang)
            self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_NUCLEO_PRINCIPAL, width=2)

        # Círculo central estático (El ojo del asistente)
        self.canvas.create_oval(cx-8, cy-8, cx+8, cy+8, fill=COLOR_NUCLEO_PRINCIPAL, outline="")

        # Re-programar el siguiente fotograma (Aprox 30 FPS para máxima fluidez)
        self.app.after(33, self.animar_nucleo)

    def actualizar_estado(self, texto_estado: str, color_hex: str):
        """Cambia el texto de la píldora y actualiza el comportamiento del núcleo."""
        self.lbl_status.configure(text=texto_estado.upper(), text_color=color_hex)
        
        # Mapeamos el string al estado del motor gráfico
        if "ESCUCHANDO" in texto_estado.upper():
            self.estado_actual = "escuchando"
        elif "PENSANDO" in texto_estado.upper():
            self.estado_actual = "pensando"
        elif "IN LÍNEA" in texto_estado.upper() or "HABLANDO" in texto_estado.upper():
            # Si está ejecutando audio (hablando) o en línea listo
            self.estado_actual = "hablando" if "HABLANDO" in texto_estado.upper() else "espera"
        elif "ERROR" in texto_estado.upper() or "DESCONECTANDO" in texto_estado.upper():
            self.estado_actual = "error"
        else:
            self.estado_actual = "espera"
            
        self.app.update_idletasks()

    def agregar_mensaje(self, emisor: str, mensaje: str):
        self.txt_chat.configure(state="normal")
        if emisor.lower() == "tu":
            self.txt_chat.insert("end", f"👤 Tú: {mensaje}\n\n")
        else:
            self.txt_chat.insert("end", f"🤖 REVAN: {mensaje}\n\n")
        self.txt_chat.see("end")
        self.txt_chat.configure(state="disabled")
        self.app.update_idletasks()

    def solicitar_cierre(self):
        self.debe_cerrar = True