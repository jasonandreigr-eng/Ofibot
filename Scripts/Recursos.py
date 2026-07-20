import os
import wave
import unicodedata
import numpy as np
import sounddevice as sd
import soundfile as sf
import Estado_global
import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from piper import PiperVoice
from piper import SynthesisConfig
from openwakeword.model import Model

WAKEWORD_PATH = "/home/semilleroiot/Desktop/Ofibot/Modelos/ofibot.onnx"
PIPER_VOICE_PATH = "/home/semilleroiot/Desktop/Ofibot/pipervoices/es_ES-carlfm-x_low.onnx"
RESPUESTA_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/Respuesta.wav"
INTERACCION_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/interaccion.wav"

fs = 16000
tiempo_grab = int(fs * 3)
UMBRAL_SILENCIO = 10000
TEXTO_AMARA = "subtitulos realizados por la comunidad de amara.org"

print("Cargando modelos...")

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
client = genai.Client(api_key=gemini_key)
openai_client = OpenAI(api_key=openai_key)

voice = PiperVoice.load(PIPER_VOICE_PATH)
syn_config = SynthesisConfig(volume=2.5, length_scale=0.8)

wake_model = Model(
    wakeword_models=[WAKEWORD_PATH],
    inference_framework="onnx"
)
for _ in range(5):
    audio_dummy = np.zeros(int(fs * 3), dtype='int16')
    wake_model.predict(audio_dummy)

print("Modelos listos. Ofibot en espera.")

def obtener_hora():
    zona = ZoneInfo("America/Bogota")
    ahora = datetime.now(zona)
    return ahora.strftime("%H:%M del %d/%m/%Y")

