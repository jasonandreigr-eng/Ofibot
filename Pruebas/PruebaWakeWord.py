import sounddevice as sd
import numpy as np
from collections import deque
from openwakeword.model import Model
import threading
import time

ultimo_activacion = 0
delay_reactivacion = 3
 
modelo = Model(
    wakeword_models=["/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"],
    inference_framework="onnx"
)

print("Precalentando modelo")
for i in range(5):
    audio_dummy = np.zeros(int(16000 * 3), dtype='int16')
    modelo.predict(audio_dummy)
print("Listo")

fs = 16000
buffer_size = int(fs * 1)
audio_buffer = deque(maxlen=buffer_size)
buffer_listo = threading.Event()

def callback(indata, frames, time, status):
    audio_buffer.extend(indata[:, 0])
    if len(audio_buffer) == buffer_size:
        buffer_listo.set()

def hilo_prediccion():
    global ultimo_activacion
    while True:
        buffer_listo.wait()
        buffer_listo.clear()
        if time.time() - ultimo_activacion <  delay_reactivacion:
            continue
        audio_array = np.array(audio_buffer, dtype='int16')
        prediction = modelo.predict(audio_array)
        for wakeword, score in prediction.items():
            print(score)
            if score > 0.2:
                print(f"Soy ofibot!!")
                ultimo_activacion = time.time()
                audio_buffer.clear()

t = threading.Thread(target=hilo_prediccion, daemon=True)
t.start()

with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
    print("Escuchando...")
    while True:
        pass