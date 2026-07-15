import sounddevice as sd
import Estado_global
from Servidor_web import iniciar_flask
import numpy as np
import time
import json
import threading
from collections import deque
from Registro import contar_usuarios, registrar_usuario_nuevo
from Recursos import client, voice, wake_model, syn_config, hablar, escuchar_comando, obtener_hora, fs

# ---------------- CONFIGURACION GENERAL ----------------

WAKEWORD_PATH = "/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"
PIPER_VOICE_PATH = "/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx"
RESPUESTA_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/Respuesta.wav"
INTERACCION_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/interaccion.wav"

fs = 16000
chunk_size = int(fs * 2)
tiempo_grab = int(fs * 3)
umbral_wakeword = 0.25
UMBRAL_SILENCIO = 10000  # ajustar segun sensibilidad del microfono
TEXTO_AMARA = "Subtitulos realizados por la comunidad de amara.org"

def construir_Config():
    estado = Estado_global.get_estado()
    config = """
    Eres Ofibot, un robot asistente de oficina amigable y servicial.
    Te estan hablando desde un microfono, si detectas un error de transcripcion dilo con naturalidad.
    En caso que se refieran a ti con un nombre distinto a Ofibot ignoralo, es error de transcripcion.
    Tu personalidad es:
    - Nivel de sociabilidad actual (1-10): {estado['sociabilidad']}
    - Nivel de formalidad actual (1-10): {estado['formalidad']}
    - Conciso en tus respuestas (maximo 2-3 oraciones)
    - Siempre hablas en espanol
    Ajusta tu tono de respuesta segun estos valores.

    El nombre del usuario que te llama se te dara en cada mensaje, usalo con naturalidad.
    Si el nombre del usuario es "Unknown", NO uses ningun nombre al dirigirte a el,
    tratalo de forma neutral y amigable sin mencionar identidad (ej: "hola, en que te puedo ayudar").

    Responde SIEMPRE en formato JSON valido con esta estructura exacta:
    {
      "usuario": "nombre del usuario",
      "estado_animo": "saludo|neutro|enojo|triste|emocion|duda|aburrimiento|asombro|descanso",
      "accion": "ninguna|baila|celebra|saluda|asiente|niega|recordatorio",
      "recordatorio_texto": "texto a recordar o null",
      "recordatorio_segundos": numero o null,
      "finalizar": true o false,
      "respuesta": "texto que se dira en voz alta"
    }

    El campo accion debe ser "recordatorio" unicamente cuando el usuario pida explicitamente que se le recuerde algo en un tiempo determinado. En ese caso, recordatorio_texto y recordatorio_segundos deben ir completos (convierte minutos/horas a segundos). En cualquier otro caso ambos deben ser null.
    
    El campo finalizar debe ser true unicamente cuando el usuario se despida o de a entender que quiere terminar la conversacion (ej: gracias hasta luego, eso es todo, nos vemos). En cualquier otro caso debe ser false.

    No agregues texto fuera del JSON.
    """
    return config

# ---------------- GEMINI ----------------

