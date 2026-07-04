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
        # 🛸 EL NÚCLEO HOLOGRÁFICO CON ONDAS EXPANSIVAS
        # -------------------------------------------------------------
        self.canvas_size = 180 # Lo hacemos un poco más grande para las ondas
        self.canvas = tk.Canvas(
            self.card, 
            width=self.canvas_size, 
            height=self.canvas_size, 
            bg=COLOR_TARJETA, 
            highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Variables de control de animación
        self.angulo_rotacion = 0
        self.radio_base = 35
        self.ondas = []        # Lista que guardará el radio actual de cada onda expansiva
        self.estado_actual = "espera"
        self.ticks = 0         # Temporizador interno para generar ondas consecutivas
        
        # Arrancar el bucle gráfico
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
        """Dibuja el núcleo Jarvis y genera ondas expansivas que se desvanecen hacia afuera."""
        self.canvas.delete("all")
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        self.ticks += 1

        # 1. Configurar velocidades e intensidades según el estado
        velocidad_rotacion = 2
        frecuencia_onda = 25  # Cada cuántos fotogramas nace una onda nueva
        velocidad_onda = 1.0  # Qué tan rápido crece la onda hacia afuera

        if self.estado_actual == "escuchando":
            velocidad_rotacion = 5
            frecuencia_onda = 12   # Ondas más seguidas al escuchar
            velocidad_onda = 2.0   # Ondas más rápidas y enérgicas
        elif self.estado_actual == "pensando":
            velocidad_rotacion = 14  # Giro loco de procesamiento
            frecuencia_onda = 999   # Sin ondas al pensar, solo rotación pura
        elif self.estado_actual == "hablando":
            velocidad_rotacion = 3
            frecuencia_onda = 8    # ¡Máximo flujo de ondas expansivas!
            velocidad_onda = 2.5   # Ondas largas y veloces de sonido

        # Actualizar ángulo de las aspas holográficas
        self.angulo_rotacion = (self.angulo_rotacion + velocidad_rotacion) % 360

        # 2. PROCESAR Y DIBUJAR ONDAS EXPANSIVAS (El efecto película)
        # Nace una nueva onda desde el centro si corresponde
        if self.ticks % frecuencia_onda == 0 and self.estado_actual != "pensando":
            self.ondas.append(self.radio_base)

        nuevas_ondas = []
        for r in self.ondas:
            # Hacer crecer la onda hacia afuera
            r_nuevo = r + velocidad_onda
            
            # Si supera los límites del Canvas, la descartamos
            if r_nuevo < (self.canvas_size // 2) - 5:
                nuevas_ondas.append(r_nuevo)
                
                # Calcular atenuación visual simulando opacidad por líneas segmentadas
                # A mayor distancia, la línea del radar se vuelve más delgada y discontinua
                distancia_maxima = (self.canvas_size // 2) - 5
                porcentaje_vida = (distancia_maxima - r_nuevo) / (distancia_maxima - self.radio_base)
                
                if porcentaje_vida > 0.6:
                    estilo_linea = (5, 3)
                    grosor = 2
                elif porcentaje_vida > 0.3:
                    estilo_linea = (3, 5)
                    grosor = 1
                else:
                    estilo_linea = (1, 8) # Puntos muy dispersos antes de morir
                    grosor = 1

                color_onda = COLOR_ROJO_PELIGRO if self.estado_actual == "error" else COLOR_NUCLEO_PRINCIPAL
                
                # Dibujar el anillo expansivo
                self.canvas.create_oval(
                    cx - r_nuevo, cy - r_nuevo, 
                    cx + r_nuevo, cy + r_nuevo, 
                    outline=color_onda, 
                    width=grosor, 
                    dash=estilo_linea
                )
        self.ondas = nuevas_ondas

        # 3. DIBUJAR NÚCLEO FIJO CENTRAL Y ASPAS DE RADAR
        # Círculo base del centro
        self.canvas.create_oval(cx - self.radio_base, cy - self.radio_base, cx + self.radio_base, cy + self.radio_base, outline=COLOR_NUCLEO_ATENUADO, width=1)
        
        # Aspas/Fragmentos holográficos giratorios externos
        for i in range(0, 360, 45):
            ang = math.radians(self.angulo_rotacion + i)
            x1 = cx + (self.radio_base + 5) * math.cos(ang)
            y1 = cy + (self.radio_base + 5) * math.sin(ang)
            x2 = cx + (self.radio_base + 12) * math.cos(ang)
            y2 = cy + (self.radio_base + 12) * math.sin(ang)
            self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_NUCLEO_PRINCIPAL, width=2)

        # Pequeño ojo tecnológico brillante en el centro exacto
        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=COLOR_NUCLEO_PRINCIPAL, outline="")

        # Mantener los FPS fluidos (aprox 30 FPS)
        self.app.after(33, self.animar_nucleo)

    def actualizar_estado(self, texto_estado: str, color_hex: str):
        """Cambia el texto de la píldora y actualiza el comportamiento del núcleo."""
        self.lbl_status.configure(text=texto_estado.upper(), text_color=color_hex)
        
        if "ESCUCHANDO" in texto_estado.upper():
            self.estado_actual = "escuchando"
        elif "PENSANDO" in texto_estado.upper():
            self.estado_actual = "pensando"
        elif "IN LÍNEA" in texto_estado.upper() or "HABLANDO" in texto_estado.upper():
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