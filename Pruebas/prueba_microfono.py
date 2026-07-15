import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

fs = 44100  # frecuencia de muestreo
seconds = 5  # duración de la grabación

print("Grabando...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()  # Espera a que termine
print("Grabación finalizada.")

write("/home/semilleroiot/Desktop/Ofibot/Audios/prueba.wav", fs, audio)
print("Archivo guardado como 'prueba.wav'")
print(f"Valor maximo detectado: {np.abs(audio).max()}")