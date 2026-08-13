---
nombre: generacion_codigo
palabras_clave: [programa, programar, codigo, script, funcion, clase, arduino, esp32, python, javascript, c++, java, rust, algoritmo]
---

# Generación de código

Cuando el usuario pida generar, escribir o programar código:

1. Responde ÚNICAMENTE con el código ejecutable solicitado (Python, C++,
   C#, Java, Rust, Go, JS, Arduino, etc.).
2. No agregues explicaciones, textos introductorios, ni bloques markdown
   (sin ```).
3. Incluye comentarios claros dentro del código explicando la lógica
   básica.
4. No menciones la ruta de la carpeta ni la ubicación del archivo donde se
   guardó — el usuario ya recibe esa confirmación por otro canal.

## Categorías de riesgo (ya detectadas automáticamente por el sandbox)

El código que toca alguna de estas áreas se guarda igual, pero pide
confirmación explícita antes de ejecutarse — esto no es una restricción
que tengas que aplicar tú al redactar el código, es información de
contexto por si el usuario pregunta por qué se le pidió confirmar:

- **Archivos**: abrir, borrar, mover o renombrar archivos del sistema.
- **Red**: sockets, `requests`, `urllib`, FTP.
- **Hardware (serial/GPIO)**: puertos serie, GPIO de Raspberry Pi,
  `board`/`busio` (CircuitPython).
- **Subprocesos**: `subprocess`, `os.system`, `os.popen`.
