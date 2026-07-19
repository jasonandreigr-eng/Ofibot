# estado_global.py
import threading
import json
import time
import uuid
from datetime import datetime, timedelta

_lock = threading.Lock()

_estado = {
    "estado_animo": "neutro",       # feliz|neutral|molesto|triste|emocionado
    "accion": "ninguna",
    "sociabilidad": 5,               # escala 1-10, ajustable en panel tecnico
    "formalidad": 5,                 # escala 1-10
    "ultimo_usuario": None,
    "en_conversacion": False,
    "ultimo_tiempo_respuesta": None, # segundos
    "historial_usuarios": [],        # lista de dicts: {nombre, hora, duracion}
    "recordatorios": []              # lista de dicts: {id, usuario, texto, hora_disparo, tipo, activo}
}

HISTORIAL_FILE = "historial_usuarios.json"

def _guardar_historial_disco():
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(_estado["historial_usuarios"], f, indent=2, ensure_ascii=False)

def set_accion(nueva_accion):
    with _lock:
        _estado["accion"] = nueva_accion
        
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

# ---------------- RECORDATORIOS ----------------

def agregar_recordatorio(usuario, texto, segundos, tipo="recordatorio"):
    with _lock:
        nuevo = {
            "id": str(uuid.uuid4()),
            "usuario": usuario,
            "texto": texto,
            "hora_disparo": (datetime.now() + timedelta(seconds=segundos)).isoformat(),
            "tipo": tipo,
            "activo": True
        }
        _estado["recordatorios"].append(nuevo)
        return nuevo["id"]

def obtener_recordatorios_pendientes():
    with _lock:
        return [r for r in _estado["recordatorios"] if r["activo"]]

def cancelar_recordatorio(id_recordatorio):
    with _lock:
        for r in _estado["recordatorios"]:
            if r["id"] == id_recordatorio:
                r["activo"] = False
                return True
        return False

def revisar_vencidos():
    """Devuelve los recordatorios que ya vencieron y los marca como inactivos."""
    ahora = datetime.now()
    vencidos = []
    with _lock:
        for r in _estado["recordatorios"]:
            if r["activo"] and datetime.fromisoformat(r["hora_disparo"]) <= ahora:
                r["activo"] = False
                vencidos.append(r)
    return vencidos