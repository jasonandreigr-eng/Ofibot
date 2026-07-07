import pigpio
import time
import board
import busio
import adafruit_tca9548a
import adafruit_pca9685
from adafruit_motor import servo


def pulse_us_to_duty(pulse_us):
    period_us = 1000000 / control_servo.frequency 
    ticks = int((pulse_us / period_us) * 4096)
    duty = int((ticks / 4096) * 65535)
    return duty

# Inicializar bus I2C de la Raspberry Pi
i2c = busio.I2C(board.SCL, board.SDA)

# Inicializar multiplexor TCA9548A en direccion 0x70
tca = adafruit_tca9548a.TCA9548A(i2c)


# Conectar al i2c del controlador de servo
control_servo_i2c = tca[1]
# Inicializar PCA9685
control_servo = adafruit_pca9685.PCA9685(control_servo_i2c)
control_servo.frequency = 50  # 50 Hz requeridos para los servos

# Crear objeto servo en canal 0
servos = [servo.Servo(control_servo.channels[0],min_pulse = 500, max_pulse = 3000),
          servo.Servo(control_servo.channels[4],min_pulse = 500, max_pulse = 3000),
          servo.Servo(control_servo.channels[8],min_pulse = 500, max_pulse = 3000),
          servo.Servo(control_servo.channels[12],min_pulse = 500, max_pulse = 2500)]
# Mover el servo a diferentes posiciones
b = 0
while True:
    sel = input("Servo a mover (1 - 4): ")
    try:
        sel = int(sel)-1
        if sel > 3 or sel <0:
            raise Exception("servo no seleccionable")
        angulo = input("angulo que tome el servo (0 - 180): ")
        try:
            angulo = int(angulo)
            servos[sel].angle = angulo
        except:
            print("Angulo no válido")
    except:
        print("Servo no válido")
print("FIN")