# app.py
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
    request,
    session,
    abort,
)
import os
import config
from tasks import (
    fase_1_lista_task,
    fase_2_movimientos_task,
    fase_3_documentos_task,
    fase_unico_task,
)
import gestor_tareas
import gestor_almacenamiento
import session_manager
import utils
from functools import wraps

# Import necesario para producción detrás de un Proxy (Railway/Nginx)
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

# --- Configuración de Flask ---
app = Flask(__name__)

# Configuración de ProxyFix para Producción
# x_for=1: Confía en 1 nivel de proxy para la IP
# x_proto=1: Confía en 1 nivel de proxy para el protocolo (HTTP/HTTPS)
# x_host=1: Confía en 1 nivel de proxy para el host
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod-MUY-SECRETO"
)


# --- Definición del Formulario de Login ---
class LoginForm(FlaskForm):
    username = StringField("Usuario (Intranet)", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")


# --- Decorador de Autenticación ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "siped_cookies" not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# --- Rutas de Autenticación ---


@app.route("/login", methods=["GET", "POST"])
def login():
    if "siped_cookies" in session:
        return redirect(url_for("indice"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        cookies_dict = session_manager.autenticar_en_siped(username, password)

        if cookies_dict:
            session["siped_cookies"] = cookies_dict
            session["username"] = username
            flash(f"¡Bienvenido, {username}! Sesión iniciada.", "success")
            return redirect(url_for("indice"))
        else:
            flash("Error de autenticación. Usuario o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    session.pop("siped_cookies", None)
    session.pop("username", None)
    flash("Sesión cerrada exitosamente.", "success")
    return redirect(url_for("login"))


# --- Rutas de la Aplicación (Protegidas) ---


@app.route("/fragmento/mensajes")
def fragmento_mensajes():
    return render_template("_fragmento_mensajes.html")


@app.route("/")
@login_required
def indice():
    usuario = session.get("username")

    # Obtener archivos de las 3 fases
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf(usuario)
    existe_maestro = gestor_almacenamiento.verificar_csv_maestro(usuario)
    lista_movimientos = gestor_almacenamiento.listar_archivos_movimientos(usuario)

    ruta_usuario = utils.obtener_ruta_usuario(usuario)
    ruta_csv = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)

    expedientes_disponibles = utils.leer_csv_a_diccionario(ruta_csv)
    if not expedientes_disponibles:
        expedientes_disponibles = []

    estados_tareas = {
        "fase_1": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_1"), "fase_1"
        ),
        "fase_2": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_2"), "fase_2"
        ),
        "fase_3": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_3"), "fase_3"
        ),
        "fase_unico": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_unico"), "fase_unico"
        ),
    }

    return render_template(
        "index.html",
        archivos_pdf=lista_pdf,
        existe_maestro=existe_maestro,
        lista_movimientos=lista_movimientos,
        estados_tareas=estados_tareas,
        username=session.get("username"),
        expedientes_disponibles=expedientes_disponibles,
    )


@app.route("/iniciar/<nombre_fase>", methods=["POST"])
@login_required
def iniciar_fase(nombre_fase):
    mapa_tareas = {
        "fase_1": fase_1_lista_task,
        "fase_2": fase_2_movimientos_task,
        "fase_3": fase_3_documentos_task,
    }

    if nombre_fase not in mapa_tareas:
        flash(f"Fase '{nombre_fase}' no reconocida o requiere parámetros.", "error")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash(
            f"La Fase {nombre_fase} ya está en curso.",
            "warning",
        )
        return render_template("_fragmento_mensajes.html"), 200

    cookies_del_usuario = session["siped_cookies"]
    usuario = session["username"]

    tarea = mapa_tareas[nombre_fase].delay(
        cookies=cookies_del_usuario, username=usuario
    )
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)

    flash(f"Fase {nombre_fase.split('_')[1]} iniciada con ID: {tarea.id}", "success")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/iniciar_descarga_unico", methods=["POST"])
@login_required
def iniciar_descarga_unico():
    nro_expediente = request.form.get("expediente_seleccionado")
    nombre_fase = "fase_unico"

    if not nro_expediente:
        flash("Debe seleccionar un expediente.", "warning")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash(f"Ya hay una descarga individual en curso.", "warning")
        return render_template("_fragmento_mensajes.html"), 200

    cookies_del_usuario = session["siped_cookies"]
    usuario = session["username"]

    tarea = fase_unico_task.delay(
        cookies=cookies_del_usuario, nro_expediente=nro_expediente, username=usuario
    )

    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)
    flash(f"Procesando expediente {nro_expediente}...", "success")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/resetear_estado/<nombre_fase>")
@login_required
def resetear_estado(nombre_fase):
    gestor_tareas.resetear_id_tarea(nombre_fase)
    flash(f"Estado de {nombre_fase} reseteado manualmente.", "info")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/fragmento/estado/<nombre_fase>")
@login_required
def fragmento_estado(nombre_fase):
    estado = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    return render_template("_fragmento_estado.html", id_fase=nombre_fase, estado=estado)


@app.route("/fragmento/pdfs")
@login_required
def fragmento_pdfs():
    usuario = session.get("username")
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf(usuario)
    return render_template("_fragmento_pdfs.html", archivos_pdf=lista_pdf)


@app.route("/descargar/<tipo>/<nombre_archivo>")
@login_required
def descargar_archivo(tipo, nombre_archivo):
    """
    Descarga archivos basándose en su tipo (carpeta de origen).
    """
    usuario = session.get("username")
    ruta_usuario = utils.obtener_ruta_usuario(usuario)

    directorio = None

    if tipo == "maestro":
        # Fase 1: En la raíz del usuario
        if nombre_archivo == config.LISTA_EXPEDIENTES_CSV:
            directorio = ruta_usuario
    elif tipo == "movimientos":
        # Fase 2: Carpeta de movimientos
        directorio = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    elif tipo == "documentos":
        # Fase 3: Carpeta de documentos PDF
        directorio = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    if not directorio or not os.path.exists(os.path.join(directorio, nombre_archivo)):
        abort(404)

    return send_from_directory(
        directory=directorio, path=nombre_archivo, as_attachment=True
    )


if __name__ == "__main__":
    # Nota: Este bloque se ignora en producción con Gunicorn
    app.run(debug=True, host="0.0.0.0", port=5001)
