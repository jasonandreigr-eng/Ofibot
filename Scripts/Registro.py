import os
from Recursos import client, hablar, escuchar_comando

DATABASE_DIR = "/home/semilleroiot/Desktop/Ofibot/Scripts/dataset"
MAX_USUARIOS = 6

CONFIG_NOMBRE = """
Tu tarea es extraer un nombre propio de una frase dicha por una persona.
La persona pudo decir cosas como "me llamo Juan", "soy Juan" o solo "Juan".
Responde SIEMPRE en formato JSON valido con esta estructura exacta:
{
  "nombre": "nombre extraido o null si no se identifica un nombre valido"
}
No agregues texto fuera del JSON.
"""

def contar_usuarios():
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    return len([d for d in os.listdir(DATABASE_DIR) if os.path.isdir(os.path.join(DATABASE_DIR, d))])

def extraer_nombre(texto, intentos=3, espera=3):
    import time
    import json
    for i in range(intentos):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=texto,
                config={
                    "system_instruction": CONFIG_NOMBRE,
                    "response_mime_type": "application/json"
                }
            )
            data = json.loads(response.text)
            return data.get("nombre")
        except Exception as e:
            if i < intentos - 1:
                time.sleep(espera)
    return None

def capturar_nombre_por_voz():
    hablar("No te reconozco. Cual es tu nombre?")
    intentos = 0
    while intentos < 3:
        texto = escuchar_comando()
        if texto != "":
            nombre = extraer_nombre(texto)
            if nombre:
                return nombre.strip().capitalize()
        intentos += 1
    return None

def registrar_usuario_nuevo():
    from Conocer import conocer
    nombre = capturar_nombre_por_voz()
    if nombre is None:
        hablar("No logre escucharte, intentemos mas tarde.")
        return None

    hablar(f"Mucho gusto {nombre}. Voy a tomarte unas fotos, mira a la camara.")
    exito = conocer(nombre)

    if exito:
        hablar(f"Listo {nombre}, ya te conozco.")
        return nombre
    else:
        hablar("Hubo un problema registrandote.")
        return None