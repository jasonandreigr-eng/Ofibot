import whisper

model = whisper.load_model("tiny")

audio_path = "prueba.wav"

result = model.transcribe(audio_path, language = "spanish", fp16 = False)

print("transcripción:")
print(result["text"])