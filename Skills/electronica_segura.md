---
nombre: electronica_segura
palabras_clave: [arduino, esp32, sensor, motor, rele, servo, puerto serial, gpio, placa, microcontrolador, circuito]
---

# Comandos hacia hardware físico (Electronics)

Cuando el usuario pida enviar un comando a un dispositivo conectado por
puerto serial (Arduino, ESP32, etc.):

1. **Leer datos (sensores, telemetría) nunca requiere confirmación** — es
   de solo lectura, sin efecto sobre el mundo físico.
2. **Enviar un comando que actúa sobre el mundo físico sí la requiere**
   siempre (mover un motor, activar un relé, un servo, etc.) — el sistema
   ya bloquea esto automáticamente y le pide al usuario decir "confirma" o
   "cancela" antes de tocar el puerto serial de verdad.
3. Al describir la acción pendiente al usuario, sé específico: qué
   comando exacto se va a enviar y a qué puerto — no una descripción vaga
   tipo "voy a mover algo".
4. Si el usuario no especifica el puerto, se autodetecta buscando placas
   conocidas (Arduino/ESP32/CH340) antes de preguntar — solo pide el
   puerto manualmente si la autodetección no encuentra nada.
