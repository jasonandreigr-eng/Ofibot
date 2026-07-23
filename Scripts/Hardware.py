# Hardware.py
import board
import busio
import adafruit_tca9548a
import adafruit_pca9685
import adafruit_ssd1306
from adafruit_motor import servo
import threading

i2c = busio.I2C(board.SCL, board.SDA)
i2c_lock = threading.Lock()
tca = adafruit_tca9548a.TCA9548A(i2c)

# Canal 1: controlador de servos/leds (PCA9685)
control_servo_i2c = tca[1]
control = adafruit_pca9685.PCA9685(control_servo_i2c)
control.frequency = 50

# LEDs RGB
led_r = control.channels[1]
led_g = control.channels[2]
led_b = control.channels[3]

# Servos
servo_cabeza_h = servo.Servo(control.channels[12], min_pulse=500, max_pulse=2500)
servo_cabeza_v = servo.Servo(control.channels[8], min_pulse=500, max_pulse=3000)
servo_brazo_izq = servo.Servo(control.channels[0], min_pulse=500, max_pulse=3000)
servo_brazo_der = servo.Servo(control.channels[4], min_pulse=500, max_pulse=3000)

# OLEDs
oled0 = adafruit_ssd1306.SSD1306_I2C(128, 64, tca[2])
oled0.fill(0)
oled0.show()

oled1 = adafruit_ssd1306.SSD1306_I2C(128, 64, tca[3])
oled1.fill(0)
oled1.show()