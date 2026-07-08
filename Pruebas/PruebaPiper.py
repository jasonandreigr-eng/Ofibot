import wave
from piper import PiperVoice
import time

t0 = time.time()
voice = PiperVoice.load("/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx")
t1 = time.time()
with wave.open("/home/semilleroiot/Desktop/Ofibot/Audios/Busca.wav","wb") as wav_file:
    voice.synthesize_wav("¿Donde estas?",wav_file)
    
t2 = time.time()

print(f"Tiempo de carga de modelo: {t1-t0}")
print(f"Tiempo de generación y guardado: {t2-t1}") 