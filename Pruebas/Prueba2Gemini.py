from google import genai
import sounddevice as sd
import soundfile as sf
import wave
from piper import PiperVoice
from piper import SynthesisConfig
import time

espera = 2
voice = PiperVoice.load("/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx")
client = genai.Client(api_key="Key")
syn_config = SynthesisConfig(
    volume = 1.0,
    length_scale = 0.8,
)


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
    return "En este momento tengo problemas"

while True:
    msg = str(input("Pregunta a ofibot:"))
    print(msg)
    respuesta = consultar_gemini(msg)
    with wave.open("Respuesta.wav","wb") as wav_file:
        voice.synthesize_wav(respuesta,wav_file,syn_config=syn_config)
    data, samplerate = sf.read("/home/semilleroiot/Desktop/Ofibot/Respuesta.wav")
    sd.play(data,samplerate)
    sd.wait
