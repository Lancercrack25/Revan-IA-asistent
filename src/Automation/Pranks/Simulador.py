import time
import customtkinter as ctk
import os
import sys
# 🛡️ 1. ESCUDO ABSOLUTO: Bloqueamos pycache
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# 🔑 CORRECCIÓN DE RUTAS ABSOLUTAS: Ahora Python sabe exactamente dónde buscarlos
from src.Automation.Pranks.Terminal_hack import lanzar_bucle_terminal
from src.Automation.Pranks.Plataformas import abrir_battlenet_escritorio

# Importamos tu cliente de voz real y el cargador de ajustes
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.Config_loader import cargar_ajustes

class Ventanahackeo:
    def __init__(self):
        # 1. Inicializar la voz de REVAN usando tus archivos del proyecto
        try:
            ajustes = cargar_ajustes()
            self.voz_ia = ElevenLabsClient()
            print("🔊 Motor de voz de REVAN conectado a la simulación.")
        except Exception as e:
            self.voz_ia = None
            print(f"⚠️ No se pudo cargar el motor de voz (ejecutando en modo silencioso): {e}")

        # 2. Configuración de la interfaz temporal
        self.app = ctk.CTk()
        self.app.title("REVAN - PROT_ATTACK")
        self.app.geometry("450x350")
        self.app.resizable(False, False)
        ctk.set_appearance_mode("Dark")

        self.txt_log = ctk.CTkTextbox(
            master=self.app, 
            font=("Consolas", 12), 
            fg_color="#0d1117", 
            text_color="#f85149", 
            wrap="word"
        )
        self.txt_log.pack(pady=15, padx=15, fill="both", expand=True)

        # Tus mensajes exactos
        self.mensajes = [
            "⚠️ ALERTA: Rompiendo protocolos de seguridad TCP/IP...\n",
            "🔌 Bypass de Firewall completado. Accediendo a los servidores proxy...\n",
            "💾 Extrayendo paquetes cifrados de la base de datos...\n",
            "👾 Inyección de código malicioso ejecutada con éxito.\n",
            "🔥 ACCESO CONCEDIDO: Servidores bajo el control de REVAN.\n",
            "🎮 Accediendo a la consola Xbox...\n",
            "🔍 Se ha detectado que el usuario está jugando Overwatch 2...\n",
            "⚡ Inicializando hacks para la cuenta de Theripper23#1722...\n"
        ]
        
        self.indice = 0
        
        # Al arrancar, REVAN dice una frase introductoria por tus auriculares
        if self.voz_ia:
            self.voz_ia.hablar("Iniciando secuencia de intrusión masiva. Desplegando exploits en la red local.")
            
        self.app.after(500, self.mostrar_siguiente_linea)

    def mostrar_siguiente_linea(self):
        if self.indice < len(self.mensajes):
            self.txt_log.insert("end", self.mensajes[self.indice])
            self.txt_log.see("end")
            self.indice += 1
            self.app.after(2000, self.mostrar_siguiente_linea)
        else:
            # 💥 EL FINAL: Dice la última frase de advertencia, abre las apps y cierra
            if self.voz_ia:
                self.voz_ia.hablar("Inyección completada. Cuenta de Overwatch comprometida exitosamente.")
                
            lanzar_bucle_terminal()
            abrir_battlenet_escritorio()
            self.app.quit()

if __name__ == "__main__":
    hacks = Ventanahackeo()
    hacks.app.mainloop()