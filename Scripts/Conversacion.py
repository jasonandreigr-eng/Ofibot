import sounddevice as sd
import Estado_global
from Servidor_web import iniciar_flask
import numpy as np
import time
import json
import threading
from collections import deque
from Registro import contar_usuarios, registrar_usuario_nuevo
from Recursos import client, voice, wake_model, syn_config, hablar, escuchar_comando, consultar_gemini, fs, reproducir_cierre,consultar_correos_no_leidos, consultar_eventos_calendario	
import Movimientos
import expresiones

# ---------------- CONFIGURACION GENERAL ----------------

WAKEWORD_PATH = "/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"
PIPER_VOICE_PATH = "/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx"
RESPUESTA_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/Respuesta.wav"
INTERACCION_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/interaccion.wav"

fs = 16000
chunk_size = int(fs * 2)
tiempo_grab = int(fs * 3)
umbral_wakeword = 0.25
UMBRAL_SILENCIO = 10000  # ajustar segun sensibilidad del microfono
TEXTO_AMARA = "Subtitulos realizados por la comunidad de amara.org"


# ---------------- RECONOCIMIENTO FACIAL (carga bajo demanda) ----------------

def identificar_usuario():
    from Buscar_Rostro import buscar_rostro
    nombre = buscar_rostro()
    return nombre

# ---------------- LOOP DE CONVERSACION ----------------

def loop_conversacion(usuario):
    Estado_global.marcar_inicio_conversacion(usuario)
    historial = []
    print(f"Iniciando conversacion con {usuario}")
    if usuario == "Unknown":
        hablar("Hola, como te puedo ayudar")
    else:
        hablar(f"Hola {usuario}, como te puedo ayudar")
    while True:
        print("Escuchando comando...")
        time.sleep(0.05)
        texto = escuchar_comando()

        if texto is None:
            hablar("En este momento no puedo escuchar")
            break

        if texto == "":
            print("Sin nuevas palabras. Cerrando conversacion.")
            break

        print(f"{usuario} dijo: {texto}")
        mensaje = f"[Usuario: {usuario}] {texto}"
        historial.append({"role": "user", "parts": [{"text": mensaje}]})

        t0 = time.time()
        data = consultar_gemini(historial)
        t1 = time.time()
        Estado_global.registrar_tiempo_respuesta(t1 - t0)

        respuesta_texto = data.get("respuesta", "")
        print(f"Ofibot ({data.get('estado_animo')}, accion: {data.get('accion')}): {respuesta_texto}")

        Estado_global.set_estado_animo(data.get("estado_animo", "neutro"))
        Estado_global.set_accion(data.get("accion", "ninguna"))

        historial.append({"role": "model", "parts": [{"text": json.dumps(data)}]})

        if data.get("accion", "ninguna") == "recordatorio":
            texto_rec = data.get("recordatorio_texto")
            segundos_rec = data.get("recordatorio_segundos")
            if texto_rec and segundos_rec:
                Estado_global.agregar_recordatorio(usuario, texto_rec, segundos_rec)
        if data.get("accion") == "consultar_calendario":
            eventos = consultar_eventos_calendario()
            if not eventos:
                resumen_eventos = "No hay eventos proximos en el calendario."
            else:
                resumen_eventos = "\n".join([f"{e['titulo']} - {e['inicio']}" for e in eventos])

            historial.append({"role": "user", "parts": [{"text": f"[Datos del calendario]\n{resumen_eventos}\nResume esto en voz para el usuario."}]})
            data = consultar_gemini(historial)
            respuesta_texto = data.get("respuesta", "")
            historial.append({"role": "model", "parts": [{"text": json.dumps(data)}]})
            
        if data.get("accion") == "consultar_correos":
            info = consultar_correos_no_leidos()
            if info["total"] == 0:
                resumen_correos = "No hay correos sin leer."
            else:
                detalle = "\n".join([f"{c['asunto']} - {c['remitente']}" for c in info["correos"]])
                resumen_correos = f"Total no leidos: {info['total']}\n{detalle}"

            historial.append({"role": "user", "parts": [{"text": f"[Datos de correo]\n{resumen_correos}\nResume esto en voz para el usuario."}]})
            data = consultar_gemini(historial)
            respuesta_texto = data.get("respuesta", "")
            historial.append({"role": "model", "parts": [{"text": json.dumps(data)}]})

        hablar(respuesta_texto)

        if data.get("finalizar", False):
            print("Despedida detectada. Cerrando conversacion.")
            break
    reproducir_cierre()
    Estado_global.marcar_fin_conversacion()
    historial.clear()
    print("Historial eliminado. Ofibot en espera.")
    
# ---------------- WAKEWORD ----------------
buffer_size = int(fs * 1)          # 1 segundo de audio, tamano de ventana de analisis
paso_lectura = int(fs * 0.25)      # cada 250ms se evalua una nueva ventana (solapamiento)

