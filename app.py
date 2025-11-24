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
)
import os
import config
from tasks import fase_1_lista_task, fase_2_movimientos_task, fase_3_documentos_task
import gestor_tareas
import gestor_almacenamiento
import session_manager
from functools import wraps

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


# --- Configuración de Flask ---
app = Flask(__name__)
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

        # Autenticación real usando session_manager.py
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
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()

    # Obtener estado real de las tareas
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
    }

    return render_template(
        "index.html",
        archivos_pdf=lista_pdf,
        estados_tareas=estados_tareas,
        username=session.get("username"),
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
        flash(f"Fase '{nombre_fase}' no reconocida.", "error")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    
    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash(
            f"La Fase {nombre_fase.split('_')[1]} ya está en curso (Estado: {estado_actual['estado']}).",
            "warning",
        )
        return render_template("_fragmento_mensajes.html"), 200

    cookies_del_usuario = session["siped_cookies"]
    
    # Lanzar tarea real de Celery
    tarea = mapa_tareas[nombre_fase].delay(cookies=cookies_del_usuario)

    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)
    flash(f"Fase {nombre_fase.split('_')[1]} iniciada con ID: {tarea.id}", "success")
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
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()
    return render_template("_fragmento_pdfs.html", archivos_pdf=lista_pdf)


@app.route("/estado_tarea/<nombre_fase>")
@login_required
def verificar_estado_tarea(nombre_fase):
    estado = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    return jsonify(
        {
            "state": estado["estado"],
            "result": estado["resultado"],
            "refresh": estado.get("recargar", False),
        }
    )


@app.route("/descargar/<nombre_archivo>")
@login_required
def descargar_archivo(nombre_archivo):
    return send_from_directory(
        directory=
