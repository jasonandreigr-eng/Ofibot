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
time.sleep(0.05)
# Seleccionar canal 2
oled0_i2c = tca[2]
oled0 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled0_i2c)

oled0.fill(0)
oled0.show()
time.sleep(0.05)


# Seleccionar canal 3
oled1_i2c = tca[3]
oled1 = adafruit_ssd1306.SSD1306_I2C(128, 64, oled1_i2c)

oled1.fill(0)
oled1.show()
time.sleep(0.05)

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

def mostrar_oled(oled, img, intentos=3, espera=0.1):
    oled.fill(0)
    for i in range(intentos):
        try:
            oled.image(img)
            oled.show()
            return True
        except OSError:
            time.sleep(espera)
    print("Error persistente en OLED")
    return False

def set_color(r, g, b, intentos=3, espera=0.15):
    for i in range(intentos):
        try:
            led_r.duty_cycle = int((r / 255) * 65535)
            led_g.duty_cycle = int((g / 255) * 65535)
            led_b.duty_cycle = int((b / 255) * 65535)
            return True
        except OSError:
            time.sleep(espera)
    print("Error persistente en LED")
    return False

def neutro():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Neutro_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Neutro_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)

  # NEUTRO - BLANCO CALIDO
  set_color(*hex_to_rgb("F5F5F0"))

def saludo():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Saludo_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Saludo_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # SALUDO AMISTOSO - AMARILLO CALIDO
  set_color(*hex_to_rgb("FFC107"))
  
def aburrimiento():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Aburrimiento_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Aburrimiento_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # ABURRIMIENTO - GRIZ AZULADO
  set_color(*hex_to_rgb("8899A6"))

def asombro():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Asombro_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Asombro_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # ASOMBRO - CIAN
  set_color(*hex_to_rgb("00CED1"))

def descanso():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Descanso_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Descanso_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # DESCANSO - VERDE SUAVE
  set_color(*hex_to_rgb("7FB685"))

def duda():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Duda_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Duda_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # DUDA - VIOLETA/LILA
  set_color(*hex_to_rgb("9B59B6"))

def emocion():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Emocion_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Emocion_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # EMOCION - NARANJA
  set_color(*hex_to_rgb("FF7F11"))

def enojo():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Enojo_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Enojo_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # ENOJO - ROJO
  set_color(*hex_to_rgb("E63946"))

def triste():
  img_R = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Triste_D.jpeg").convert("L").resize((128, 64))
  img_R = ImageOps.invert(img_R)
  img_R = img_R.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  img_L = Image.open("/home/semilleroiot/Desktop/Ofibot/Expresiones/Triste_I.jpeg").convert("L").resize((128, 64))
  img_L = ImageOps.invert(img_L)
  img_L = img_L.point(lambda p: 255 if p > UMBRAL else 0).convert("1")

  mostrar_oled(oled0, img_R)
  mostrar_oled(oled1, img_L)
  # TRISTEZA - AZUL
  set_color(*hex_to_rgb("3B5998"))

if __name__ == "__main__":
  expresiones_lista = [neutro, saludo, aburrimiento, asombro, descanso, duda, emocion, enojo, triste]
  for expresion in expresiones_lista:
      print(f"Probando: {expresion.__name__}")
      expresion()
      time.sleep(2)