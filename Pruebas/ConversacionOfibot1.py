import sounddevice as sd
import whisper
import torch
import time
from google import genai
import numpy as np
from openwakeword.model import Model
import soundfile as sf
import wave
from piper import PiperVoice
from piper import SynthesisConfig

print("Preparando modelo")

client = genai.Client(api_key="Key")
fs = 16000
chunk_size = int(fs * 2)
tiempo_grab = int(fs * 3)
voice = PiperVoice.load("/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx")
syn_config = SynthesisConfig(
    volume = 0.5,
    length_scale = 0.8,
)


Config = """
Eres Ofibot, un robot asistente de oficina amigable y servicial.
Te estoy hablando desde un microfono, por lo tanto en caso de detectar error de escritura di que no me entendiste
Tu personalidad es:
- Amable y profesional
- conciso en tus respuestas (maximo 2-3 oraciones)
- Siempre hablas en español
- Usas un tono cercano

Capacidades que tienes:
- Responder preguntas generales
- Consultar eventos del calendario
- Buscar informacion en internet

Cuando no puedas hacer algo, lo dices claramente y de forma amable.
"""

def consultar_gemini(prompt, intentos=3, espera=5):
    for i in range(intentos):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config={"system_instruction": Config}
            )
            return response.text
        except Exception as e:
            if i == 0: print("Estoy pensando un poco...")
            if i < intentos - 1:
                time.sleep(espera)
    return "En este momento tengo problemas :c"

wake = Model(
    wakeword_models=["/home/semilleroiot/Desktop/Ofibot/ofibot.onnx"],
    inference_framework="onnx"
)

model = whisper.load_model("tiny")

for _ in range(5):
    audio_dummy = np.zeros(int(16000 * 3), dtype='int16')
    wake.predict(audio_dummy)

print("Escuchando...")
speaking = False
while True:
    while speaking: print("A1")
    audio = sd.rec(chunk_size, samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    audio = audio.flatten()
    prediction = wake.predict(audio)

    for wakeword, score in prediction.items():
        if score > 0.1:
            print("Dime?")
            audio = sd.rec(tiempo_grab, samplerate=fs, channels=1, dtype='float32')
            sd.wait()  # Espera a que termine
            audio = audio.flatten()
            msg = model.transcribe(audio, language = "spanish", fp16=False)
            msg = msg["text"]
            print(f"dijiste: {msg}")
            respuesta = consultar_gemini(msg)
            print(respuesta)
            with wave.open("Respuesta.wav","wb") as wav_file:
                voice.synthesize_wav(respuesta,wav_file,syn_config=syn_config)
            time.sleep(1)
            speaking = True
            data, samplerate = sf.read("/home/semilleroiot/Desktop/Ofibot/Respuesta.wav")
            sd.play(data,samplerate)
            sd.wait()
            speaking = False
            
