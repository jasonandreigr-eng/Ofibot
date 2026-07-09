import time
import board
import busio
import adafruit_tca9548a
import adafruit_pca9685
from adafruit_motor import servo
from Reconocer import reconocer_rostro

PASO = 10
PAUSA = 0.005
POS_INICIAL = 90
POS_MAX = 150
POS_MIN = 30

def inicializar_servo_cuello():
    i2c = busio.I2C(board.SCL, board.SDA)
    tca = adafruit_tca9548a.TCA9548A(i2c)
    control_servo_i2c = tca[1]
    control_servo = adafruit_pca9685.PCA9685(control_servo_i2c)
    control_servo.frequency = 50
    servo_cuello = servo.Servo(control_servo.channels[12], min_pulse=500, max_pulse=2500)
    return servo_cuello

def hay_rostro():
    import cv2
    import face_recognition
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    return len(locations) > 0

def buscar_rostro(servo_cuello):
    servo_cuello.angle = POS_INICIAL
    time.sleep(0.2)

    # Barrido derecha: 90 -> 180
    angulo = POS_INICIAL
    while angulo <= POS_MAX:
        servo_cuello.angle = angulo
        time.sleep(PAUSA)
        if hay_rostro():
            resultado = reconocer_rostro()
            if resultado is not None:
                servo_cuello.angle = POS_INICIAL
                return resultado
            # si es None, el rostro se perdio: seguir barrido
        angulo += PASO

    # Vuelve al centro
    servo_cuello.angle = POS_INICIAL
    time.sleep(0.2)

    # Barrido izquierda: 90 -> 0
    angulo = POS_INICIAL
    while angulo >= POS_MIN:
        servo_cuello.angle = angulo
        time.sleep(PAUSA)
        if hay_rostro():
            resultado = reconocer_rostro()
            if resultado is not None:
                servo_cuello.angle = POS_INICIAL
                return resultado
        angulo -= PASO

    servo_cuello.angle = POS_INICIAL
    return None