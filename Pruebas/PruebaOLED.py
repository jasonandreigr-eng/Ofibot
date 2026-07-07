import board
import busio  #Libreria comunicacion (buses de datos)
from PIL import Image, ImageDraw, ImageOps
import adafruit_ssd1306
import adafruit_tca9548a
import time

# Inicializar bus I2C de la Raspberry Pi
i2c = busio.I2C(board.SCL, board.SDA)

# Inicializar multiplexor TCA9548A en direccion 0x70
tca = adafruit_tca9548a.TCA9548A(i2c)

# Seleccionar canal 2
oled0_i2c = tca[2]
oled0 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled0_i2c)

oled0.fill(0)
oled0.show()

img = Image.open("Ojoizquierdo.bmp").convert("1").resize((128, 64))
img = ImageOps.invert(img.convert("L")).convert("1").resize((128, 64))

oled0.image(img)
oled0.show()

# Seleccionar canal 3
oled1_i2c = tca[3]
oled1 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled1_i2c)

oled1.fill(0)
oled1.show()

img = Image.open("Ojoderecho.bmp").convert("1").resize((128, 64))
img = ImageOps.invert(img.convert("L")).convert("1").resize((128, 64))

oled1.image(img)
oled1.show()