buffer_circular = np.zeros(buffer_size, dtype='int16')
lock_buffer = threading.Lock()
muestras_nuevas = 0                # cuenta cuantas muestras nuevas llegaron desde la ultima lectura

en_conversacion = False
ultimo_activacion = 0
delay_reactivacion = 3
MAX_USUARIOS = 6

def callback(indata, frames, time_info, status):
    global buffer_circular, muestras_nuevas

    if en_conversacion:
        return

    datos = indata[:, 0]
    n = len(datos)

    with lock_buffer:
        # desplaza el buffer y agrega los datos nuevos al final (FIFO)
        buffer_circular = np.roll(buffer_circular, -n)
        buffer_circular[-n:] = datos
        muestras_nuevas += n

def hilo_wakeword():
    global ultimo_activacion, en_conversacion, muestras_nuevas, buffer_circular

    while True:
        time.sleep(0.05)  # evita busy-waiting

        if en_conversacion:
            continue

        if muestras_nuevas < paso_lectura:
            continue

        with lock_buffer:
            audio_array = buffer_circular.copy()
            muestras_nuevas = 0

        if time.time() - ultimo_activacion < delay_reactivacion:
            continue

        prediction = wake_model.predict(audio_array)

        for wakeword, score in prediction.items():
            if score > umbral_wakeword:
                print(f"Wakeword detectada ({score:.2f})")
                ultimo_activacion = time.time()
                en_conversacion = True

                # reset a ceros para arrancar limpio en la proxima escucha
                with lock_buffer:
                    buffer_circular[:] = 0
                    muestras_nuevas = 0

                try:
                    Estado_global.set_buscando_rostro(True)
                    usuario = identificar_usuario()
                    Estado_global.set_buscando_rostro(False)

                    print(f"Usuario identificado: {usuario}")

                    if usuario is None:
                        hablar("No veo a nadie, te puedes acercar un poco mas?")
                        continue

                    if usuario == "Unknown":
                        if contar_usuarios() < MAX_USUARIOS:
                            usuario = registrar_usuario_nuevo()
                            if usuario is None:
                                continue
                        else:
                            hablar("Ya tengo el cupo maximo de usuarios registrados, pero puedo ayudarte igual.")

                    loop_conversacion(usuario)
                finally:
                    time.sleep(1)
                    ultimo_activacion = time.time()

                    # reset adicional al volver de la conversacion, por seguridad
                    with lock_buffer:
                        buffer_circular[:] = 0
                        muestras_nuevas = 0

                    en_conversacion = False
                    
# ---------------- GESTOS EN PARALELO ----------------

ACCIONES = {
    "ninguna": Movimientos.ninguna,
    "baila": Movimientos.baila,
    "celebra": Movimientos.celebra,
    "saluda": Movimientos.saluda,
    "asiente": Movimientos.asiente,
    "niega": Movimientos.niega,
    "recordatorio": Movimientos.recordatorio
}

ANIMOS = {
    "saludo": expresiones.saludo,
    "neutro": expresiones.neutro,
    "enojo": expresiones.enojo,
    "triste": expresiones.triste,
    "emocion": expresiones.emocion,
    "duda": expresiones.duda,
    "aburrimiento": expresiones.aburrimiento,
    "asombro": expresiones.asombro,
    "descanso": expresiones.descanso
}

def hilo_gestos():
    ultimo_animo = None
    ultima_accion = None
    while True:
        estado = Estado_global.get_estado()
        animo = estado.get("estado_animo")
        accion = estado.get("accion")

        if animo != ultimo_animo and animo in ANIMOS:
            try:
                ANIMOS[animo]()
            except Exception as e:
                print(f"error expresion: {e}")
            ultimo_animo = animo

        if accion != ultima_accion and accion in ACCIONES:
            if accion == "niega" and estado.get("buscando_rostro"):
                pass
            else:
                try:
                    ACCIONES[accion]()
                except Exception as e:
                    print(f"error movimiento: {e}")
            ultima_accion = accion

        time.sleep(1)

# ---------------- RECORDATORIOS ----------------

def hilo_recordatorios():
    while True:
        time.sleep(5)

        # No revisar mientras hay una conversacion activa
        if en_conversacion:
            continue

        vencidos = Estado_global.revisar_vencidos()
        for r in vencidos:
            hablar(f"Recordatorio: {r['texto']}")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    hilo_gest = threading.Thread(target=hilo_gestos, daemon=True)
    hilo_gest.start()
    print("[GESTOS] Hilo de gestos iniciado")
    hilo_servidor = threading.Thread(target=iniciar_flask, daemon=True)
    hilo_servidor.start()
    print("[SERVIDOR] Hilo del servidor web iniciado en puerto 5000")

    hilo = threading.Thread(target=hilo_wakeword, daemon=True)
    hilo.start()

    hilo_rec = threading.Thread(target=hilo_recordatorios, daemon=True)
    hilo_rec.start()
    print("[RECORDATORIOS] Hilo de recordatorios iniciado")

    with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
        print("Escuchando wakeword...")
        while True:
            time.sleep(0.1)