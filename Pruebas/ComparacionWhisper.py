import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import time
from openai import OpenAI

fs = 16000
seconds = 5
archivo = "prueba.wav"

client = OpenAI(api_key="key")

print("Grabando...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()
write(archivo, fs, audio)
print("Grabacion finalizada.\n")

print("Transcribiendo con Whisper local (tiny)...")
t0 = time.time()
modelo_local = whisper.load_model("tiny")
t1 = time.time()
resultado_local = modelo_local.transcribe(archivo, language="spanish", fp16=False)
t2 = time.time()

print(f"Texto (local): {resultado_local['text']}")
print(f"Tiempo carga modelo: {t1 - t0:.2f}s")
print(f"Tiempo transcripcion: {t2 - t1:.2f}s")
print(f"Tiempo total local: {t2 - t0:.2f}s\n")

print("Transcribiendo con API de OpenAI (whisper-1)...")
t3 = time.time()
with open(archivo, "rb") as f:
    resultado_api = client.audio.transcriptions.create(
        model="whisper-1",
        file=f,
        language="es"
    )
t4 = time.time()

print(f"Texto (API): {resultado_api.text}")
print(f"Tiempo total API: {t4 - t3:.2f}s\n")

print("---------- Resumen (solo transcripcion) ----------")
print(f"Local (tiny):  {t2 - t1:.2f}s")
print(f"API (whisper-1): {t4 - t3:.2f}s")