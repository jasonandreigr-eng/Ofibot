import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import json
import wave
import threading
from collections import deque
from openwakeword.model import Model
from google import genai
from piper import PiperVoice
from piper import SynthesisConfig
from Registro import contar_usuarios, registrar_usuario_nuevo
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import unicodedata

# ---------------- CONFIGURACION GENERAL ----------------

WAKEWORD_PATH = "/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"
PIPER_VOICE_PATH = "/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx"
RESPUESTA_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/Respuesta.wav"
INTERACCION_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/interaccion.wav"

fs = 16000
chunk_size = int(fs * 2)
tiempo_grab = int(fs * 3)
umbral_wakeword = 0.15
UMBRAL_SILENCIO = 10000  # ajustar segun sensibilidad del microfono
TEXTO_AMARA = "Subtitulos realizados por la comunidad de amara.org"

Config = """
Eres Ofibot, un robot asistente de oficina amigable y servicial.
Te estan hablando desde un microfono, si detectas un error de transcripcion dilo con naturalidad.
Tu personalidad es:
- Amable y profesional
- Conciso en tus respuestas (maximo 2-3 oraciones)
- Siempre hablas en espanol
- Usas un tono cercano

El nombre del usuario que te llama se te dara en cada mensaje, usalo con naturalidad.

Responde SIEMPRE en formato JSON valido con esta estructura exacta:
{
  "usuario": "nombre del usuario",
  "estado_animo": "feliz|neutral|molesto|triste|emocionado",
  "accion": "ninguna|baila|celebra|saluda",
  "finalizar": true o false,
  "respuesta": "texto que se dira en voz alta"
}

El campo finalizar debe ser true unicamente cuando el usuario se despida o de a entender que quiere terminar la conversacion (ej: gracias hasta luego, eso es todo, nos vemos). En cualquier otro caso debe ser false.

No agregues texto fuera del JSON.
"""

# ---------------- CARGA DE MODELOS (una sola vez) ----------------

print("Cargando modelos...")
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
client = genai.Client(api_key=gemini_key)
openai_client = OpenAI(api_key=openai_key)

voice = PiperVoice.load(PIPER_VOICE_PATH)
syn_config = SynthesisConfig(volume=0.7, length_scale=0.8)



wake_model = Model(
    wakeword_models=[WAKEWORD_PATH],
    inference_framework="onnx"
)
for _ in range(5):
    audio_dummy = np.zeros(int(fs * 3), dtype='int16')
    wake_model.predict(audio_dummy)

print("Modelos listos. Ofibot en espera.")

# ---------------- GEMINI ----------------

def obtener_hora():
    zona = ZoneInfo("America/Bogota")
    ahora = datetime.now(zona)
    return ahora.strftime("%H:%M del %d/%m/%Y")

def consultar_gemini(historial, intentos=3, espera=5):
    hora_actual = obtener_hora()
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
        "estado_animo": "neutral",
        "accion": "ninguna",
        "respuesta": "En este momento tengo problemas para pensar."
    }

def hablar(texto):
    with wave.open(RESPUESTA_WAV, "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file, syn_config=syn_config)
    data, samplerate = sf.read(RESPUESTA_WAV)
    sd.play(data, samplerate)
    sd.wait()

# ---------------- RECONOCIMIENTO FACIAL (carga bajo demanda) ----------------

def identificar_usuario():
    from Buscar_Rostro import inicializar_servo_cuello, buscar_rostro
    servo_cuello = inicializar_servo_cuello()
    nombre = buscar_rostro(servo_cuello)
    return nombre

# ---------------- LOOP DE CONVERSACION ----------------

def es_audio_vacio(audio):
    return np.abs(audio).max() < UMBRAL_SILENCIO

def normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto)
    return texto.encode('ascii', 'ignore').decode('ascii').lower()

def escuchar_comando():
    audio = sd.rec(tiempo_grab, samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    if es_audio_vacio(audio):
        return ""

    with wave.open(INTERACCION_WAV, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(fs)
        wav_file.writeframes(audio.tobytes())

    with open(INTERACCION_WAV, "rb") as f:
        transcripcion = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="es"
        )
    texto = transcripcion.text.strip()

    if normalizar(texto) == TEXTO_AMARA:
        return ""

    return texto

def loop_conversacion(usuario):
    historial = []
    print(f"Iniciando conversacion con {usuario}")
    hablar(f"Hola {usuario}, como te puedo ayudar")
    while True:
        print("Escuchando comando...")
        texto = escuchar_comando()

        if texto == "":
            print("Sin nuevas palabras. Cerrando conversacion.")
            break

        print(f"{usuario} dijo: {texto}")
        mensaje = f"[Usuario: {usuario}] {texto}"
        historial.append({"role": "user", "parts": [{"text": mensaje}]})

        data = consultar_gemini(historial)
        respuesta_texto = data.get("respuesta", "")
        print(f"Ofibot ({data.get('estado_animo')}, accion: {data.get('accion')}): {respuesta_texto}")

        historial.append({"role": "model", "parts": [{"text": json.dumps(data)}]})

        if data.get("accion", "ninguna") != "ninguna":
            ejecutar_accion(data["accion"])

        hablar(respuesta_texto)

        if data.get("finalizar", False):
            print("Despedida detectada. Cerrando conversacion.")
            break

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
                            audio_buffer.clear()
                            buffer_listo.clear()
                            continue
                    else:
                        hablar("Ya tengo el cupo maximo de usuarios registrados, pero puedo ayudarte igual.")

                loop_conversacion(usuario)

                time.sleep(1)
                ultimo_activacion = time.time()
                audio_buffer.clear()
                buffer_listo.clear()
                en_conversacion = False
                

# ---------------- MAIN ----------------

if __name__ == "__main__":
    hilo = threading.Thread(target=hilo_wakeword, daemon=True)
    hilo.start()

    with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
        print("Escuchando wakeword...")
        while True:
            time.sleep(0.1)