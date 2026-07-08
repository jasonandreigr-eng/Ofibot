import face_recognition
import cv2
import numpy as np
import pickle
from collections import Counter

ENCODINGS_FILE = "encodings.pickle"
NUM_INTENTOS = 5
CV_SCALER = 4

def reconocer_rostro():
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.loads(f.read())
    known_face_encodings = data["encodings"]
    known_face_names = data["names"]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo acceder a la camara USB.")
        return "Unknown"

    detecciones = []

    for intento in range(NUM_INTENTOS):
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar frame.")
            continue

        resized_frame = cv2.resize(frame, (0, 0), fx=(1/CV_SCALER), fy=(1/CV_SCALER))
        rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_resized_frame)
        face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations, model='large')

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

            detecciones.append(name)

    cap.release()

    if not detecciones:
        print("No se detecto ningun rostro.")
        return "Unknown"

    conteo = Counter(detecciones)
    nombre_mas_comun, veces = conteo.most_common(1)[0]

    print(f"Detecciones: {detecciones}")
    print(f"Resultado: {nombre_mas_comun} ({veces}/{len(detecciones)})")

    return nombre_mas_comun

if __name__ == "__main__":
    resultado = reconocer_rostro()
    print(f"Persona identificada: {resultado}")