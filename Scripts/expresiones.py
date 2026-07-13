import board
import busio  #Libreria comunicacion (buses de datos)
from PIL import Image, ImageDraw, ImageOps
import adafruit_ssd1306
import adafruit_tca9548a
import adafruit_pca9685
import time

UMBRAL = 170  # mas alto = mas pixeles se vuelven negros

# Inicializar bus I2C de la Raspberry Pi e Inicializar multiplexor TCA9548A en direccion 0x70
i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c)

# Seleccionar canal 2
oled0_i2c = tca[2]
oled0 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled0_i2c)

oled0.fill(0)
oled0.show()

# Seleccionar canal 3
oled1_i2c = tca[3]
oled1 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled1_i2c)

oled1.fill(0)
oled1.show()

## Definicion Colorea LED's RGB

# Multiplexor -> controlador de servos/leds
control_i2c = tca[1]
control = adafruit_pca9685.PCA9685(control_i2c)
control.frequency = 50

# Canales del LED RGB
led_r = control.channels[1]
led_g = control.channels[2]
led_b = control.channels[3]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b

def set_color(r, g, b):
    # r, g, b en rango 0-255
    led_r.duty_cycle = int((r / 255) * 65535)
    led_g.duty_cycle = int((g / 255) * 65535)
    led_b.duty_cycle = int((b / 255) * 65535)

def neutro():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Neutro_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Neutro_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()

  # NEUTRO - BLANCO CALIDO
  set_color(*hex_to_rgb("F5F5F0"))

def saludo():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Saludo_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Saludo_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # SALUDO AMISTOSO - AMARILLO CALIDO
  set_color(*hex_to_rgb("FFC107"))

def aburrimiento():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Aburrimiento_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Aburrimiento_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # ABURRIMIENTO - GRIZ AZULADO
  set_color(*hex_to_rgb("8899A6"))

def asombro():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Asombro_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Asombro_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # ASOMBRO - CIAN
  set_color(*hex_to_rgb("00CED1"))

def descanso():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Descanso_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Descanso_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # DESCANSO - VERDE SUAVE
  set_color(*hex_to_rgb("7FB685"))

def duda():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Duda_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Duda_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # DUDA - VIOLETA/LILA
  set_color(*hex_to_rgb("9B59B6"))

def emocion():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Emocion_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Emocion_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # EMOCION - NARANJA
  set_color(*hex_to_rgb("FF7F11"))

def enojo():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Enojo_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Enojo_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # ENOJO - ROJO
  set_color(*hex_to_rgb("E63946"))

def triste():
  oled0.fill(0)
  oled1.fill(0)
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Triste_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Triste_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  oled0.image(img_R)
  oled0.show()
  oled1.image(img_L)
  oled1.show()
  # TRISTEZA - AZUL
  set_color(*hex_to_rgb("3B5998"))

if __name__ == "__main__":
  expresiones_lista = [neutro, saludo, aburrimiento, asombro, descanso, duda, emocion, enojo, triste]
  for expresion in expresiones_lista:
      print(f"Probando: {expresion.__name__}")
      expresion()
      time.sleep(2)