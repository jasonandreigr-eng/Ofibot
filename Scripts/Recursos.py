import os
import wave
import unicodedata
import numpy as np
import sounddevice as sd
import soundfile as sf
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from piper import PiperVoice
from piper import SynthesisConfig
from openwakeword.model import Model

WAKEWORD_PATH = "/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"
PIPER_VOICE_PATH = "/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx"
RESPUESTA_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/Respuesta.wav"
INTERACCION_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/interaccion.wav"

fs = 16000
tiempo_grab = int(fs * 3)
UMBRAL_SILENCIO = 10000
TEXTO_AMARA = "subtitulos realizados por la comunidad de amara.org"

print("Cargando modelos...")

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
client = genai.Client(api_key=gemini_key)
openai_client = OpenAI(api_key=openai_key)

voice = PiperVoice.load(PIPER_VOICE_PATH)
syn_config = SynthesisConfig(volume=2.5, length_scale=0.8)

wake_model = Model(
    wakeword_models=[WAKEWORD_PATH],
    inference_framework="onnx"
)
for _ in range(5):
    audio_dummy = np.zeros(int(fs * 3), dtype='int16')
    wake_model.predict(audio_dummy)

print("Modelos listos. Ofibot en espera.")

def obtener_hora():
    zona = ZoneInfo("America/Bogota")
    ahora = datetime.now(zona)
    return ahora.strftime("%H:%M del %d/%m/%Y")

def hablar(texto):
    with wave.open(RESPUESTA_WAV, "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file, syn_config=syn_config)
    data, samplerate = sf.read(RESPUESTA_WAV)
    sd.play(data, samplerate)
    sd.wait()

def es_audio_vacio(audio):
    return np.abs(audio).max() < UMBRAL_SILENCIO

def normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto)
    return texto.encode('ascii', 'ignore').decode('ascii').lower()

def escuchar_comando(intentos=3, espera=3):
    audio = sd.rec(tiempo_grab, samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    if es_audio_vacio(audio):
        return ""

    with wave.open(INTERACCION_WAV, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(fs)
        wav_file.writeframes(audio.tobytes())

    for i in range(intentos):
        try:
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
        except Exception as e:
            print(f"error whisper: {e}")
            if i < intentos - 1:
                import time
                time.sleep(espera)

    return None