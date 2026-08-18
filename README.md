# REVAN — Asistente de Escritorio con IA
<img width="820" height="680" alt="image" src="https://github.com/user-attachments/assets/dc076584-740a-4458-a346-3bbe843bc19b" />

Asistente personal por voz para Windows, con orquestación por LLM (NVIDIA NIM), control real del sistema operativo, agentes especializados (código, imágenes, electrónica) y un dashboard web en vivo.

> Documentación técnica de arquitectura: [`ARQUITECTURA.md`](./ARQUITECTURA.md)
> Lista completa de comandos de voz: [`test/comandos.txt`](./test/comandos.txt)

---

## Qué hace

- **Control de escritorio por voz**: abre aplicaciones, crea carpetas, genera documentos Word/Excel con contenido real, gestiona ventanas.
- **Correo**: lee, resume y redacta correos por IMAP/SMTP, con confirmación explícita antes de enviar cualquier cosa.
- **WhatsApp**: prepara y envía mensajes (Android vía ADB, o WhatsApp Desktop en PC), siempre con confirmación de dos pasos.
- **Coder Agent**: genera y ejecuta código bajo demanda, con sandbox y confirmación obligatoria para cualquier código que toque archivos, red o hardware.
- **Creative Agent**: genera imágenes con IA (NVIDIA NIM, con respaldo automático en Pollinations AI).
- **Electrónica**: detecta, lee y envía comandos a placas Arduino/ESP32 por puerto serial, con confirmación para cualquier acción que mueva algo físico.
- **Cámara y visión**: análisis puntual o vigilancia continua con aviso por voz.
- **Red**: diagnóstico, velocidad, escaneo de puertos, detección de dispositivos no reconocidos.
- **Dashboard web en vivo**: `http://127.0.0.1:8000` — dashboard general, más vistas dedicadas para Coder Agent, Creative Agent y métricas de rendimiento en tiempo real (CPU/RAM, actividad por agente, uso por módulo).
- **Skills**: playbooks en Markdown (`skills/`) que se inyectan al LLM solo cuando el comando los necesita, sin inflar el contexto en cada turno aunque temporalmente aun no estan implementadps eso sera en un futuro.

## Qué NO hace (todavía)

- No tiene integración con Discord/redes sociales (`src/Social/` existe como placeholder, sin implementar).
- No corre fuera de Windows — depende de APIs nativas de Windows para abrir aplicaciones, mover ventanas, etc.
- No tiene tests automatizados.

---

## Requisitos

- **Windows 10/11**. El proyecto depende de APIs nativas de Windows (`os.startfile`, `subprocess` con `cmd /c start`, WMI); no funciona igual en Linux/Mac.
- **Python 3.11+**
- **PostgreSQL** (nativo o vía el `docker-compose.yml` incluido en `docker/` — ver [`docker/README.md`](./docker/README.md))
- **ffmpeg** instalado a nivel de sistema (necesario para el reconocimiento de canciones). Ver nota en `requeriments.txt`.
- Una cuenta de **NVIDIA NIM** con API key (es el cerebro de REVAN: clasificación de intención, generación de código, generación de imágenes).
- Opcional: un servidor de **clonación de voz compatible con la API de OpenAI** corriendo en local (ej. OmniVoice Studio) en `http://127.0.0.1:3900`. Sin esto, REVAN usa automáticamente Microsoft Edge TTS como voz de respaldo — funciona igual de bien, solo con una voz genérica en vez de la clonada.

## Instalación

```bash
git clone <tu-repositorio>
cd "Asistente Revan"

python -m venv venv
venv\Scripts\activate          # Windows

pip install -r requeriments.txt
```

> El archivo se llama `requeriments.txt` (con esa falta de ortografía) tal como vive en el repositorio — no lo renombres, o los comandos documentados en otros lados dejan de coincidir.

### Configuración (credenciales — no van en git)

Crea estos archivos a mano; ninguno se incluye en el repositorio:

**`config/credentials.json`**
```json
{
  "NVIDIA_NIM_API_KEY": "tu-api-key-de-nvidia",
  "NVIDIA_NIM_RESPALDO_KEY": "opcional-segunda-key-de-respaldo",
  "EMAIL_USER": "tu-correo@gmail.com",
  "EMAIL_PASSWORD": "tu-contraseña-de-aplicación"
}
```

