import time
import Hardware
from Reconocer import reconocer_rostro
import cv2
import face_recognition

PASO = 5
PAUSA = 0.005
POS_INICIAL = 90
POS_MAX = 150
POS_MIN = 30

def hay_rostro(cap):
    ret, frame = cap.read()
    if not ret:
        return False
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    return len(locations) > 0

def buscar_rostro():
    servo_cuello = Hardware.servo_cabeza_h
    with Hardware.i2c_lock:
        servo_cuello.angle = POS_INICIAL
    time.sleep(0.2)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        with Hardware.i2c_lock:
            servo_cuello.angle = POS_INICIAL
        return None

    resultado_final = None
    try:
        angulo = POS_INICIAL
        while angulo <= POS_MAX:
            with Hardware.i2c_lock:
                servo_cuello.angle = angulo
            time.sleep(PAUSA)
            if hay_rostro(cap):
                resultado = reconocer_rostro(cap)
                if resultado is not None:
                    resultado_final = resultado
                    break
            angulo += PASO

        if resultado_final is None:
            with Hardware.i2c_lock:
                servo_cuello.angle = POS_INICIAL
            time.sleep(0.2)

            angulo = POS_INICIAL
            while angulo >= POS_MIN:
                with Hardware.i2c_lock:
                    servo_cuello.angle = angulo
                time.sleep(PAUSA)
                if hay_rostro(cap):
                    resultado = reconocer_rostro(cap)
                    if resultado is not None:
                        resultado_final = resultado
                        break
                angulo -= PASO
    finally:
        cap.release()

    with Hardware.i2c_lock:
        servo_cuello.angle = POS_INICIAL
    return resultado_final