def hablar(texto):
    with wave.open(RESPUESTA_WAV, "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file, syn_config=syn_config)
    data, samplerate = sf.read(RESPUESTA_WAV)
    sd.play(data, samplerate)
    sd.wait()

MARGEN_INICIO_SEG = 0.2

def es_audio_vacio(audio):
    muestras_margen = int(fs * MARGEN_INICIO_SEG)
    audio_util = audio[muestras_margen:]
    return np.abs(audio_util).max() < UMBRAL_SILENCIO

SONIDO_CIERRE_WAV = "/home/semilleroiot/Desktop/Ofibot/Audios/cierre.wav"

def reproducir_cierre():
    data, samplerate = sf.read(SONIDO_CIERRE_WAV)
    sd.play(data, samplerate)
    sd.wait()

def construir_Config():
    estado = Estado_global.get_estado()
    config = f"""
    Eres Ofibot, un robot asistente de oficina amigable y servicial.
    Te estan hablando desde un microfono, si detectas un error de transcripcion dilo con naturalidad.
    En caso que se refieran a ti con un nombre distinto a Ofibot ignoralo, es error de transcripcion.
    Tu personalidad es:
    - Nivel de sociabilidad actual (1-10): {estado['sociabilidad']}
    - Nivel de formalidad actual (1-10): {estado['formalidad']}
    - Nivel de estado de animo base actual (1-10, 1=triste, 10=feliz/alegre): {estado['estado_animo_nivel']}
    - Conciso en tus respuestas (maximo 2-3 oraciones)
    - Siempre hablas en espanol
    Ajusta tu tono de respuesta segun estos valores.

    El nombre del usuario que te llama se te dara en cada mensaje, usalo con naturalidad.
    Si el nombre del usuario es "Unknown", NO uses ningun nombre al dirigirte a el,
    tratalo de forma neutral y amigable sin mencionar identidad (ej: "hola, en que te puedo ayudar").

    Responde SIEMPRE en formato JSON valido con esta estructura exacta:
    {{
      "usuario": "nombre del usuario",
      "estado_animo": "saludo|neutro|enojo|triste|emocion|duda|aburrimiento|asombro|descanso",
      "accion": "ninguna|baila|celebra|saluda|asiente|niega|recordatorio|consultar_calendario|consultar_correos",
      "recordatorio_texto": "texto a recordar o null",
      "recordatorio_segundos": numero o null,
      "finalizar": true o false,
      "respuesta": "texto que se dira en voz alta"
    }}

    El campo accion debe ser "recordatorio" unicamente cuando el usuario pida explicitamente que se le recuerde algo en un tiempo determinado. En ese caso, recordatorio_texto y recordatorio_segundos deben ir completos (convierte minutos/horas a segundos). En cualquier otro caso ambos deben ser null.
    
    El campo finalizar debe ser true unicamente cuando el usuario se despida o de a entender que quiere terminar la conversacion (ej: gracias hasta luego, eso es todo, nos vemos). En cualquier otro caso debe ser false.

    El campo accion debe ser "consultar_calendario" unicamente cuando el usuario pregunte por su agenda, eventos o calendario. En este caso, el campo "respuesta" debe quedar vacio, se completara automaticamente.

    El campo accion debe ser "consultar_correos" unicamente cuando el usuario pregunte por sus correos, emails o bandeja de entrada. En este caso, el campo "respuesta" debe quedar vacio, se completara automaticamente.
    
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


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto)
    return texto.encode('ascii', 'ignore').decode('ascii').lower()

def escuchar_comando(intentos=3, espera=3):
    audio = sd.rec(tiempo_grab, samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    if es_audio_vacio(audio):
        return ""

    with wave.open(INTERACCION_WAV, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(fs)
        wav_file.writeframes(audio.tobytes())

    for i in range(intentos):
        try:
            with open(INTERACCION_WAV, "rb") as f:
                transcripcion = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="es"
                )
            texto = transcripcion.text.strip()

            if normalizar(texto) == TEXTO_AMARA:
                return ""

            return texto
        except Exception as e:
            print(f"error whisper: {e}")
            if i < intentos - 1:
                import time
                time.sleep(espera)

    return None

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def obtener_credenciales_google():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES
    )
    return creds

def obtener_servicio_calendar():
    creds = obtener_credenciales_google()
    return build("calendar", "v3", credentials=creds)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def consultar_eventos_calendario(dias=7):
    servicio = obtener_servicio_calendar()
    zona = ZoneInfo("America/Bogota")
    ahora = datetime.now(zona)
    limite = ahora + timedelta(days=dias)

    eventos_result = servicio.events().list(
        calendarId="primary",
        timeMin=ahora.isoformat(),
        timeMax=limite.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    eventos = eventos_result.get("items", [])

    if not eventos:
        return []

    lista = []
    for evento in eventos:
        inicio = evento["start"].get("dateTime", evento["start"].get("date"))
        lista.append({
            "titulo": evento.get("summary", "Sin titulo"),
            "inicio": inicio
        })

    return lista

def obtener_servicio_gmail():
    creds = obtener_credenciales_google()
    return build("gmail", "v1", credentials=creds)

def consultar_correos_no_leidos(max_resultados=5):
    servicio = obtener_servicio_gmail()

    label_info = servicio.users().labels().get(userId="me", id="UNREAD").execute()
    total_no_leidos = label_info.get("messagesUnread", 0)

    if total_no_leidos == 0:
        return {"total": 0, "correos": []}

    resultado = servicio.users().messages().list(
        userId="me",
        q="is:unread",
        maxResults=max_resultados
    ).execute()

    mensajes = resultado.get("messages", [])

    correos = []
    for msg in mensajes:
        detalle = servicio.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"]
        ).execute()

        headers = detalle.get("payload", {}).get("headers", [])
        asunto = next((h["value"] for h in headers if h["name"] == "Subject"), "Sin asunto")
        remitente = next((h["value"] for h in headers if h["name"] == "From"), "Desconocido")

        correos.append({"asunto": asunto, "remitente": remitente})

    return {"total": total_no_leidos, "correos": correos}