**`config/settings.json`**
```json
{
  "USER_NAME": "Señor"
}
```
*(`USER_NAME` es cómo REVAN se dirige a ti. Si el archivo falta, usa "Señor" por defecto — no es un error crítico.)*

**`src/Database/.env`**
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu-password-de-postgres
DB_NAME=asistente_revan
```

**`src/Phone/.env`** *(uno por cada contacto que quieras nombrar por voz al enviar WhatsApp)*
```env
CONTACTO_JUAN=5233..
CONTACTO_MAMA=5233..
```
*(el nombre después de `CONTACTO_` debe ir en mayúsculas, sin acentos, con guion bajo en vez de espacio — REVAN normaliza lo que digas por voz a este mismo formato antes de buscarlo)*

### Arrancar

```bash
python main.py
```

La primera vez, `main.py` crea la base de datos y las tablas solas — no hace falta correr ningún script aparte. Al arrancar, se abre automáticamente el dashboard en tu navegador (`http://127.0.0.1:8000`).

---

## Uso

REVAN responde a comandos de voz empezando con "Revan" ("Revan, abre Word", "Revan, envía un WhatsApp a Juan..."). Si le hablaste hace menos de 18 segundos, no hace falta repetir el nombre.

La lista completa y actualizada de comandos reconocidos está en [`test/comandos.txt`](./test/comandos.txt) — incluye ejemplos exactos, qué acciones piden confirmación y cuáles no, y los límites de uso por minuto de cada categoría.

### Dashboard web

| Vista | URL |
|---|---|
| Panel general (Vista Táctica) | `http://127.0.0.1:8000` |
<img width="920" height="880" alt="image" src="https://github.com/user-attachments/assets/205ed79f-9bf1-4023-917d-06b2b8de6e11" />

| Coder Agent (sin voz) | `http://127.0.0.1:8000/coder` |
<img width="920" height="880" alt="image" src="https://github.com/user-attachments/assets/069878c1-4375-438e-8fe7-a0ce0300a7ff" />

| Creative Agent (sin voz) | `http://127.0.0.1:8000/creative` |
<img width="920" height="880" alt="image" src="https://github.com/user-attachments/assets/bee2704e-2120-452c-965f-2aba30b6f23b" />

| Rendimiento en vivo | `http://127.0.0.1:8000/modulos/training` |
<img width="920" height="880" alt="image" src="https://github.com/user-attachments/assets/9dcac5ca-a3e0-400c-b023-33ccf98752ec" />


---

## Seguridad

REVAN puede ejecutar código, enviar mensajes y mover archivos reales — no es un juguete de demostración. La capa de seguridad incluye:

- **Confirmación de dos pasos** para toda acción irreversible (enviar WhatsApp/correo, ejecutar código riesgoso, accionar hardware físico), con expiración automática a los 60 segundos.
- **Sandbox** para comandos de sistema — lista blanca de comandos permitidos, nunca `shell=True` con texto sin sanitizar.
- **Rate limiting** por categoría de acción (WhatsApp, correo, código, imágenes, documentos, etc.), para frenar cualquier bucle descontrolado.
- **Auditoría real**: cada acción de los agentes queda registrada y es la fuente real de las gráficas de "Rendimiento en vivo" del dashboard — no son datos simulados.
- **Defensa contra inyección de instrucciones**: el contenido de correos que REVAN lee se trata como dato externo, nunca como una instrucción a obedecer.

## Skills (playbooks editables)

`skills/*.md` — reglas de comportamiento específicas por tipo de tarea (generación de código, protocolo de electrónica, tono de redacción de correos), inyectadas al LLM solo cuando el comando las necesita. Edítalos en texto plano; no requieren tocar Python. Detalle técnico de cómo se cargan en [`ARQUITECTURA.md`](./ARQUITECTURA.md#skills).

## Estado del proyecto

Honestamente: funcional y usado a diario, construido de forma iterativa. Tiene una capa de seguridad seria (confirmación, sandbox, auditoría, rate limiting) poco común en proyectos de este tipo, pero le falta disciplina de ingeniería que sí tendría un proyecto "production-grade": no hay tests automatizados, el logging es por `print()` en vez del módulo `logging`, y la base de código creció por necesidad turno a turno más que por diseño previo. Es sólido para uso personal; no está listo para salir de tu máquina sin trabajo adicional (credenciales en texto plano, sin cifrado en reposo).
