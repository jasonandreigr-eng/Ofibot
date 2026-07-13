# estado_global.py
import threading
import json
import time
from datetime import datetime

_lock = threading.Lock()

_estado = {
    "estado_animo": "neutro",       # feliz|neutral|molesto|triste|emocionado
    "sociabilidad": 5,               # escala 1-10, ajustable en panel tecnico
    "formalidad": 5,                 # escala 1-10
    "ultimo_usuario": None,
    "en_conversacion": False,
    "ultimo_tiempo_respuesta": None, # segundos
    "historial_usuarios": []         # lista de dicts: {nombre, hora, duracion}
}

HISTORIAL_FILE = "historial_usuarios.json"

def _guardar_historial_disco():
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(_estado["historial_usuarios"], f, indent=2, ensure_ascii=False)

def get_estado():
    """Devuelve una copia segura del estado actual (thread-safe)."""
    with _lock:
        return dict(_estado)

def set_estado_animo(nuevo_animo):
    with _lock:
        _estado["estado_animo"] = nuevo_animo

def set_config(sociabilidad=None, formalidad=None):
    with _lock:
        if sociabilidad is not None:
            _estado["sociabilidad"] = sociabilidad
        if formalidad is not None:
            _estado["formalidad"] = formalidad

def marcar_inicio_conversacion(usuario):
    with _lock:
        _estado["en_conversacion"] = True
        _estado["ultimo_usuario"] = usuario
        _estado["_inicio_ts"] = time.time()

def marcar_fin_conversacion():
    with _lock:
        duracion = None
        if "_inicio_ts" in _estado:
            duracion = round(time.time() - _estado["_inicio_ts"], 2)
        _estado["en_conversacion"] = False
        _estado["historial_usuarios"].append({
            "nombre": _estado["ultimo_usuario"],
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duracion_seg": duracion
        })
        _guardar_historial_disco()

def registrar_tiempo_respuesta(segundos):
    with _lock:
        _estado["ultimo_tiempo_respuesta"] = round(segundos, 2)