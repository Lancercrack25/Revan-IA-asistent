import customtkinter as ctk
import tkinter as tk
import math
import asyncio
from src.Gui.styles.css import *
# Importación relativa a la estructura verificada de tu proyecto
from src.Interfaces.servidor import cambiar_estado_esfera

class RevanGUI:
    def __init__(self, titulo_usuario="Maestro"):
        self.titulo_usuario = titulo_usuario
        
        # 1. Configuración de la Ventana Principal
        self.app = ctk.CTk()
        self.app.title("REVAN - Interface")
        self.app.geometry("480x680")
        self.app.minsize(320, 400)
        self.app.resizable(True, True)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        # 2. Contenedor Principal
        self.card = ctk.CTkFrame(master=self.app, corner_radius=16, fg_color=COLOR_TARJETA, border_width=1, border_color=COLOR_BORDE)
        self.card.grid(row=0, column=0, pady=15, padx=20, sticky="nsew")
        
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(4, weight=1)

        self.lbl_titulo = ctk.CTkLabel(master=self.card, text="🌌 REVAN V1.0", font=("Segoe UI", 20, "bold"), text_color=COLOR_TEXTO_AZUL)
        self.lbl_titulo.grid(row=0, column=0, pady=(15, 2), sticky="ew")

        self.lbl_subtitulo = ctk.CTkLabel(master=self.card, text=f"Operador: {self.titulo_usuario}", font=("Segoe UI", 12), text_color=COLOR_TEXTO_GRIS)
        self.lbl_subtitulo.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        # Núcleo 2D clásico de reserva
        self.canvas_size = 180 
        self.canvas = tk.Canvas(self.card, width=self.canvas_size, height=self.canvas_size, bg=COLOR_TARJETA, highlightthickness=0)
        self.canvas.grid(row=2, column=0, pady=10)

        self.angulo_rotacion = 0
        self.radio_base = 35
        self.ondas = []        
        self.estado_actual = "espera"
        self.ticks = 0         
        
        self.animar_nucleo()

        # Indicador de Estado
        self.lbl_status = ctk.CTkLabel(
            master=self.card, text="⚡ SISTEMAS EN ESPERA", font=("Consolas", 11, "bold"),
            text_color=COLOR_CYAN_STATUS, fg_color=COLOR_FONDO_STATUS, corner_radius=20, height=28, width=180
        )
        self.lbl_status.grid(row=3, column=0, pady=5)

        # Área de Chat
        self.txt_chat = ctk.CTkTextbox(
            master=self.card, font=("Segoe UI", 12), corner_radius=12, border_width=1,
            border_color=COLOR_BORDE, fg_color=COLOR_FONDO_PRINCIPAL, text_color="#c9d1d9", wrap="word"
        )
        self.txt_chat.grid(row=4, column=0, pady=10, padx=20, sticky="nsew")
        self.txt_chat.configure(state="disabled")

        # Botón de Apagado (¡Corregido con sticky="ew"!)
        self.btn_control = ctk.CTkButton(
            master=self.card, text="APAGAR SISTEMAS", font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_BOTON_BG, hover_color=COLOR_ROJO_PELIGRO, text_color=COLOR_ROJO_PELIGRO,
            border_width=1, border_color=COLOR_ROJO_PELIGRO, corner_radius=8, height=35, cursor="hand2",
            command=self.solicitar_cierre
        )
        self.btn_control.grid(row=5, column=0, pady=15, padx=20, sticky="ew")
        
        self.debe_cerrar = False
        self.app.bind("<Configure>", self.adaptar_layout)
        
        # Enlace al bucle asíncronico global
        self.loop_ui = asyncio.get_event_loop()

    def adaptar_layout(self, event=None):
        alto = self.app.winfo_height()
        ancho = self.app.winfo_width()
        if alto < 520 or ancho < 380:
            self.lbl_titulo.grid_remove()
            self.lbl_subtitulo.grid_remove()
            self.canvas.grid_remove()
        else:
            self.lbl_titulo.grid()
            self.lbl_subtitulo.grid()
            self.canvas.grid()

    def animar_nucleo(self):
        self.canvas.delete("all")
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        self.ticks += 1
        velocidad_rotacion = 2
        frecuencia_onda = 25  
        velocidad_onda = 1.0  

        if self.estado_actual == "escuchando":
            velocidad_rotacion = 5
            frecuencia_onda = 12   
            velocidad_onda = 2.0   
        elif self.estado_actual == "pensando":
            velocidad_rotacion = 14  
            frecuencia_onda = 999   
        elif self.estado_actual == "hablando":
            velocidad_rotacion = 3
            frecuencia_onda = 8    
            velocidad_onda = 2.5   

        self.angulo_rotacion = (self.angulo_rotacion + velocidad_rotacion) % 360

        if self.ticks % frecuencia_onda == 0 and self.estado_actual != "pensando":
            self.ondas.append(self.radio_base)

        nuevas_ondas = []
        for r in self.ondas:
            r_nuevo = r + velocidad_onda
            if r_nuevo < (self.canvas_size // 2) - 5:
                nuevas_ondas.append(r_nuevo)
                distancia_maxima = (self.canvas_size // 2) - 5
                porcentaje_vida = (distancia_maxima - r_nuevo) / (distancia_maxima - self.radio_base)
                estilo_linea = (5, 3) if porcentaje_vida > 0.6 else ((3, 5) if porcentaje_vida > 0.3 else (1, 8))
                grosor = 2 if porcentaje_vida > 0.6 else 1
                color_onda = COLOR_ROJO_PELIGRO if self.estado_actual == "error" else COLOR_NUCLEO_PRINCIPAL
                self.canvas.create_oval(cx - r_nuevo, cy - r_nuevo, cx + r_nuevo, cy + r_nuevo, outline=color_onda, width=grosor, dash=estilo_linea)
        self.ondas = nuevas_ondas

        self.canvas.create_oval(cx - self.radio_base, cy - self.radio_base, cx + self.radio_base, cy + self.radio_base, outline=COLOR_NUCLEO_ATENUADO, width=1)
        for i in range(0, 360, 45):
            ang = math.radians(self.angulo_rotacion + i)
            x1, y1 = cx + (self.radio_base + 5) * math.cos(ang), cy + (self.radio_base + 5) * math.sin(ang)
            x2, y2 = cx + (self.radio_base + 12) * math.cos(ang), cy + (self.radio_base + 12) * math.sin(ang)
            self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_NUCLEO_PRINCIPAL, width=2)

        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=COLOR_NUCLEO_PRINCIPAL, outline="")
        self.app.after(33, self.animar_nucleo)

    def mostrar_panel(self):
        self.app.deiconify()

    def actualizar_estado(self, texto_estado: str, color_hex: str):
        """Modifica la barra táctil de Windows y sincroniza la Esfera 3D del Navegador."""
        self.lbl_status.configure(text=texto_estado.upper(), text_color=color_hex)
        
        if "ESCUCHANDO" in texto_estado.upper():
            self.estado_actual = "escuchando"
            estado_esfera = "ESCUCHANDO"
        elif "PENSANDO" in texto_estado.upper():
            self.estado_actual = "pensando"
            estado_esfera = "PENSANDO"
        elif "IN LÍNEA" in texto_estado.upper() or "HABLANDO" in texto_estado.upper():
            self.estado_actual = "hablando" if "HABLANDO" in texto_estado.upper() else "espera"
            estado_esfera = "HABLANDO" if "HABLANDO" in texto_estado.upper() else "ESPERA"
        elif "ERROR" in texto_estado.upper():
            self.estado_actual = "error"
            estado_esfera = "ERROR"
        else:
            self.estado_actual = "espera"
            estado_esfera = "ESPERA"
            
        self.app.update_idletasks()

        # Enlace asíncrono seguro entre el hilo de Tkinter y FastAPI
        try:
            asyncio.run_coroutine_threadsafe(
                cambiar_estado_esfera(estado_esfera, color_hex), 
                self.loop_ui
            )
        except Exception:
            pass

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