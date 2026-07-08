import os
from imutils import paths
import face_recognition
import pickle
import cv2

DATASET_DIR = "dataset"
ENCODINGS_FILE = "encodings.pickle"
PROCESADAS_FILE = "procesadas.txt"

def entrenar_incremental():
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.loads(f.read())
        knownEncodings = data["encodings"]
        knownNames = data["names"]
    else:
        knownEncodings = []
        knownNames = []

    if os.path.exists(PROCESADAS_FILE):
        with open(PROCESADAS_FILE, "r") as f:
            procesadas = set(f.read().splitlines())
    else:
        procesadas = set()

    imagePaths = list(paths.list_images(DATASET_DIR))
    nuevasPaths = [p for p in imagePaths if p not in procesadas]

    if not nuevasPaths:
        print("[INFO] No hay imagenes nuevas para procesar.")
        return

    print(f"[INFO] Procesando {len(nuevasPaths)} imagenes nuevas...")
    for (i, imagePath) in enumerate(nuevasPaths):
        print(f"[INFO] procesando imagen {i + 1}/{len(nuevasPaths)}: {imagePath}")
        name = imagePath.split(os.path.sep)[-2]

        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding in encodings:
            knownEncodings.append(encoding)
            knownNames.append(name)

        procesadas.add(imagePath)

    print("[INFO] Serializando encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    with open(ENCODINGS_FILE, "wb") as f:
        f.write(pickle.dumps(data))

    with open(PROCESADAS_FILE, "w") as f:
        f.write("\n".join(procesadas))

    print(f"[INFO] Entrenamiento incremental completo. {len(nuevasPaths)} imagenes añadidas.")

if __name__ == "__main__":
    entrenar_incremental()