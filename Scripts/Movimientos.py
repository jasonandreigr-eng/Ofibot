# Movimientos.py
import time
import Hardware

servo_izq = Hardware.servo_brazo_izq
servo_der = Hardware.servo_brazo_der
servo_cabeza_h = Hardware.servo_cabeza_h
servo_cabeza_v = Hardware.servo_cabeza_v
servo_izq.angle = 0
servo_der.angle = 0
servo_cabeza_h.angle = 90
servo_cabeza_v.angle = 90

"ninguna|baila|celebra|saluda|asiente|niega|recordatorio"
def ninguna():
    servo_izq.angle = 30   # brazo izquierdo estatico pos. base
    servo_der.angle = 30    # brazo derecho estatico pos. base
    time.sleep(0.5)
    
def baila(ciclos=3, pausa=0.8):
    for _ in range(ciclos):
        servo_izq.angle = 150   # brazo izquierdo sube
        servo_der.angle = 30    # brazo derecho baja
        time.sleep(pausa)

        servo_izq.angle = 30    # brazo izquierdo baja
        servo_der.angle = 150   # brazo derecho sube
        time.sleep(pausa)

    # posicion neutral al terminar
    servo_izq.angle = 25
    servo_der.angle = 25
    
def celebra(ciclos=3, pausa=0.8):
    for _ in range(ciclos):
        servo_izq.angle =150
        servo_der.angle =150
        time.sleep(pausa)
        
        servo_izq.angle = 30
        servo_der.angle = 30
        time.sleep(pausa)
        
    servo_izq.angle = 25
    servo_der.angle = 25

def saluda():
    servo_der.angle = 150
    time.sleep(2)
    servo_der.angle = 25
    time.sleep(2)

def asiente(ciclos=3, pausa=0.8):
    for _ in range(ciclos):
        servo_cabeza_v.angle = 110
        time.sleep(pausa)
        
        servo_cabeza_v.angle = 70
        time.sleep(pausa)
        
    servo_cabeza_v.angle = 90

def niega(ciclos=3, pausa=0.8):
    for _ in range(ciclos):
        servo_cabeza_h.angle = 110
        time.sleep(pausa)
        
        servo_cabeza_h.angle = 70
        time.sleep(pausa)
        
    servo_cabeza_h.angle = 90

def recordatorio(ciclos=2, pausa=0.8):
    for _ in range(ciclos):
        servo_der.angle = 70
        servo_izq.angle = 70
        time.sleep(pausa)
        
        servo_der.angle = 10
        servo_izq.angle = 10
        time.sleep(pausa)
        
    servo_der.angle = 25
    servo_izq.angle = 25

if __name__ == "__main__":
  moves_lista = [ninguna,baila,celebra,saluda,asiente,niega,recordatorio]
  for move in moves_lista:
      print(f"Probando: {move.__name__}")
      move()
      time.sleep(2)



