import time
import base64
import scipy.io.wavfile as wav
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from google import genai
from google.genai import types

client = genai.Client(api_key="Key")

Config = """
Eres Ofibot, un robot asistente de oficina amigable y servicial.
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
                print(f"error: {e}")
    return "En este momento tengo problemas :c"

respuesta = consultar_gemini("Quien eres?")
print(respuesta)

