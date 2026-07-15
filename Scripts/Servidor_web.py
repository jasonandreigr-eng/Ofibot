# servidor_web.py
from flask import Flask, jsonify, request, render_template
import Estado_global

app = Flask(__name__)

# ---------- API compartida ----------

@app.route("/api/estado")
def api_estado():
    return jsonify(Estado_global.get_estado())

# ---------- Panel de usuario ----------

@app.route("/")
def panel_usuario():
    return render_template("usuario.html")

@app.route("/api/estado_animo", methods=["POST"])
def api_set_animo():
    nuevo = request.json.get("estado_animo")
    valores_validos = ["saludo", "neutro", "emocion", "triste", "asombro", "enojo", "duda", "descanso", "aburrimiento"]
    if nuevo not in valores_validos:
        return jsonify({"error": "estado_animo invalido"}), 400
    Estado_global.set_estado_animo(nuevo)
    return jsonify({"ok": True})

# ---------- Panel tecnico (protegido) ----------

TOKEN_TECNICO = "oneforall"

def requiere_token():
    token = request.headers.get("Authorization")
    return token == f"Bearer {TOKEN_TECNICO}"

@app.route("/tecnico")
def panel_tecnico():
    return render_template("tecnico.html")

@app.route("/api/config", methods=["POST"])
def api_set_config():
    if not requiere_token():
        return jsonify({"error": "no autorizado"}), 401
    data = request.json
    Estado_global.set_config(
        sociabilidad=data.get("sociabilidad"),
        formalidad=data.get("formalidad")
    )
    return jsonify({"ok": True})

@app.route("/api/historial")
def api_historial():
    if not requiere_token():
        return jsonify({"error": "no autorizado"}), 401
    return jsonify(Estado_global.get_estado()["historial_usuarios"])
def iniciar_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    # host=0.0.0.0 permite acceso desde cualquier dispositivo en la misma red
    iniciar_flask()