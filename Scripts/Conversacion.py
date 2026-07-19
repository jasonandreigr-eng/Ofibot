import sounddevice as sd
import Estado_global
from Servidor_web import iniciar_flask
import numpy as np
import time
import json
import threading
from collections import deque
from Registro import contar_usuarios, registrar_usuario_nuevo
from Recursos import client, voice, wake_model, syn_config, hablar, escuchar_comando, obtener_hora, fs
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

def construir_Config():
    estado = Estado_global.get_estado()
    config = """
    Eres Ofibot, un robot asistente de oficina amigable y servicial.
    Te estan hablando desde un microfono, si detectas un error de transcripcion dilo con naturalidad.
    En caso que se refieran a ti con un nombre distinto a Ofibot ignoralo, es error de transcripcion.
    Tu personalidad es:
    - Nivel de sociabilidad actual (1-10): {estado['sociabilidad']}
    - Nivel de formalidad actual (1-10): {estado['formalidad']}
    - Conciso en tus respuestas (maximo 2-3 oraciones)
    - Siempre hablas en espanol
    Ajusta tu tono de respuesta segun estos valores.

    El nombre del usuario que te llama se te dara en cada mensaje, usalo con naturalidad.
    Si el nombre del usuario es "Unknown", NO uses ningun nombre al dirigirte a el,
    tratalo de forma neutral y amigable sin mencionar identidad (ej: "hola, en que te puedo ayudar").

    Responde SIEMPRE en formato JSON valido con esta estructura exacta:
    {
      "usuario": "nombre del usuario",
      "estado_animo": "saludo|neutro|enojo|triste|emocion|duda|aburrimiento|asombro|descanso",
      "accion": "ninguna|baila|celebra|saluda|asiente|niega|recordatorio",
      "recordatorio_texto": "texto a recordar o null",
      "recordatorio_segundos": numero o null,
      "finalizar": true o false,
      "respuesta": "texto que se dira en voz alta"
    }

    El campo accion debe ser "recordatorio" unicamente cuando el usuario pida explicitamente que se le recuerde algo en un tiempo determinado. En ese caso, recordatorio_texto y recordatorio_segundos deben ir completos (convierte minutos/horas a segundos). En cualquier otro caso ambos deben ser null.
    
    El campo finalizar debe ser true unicamente cuando el usuario se despida o de a entender que quiere terminar la conversacion (ej: gracias hasta luego, eso es todo, nos vemos). En cualquier otro caso debe ser false.

    No agregues texto fuera del JSON.
    """
    return config

# ---------------- GEMINI ----------------

def consultar_gemini(historial, intentos=3, espera=5):
    hora_actual = obtener_hora()
    Config = construir_Config()
    config_dinamico = Config + f"\nHora actual en Colombia: {hora_actual}"
    for i in range(intentos):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=historial,
                config={
                    "system_instruction": config_dinamico,
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
        except Exception as e:
            if i == 0:
                print("Estoy pensando un poco...")
            if i < intentos - 1:
                time.sleep(espera)
            else:
                print(f"error gemini: {e}")
    return {
        "usuario": "desconocido",
        "estado_animo": "neutro",
        "accion": "ninguna",
        "respuesta": "En este momento tengo problemas para pensar."
    }

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

        hablar(respuesta_texto)

        if data.get("finalizar", False):
            print("Despedida detectada. Cerrando conversacion.")
            break

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
                    usuario = identificar_usuario()

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