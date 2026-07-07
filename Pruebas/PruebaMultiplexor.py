import board
import busio
import adafruit_tca9548a
import adafruit_ssd1306
import adafruit_pca9685
from adafruit_motor import servo

from PIL import Image, ImageDraw, ImageFont


# Inicializar bus I2C de la Raspberry Pi
i2c = busio.I2C(board.SCL, board.SDA)

# Inicializar multiplexor TCA9548A en direccion 0x70
tca = adafruit_tca9548a.TCA9548A(i2c)

# Seleccionar canal 2
oled0_i2c = tca[2]
oled0 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled0_i2c)

# Seleccionar canal 3
oled1_i2c = tca[3]
oled1 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled1_i2c)

# Escribir en OLED del canal 0
oled0.fill(0)  # limpiar pantalla
image = Image.new("1", (oled0.width, oled0.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()  # fuente basica incluida en PIL
draw.text((0, 0), "Pantalla1", font=font, fill=255)

oled0.image(image)
oled0.show()

# Escribir en OLED del canal 1
oled1.fill(0)
image = Image.new("1", (oled1.width, oled1.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()  # fuente basica incluida en PIL
draw.text((0, 0),"Pantalla 2", font=font, fill=255)

oled1.image(image)
oled1.show()

# Conectar al i2c del controlador de servo
control_servo_i2c = tca[1]
# Inicializar PCA9685
control_servo = adafruit_pca9685.PCA9685(control_servo_i2c)
control_servo.frequency = 50  # 50 Hz requeridos para los servos

# Crear objeto servo en canal 0
servo0 = servo.Servo(control_servo.channels[0])

# Mover el servo a diferentes posiciones
while True:
    angulo = input("Ingrese angulo del servo: ")
    try:
        angulo = int(angulo)
        servo0.angle = angulo
    except:
        print("Angulo no valido intente de nuevo")