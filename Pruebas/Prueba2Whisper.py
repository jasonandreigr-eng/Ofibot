import sounddevice as sd
import whisper
import torch
import time

torch.set_num_threads(4)
t_carga_inicio = time.time()
model = whisper.load_model("tiny")
t_carga_fin = time.time()

print(f"tiempo de carga del modelo: {t_carga_fin - t_carga_inicio:.2f}s\n")

fs = 16000  # frecuencia de muestreo
seconds = 3 #duración entre tomas
while True:
    t0 = time.time()
    print("Grabando...")
    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Espera a que termine
    t1 = time.time()
    print("fin grabación")
    audio = audio.flatten()
    t2 = time.time()
    result = model.transcribe(audio, language = "spanish", fp16=False)
    t3 = time.time()
    print(result["text"])
    
    print(f"---------Tiempos----------------")
    print(f"Grabacion: {t1 - t0:.4f}s")
    print(f"Preparacion:   {t2 - t1:.4f}s")
    print(f"Transcripcion:  {t3 - t2:.2f}s")
    print(f"TOTAL ciclo:    {t3 - t0:.2f}s")
    print(f"--------------------------\n")
    