def consultar_gemini(historial, intentos=3, espera=5):
    hora_actual = obtener_hora()
    Config = construir_Config()
    config_dinamico = Config + f"\nHora actual en Colombia: {hora_actual}"
    for i in range(intentos):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=historial,
                config={
                    "system_instruction": config_dinamico,
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
        except Exception as e:
            if i == 0:
                print("Estoy pensando un poco...")
            if i < intentos - 1:
                time.sleep(espera)
            else:
                print(f"error gemini: {e}")
    return {
        "usuario": "desconocido",
        "estado_animo": "neutro",
        "accion": "ninguna",
        "respuesta": "En este momento tengo problemas para pensar."
    }

# ---------------- RECONOCIMIENTO FACIAL (carga bajo demanda) ----------------

def identificar_usuario():
    from Buscar_Rostro import buscar_rostro
    nombre = buscar_rostro()
    return nombre

# ---------------- LOOP DE CONVERSACION ----------------

def loop_conversacion(usuario):
    Estado_global.marcar_inicio_conversacion(usuario)
    historial = []
    print(f"Iniciando conversacion con {usuario}")
    if usuario == "Unknown":
        hablar("Hola, como te puedo ayudar")
    else:
        hablar(f"Hola {usuario}, como te puedo ayudar")
    while True:
        print("Escuchando comando...")
        texto = escuchar_comando()

        if texto is None:
            hablar("En este momento no puedo escuchar")
            break

        if texto == "":
            print("Sin nuevas palabras. Cerrando conversacion.")
            break

        print(f"{usuario} dijo: {texto}")
        mensaje = f"[Usuario: {usuario}] {texto}"
        historial.append({"role": "user", "parts": [{"text": mensaje}]})

        t0 = time.time()
        data = consultar_gemini(historial)
        t1 = time.time()
        Estado_global.registrar_tiempo_respuesta(t1 - t0)

        respuesta_texto = data.get("respuesta", "")
        print(f"Ofibot ({data.get('estado_animo')}, accion: {data.get('accion')}): {respuesta_texto}")

        Estado_global.set_estado_animo(data.get("estado_animo", "neutro"))

        historial.append({"role": "model", "parts": [{"text": json.dumps(data)}]})

        if data.get("accion", "ninguna") == "recordatorio":
            texto_rec = data.get("recordatorio_texto")
            segundos_rec = data.get("recordatorio_segundos")
            if texto_rec and segundos_rec:
                Estado_global.agregar_recordatorio(usuario, texto_rec, segundos_rec)
        elif data.get("accion", "ninguna") != "ninguna":
            ejecutar_accion(data["accion"])

        hablar(respuesta_texto)

        if data.get("finalizar", False):
            print("Despedida detectada. Cerrando conversacion.")
            break

    Estado_global.marcar_fin_conversacion()
    historial.clear()
    print("Historial eliminado. Ofibot en espera.")
    
def ejecutar_accion(accion):
    # Aqui se conectaran los movimientos de servos segun la accion
    print(f"[ACCION] ejecutando: {accion}")
    
# ---------------- WAKEWORD ----------------

buffer_size = int(fs * 1)
audio_buffer = deque(maxlen=buffer_size)
buffer_listo = threading.Event()
en_conversacion = False
ultimo_activacion = 0
delay_reactivacion = 3
MAX_USUARIOS = 6

def callback(indata, frames, time_info, status):
    if en_conversacion:
        return
    audio_buffer.extend(indata[:, 0])
    if len(audio_buffer) == buffer_size:
        buffer_listo.set()

def hilo_wakeword():
    global ultimo_activacion
    global en_conversacion
    while True:
        buffer_listo.wait()
        buffer_listo.clear()

        if time.time() - ultimo_activacion < delay_reactivacion:
            continue

        audio_array = np.array(audio_buffer, dtype='int16')
        prediction = wake_model.predict(audio_array)

        for wakeword, score in prediction.items():
            if score > umbral_wakeword:
                print(f"Wakeword detectada ({score:.2f})")
                ultimo_activacion = time.time()
                en_conversacion = True
                audio_buffer.clear()

                try:
                    usuario = identificar_usuario()
                    audio_buffer.clear()
                    buffer_listo.clear()

                    print(f"Usuario identificado: {usuario}")

                    if usuario is None:
                        hablar("No veo a nadie, te puedes acercar un poco mas?")
                        continue

                    if usuario == "Unknown":
                        if contar_usuarios() < MAX_USUARIOS:
                            usuario = registrar_usuario_nuevo()
                            if usuario is None:
                                continue
                        else:
                            hablar("Ya tengo el cupo maximo de usuarios registrados, pero puedo ayudarte igual.")

                    loop_conversacion(usuario)
                finally:
                    time.sleep(1)
                    ultimo_activacion = time.time()
                    audio_buffer.clear()
                    buffer_listo.clear()
                    en_conversacion = False
                
# ---------------- RECORDATORIOS ----------------

def hilo_recordatorios():
    while True:
        time.sleep(5)

        # No revisar mientras hay una conversacion activa
        if en_conversacion:
            continue

        vencidos = Estado_global.revisar_vencidos()
        for r in vencidos:
            hablar(f"Recordatorio: {r['texto']}")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    hilo_servidor = threading.Thread(target=iniciar_flask, daemon=True)
    hilo_servidor.start()
    print("[SERVIDOR] Hilo del servidor web iniciado en puerto 5000")

    hilo = threading.Thread(target=hilo_wakeword, daemon=True)
    hilo.start()

    hilo_rec = threading.Thread(target=hilo_recordatorios, daemon=True)
    hilo_rec.start()
    print("[RECORDATORIOS] Hilo de recordatorios iniciado")

    with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
        print("Escuchando wakeword...")
        while True:
            time.sleep(0.1)