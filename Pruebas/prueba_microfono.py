import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100  # frecuencia de muestreo
seconds = 5  # duración de la grabación

print("Grabando...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()  # Espera a que termine
print("Grabación finalizada.")

write("prueba.wav", fs, audio)
print("Archivo guardado como 'prueba.wav'")