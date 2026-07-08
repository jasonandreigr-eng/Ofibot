import cv2
import os
import time
from datetime import datetime
from model_training import entrenar_incremental

DATASET_DIR = "dataset"
NUM_FOTOS = 12
INTERVALO = 1  # segundos entre fotos

def create_folder(name):
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)
    person_folder = os.path.join(DATASET_DIR, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

def conocer(name):
    folder = create_folder(name)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo acceder a la camara USB.")
        return False

    time.sleep(2)  # calentamiento de camara

    photo_count = 0
    while photo_count < NUM_FOTOS:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar frame.")
            break

        photo_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(folder, filename)
        cv2.imwrite(filepath, frame)
        print(f"Foto {photo_count}/{NUM_FOTOS} guardada")

        time.sleep(INTERVALO)

    cap.release()
    print(f"Captura completada. {photo_count} fotos guardadas para {name}.")

    print("Entrenando con las nuevas fotos...")
    entrenar_incremental()
    print(f"{name} ahora es reconocido por Ofibot.")
    return True

if __name__ == "__main__":
    nombre = input("Nombre de la nueva persona: ")
    conocer(nombre)