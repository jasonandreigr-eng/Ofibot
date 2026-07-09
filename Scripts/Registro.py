import os

DATABASE_DIR = "/home/semilleroiot/Desktop/Ofibot/Scripts/dataset"
MAX_USUARIOS = 6

def contar_usuarios():
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    return len([d for d in os.listdir(DATABASE_DIR) if os.path.isdir(os.path.join(DATABASE_DIR, d))])

def capturar_nombre_por_voz():
    hablar("No te reconozco. Cual es tu nombre?")
    intentos = 0
    while intentos < 3:
        nombre = escuchar_comando()
        if nombre != "":
            return nombre.strip().split()[0].capitalize()
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