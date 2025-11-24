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


# ==========================================================
# ===== MODO TESTING (Simulaciones) =====
# ==========================================================
if os.environ.get("FLASK_ENV") == "testing":
    print("=" * 50)
    print("¡¡¡ATENCIÓN: SERVIDOR EN MODO DE PRUEBA!!!")
    print("=" * 50)

    class MockSessionManager:
        def autenticar_en_siped(self, username, password):
            print(f"AUTENTICACIÓN SIMULADA para {username}...")
            if password in ["testpass", "pass", "test_password"]:
                return {"siped_cookies": "mock-cookie-para-" + username}
            return None

    session_manager = MockSessionManager()

    MOCK_TASK_STATES = {
        "fase_1": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        "fase_2": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        "fase_3": {"estado": "IDLE", "resultado": "En espera (Mock)"},
    }

    class MockGestorTareas:
        def obtener_estado_tarea(self, task_id, nombre_fase):
            return MOCK_TASK_STATES.get(
                nombre_fase, {"estado": "FAILURE", "resultado": "Fase desconocida"}
            )

        def registrar_tarea_iniciada(self, nombre_fase, tarea):
            MOCK_TASK_STATES[nombre_fase] = {
                "estado": "STARTED",
                "resultado": "En cola (Mock)...",
            }

        def obtener_id_tarea(self, nombre_fase):
            return f"mock-id-{nombre_fase}"

        def resetear_id_tarea(self, nombre_fase):
            MOCK_TASK_STATES[nombre_fase] = {
                "estado": "IDLE",
                "resultado": "En espera (Mock)",
            }

    gestor_tareas = MockGestorTareas()

    class MockTask:
        def __init__(self, task_id):
            self.id = task_id

        @classmethod
        def delay(cls, *args, **kwargs):
            task_id = f"mock-celery-id-{cls.name}"
            return MockTask(task_id)

    class MockFase1(MockTask):
        name = "fase_1"

    class MockFase2(MockTask):
        name = "fase_2"

    class MockFase3(MockTask):
        name = "fase_3"

    fase_1_lista_task = MockFase1
    fase_2_movimientos_task = MockFase2
    fase_3_documentos_task = MockFase3


# --- Configuración de Flask ---
app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod-MUY-SECRETO"
)


# ========================================================
# ===== ENDPOINTS DE CONTROL PARA TESTS =====
# ========================================================
if os.environ.get("FLASK_ENV") == "testing":

    @app.route("/_test/set_state", methods=["POST"])
    def set_mock_state():
        data = request.json
        fase = data.get("fase")
        estado = data.get("estado")
        resultado = data.get("resultado")

        if fase in MOCK_TASK_STATES:
            MOCK_TASK_STATES[fase] = {"estado": estado, "resultado": resultado}
            return jsonify(
                {"status": "success", "fase": fase, "new_state": MOCK_TASK_STATES[fase]}
            )
        return jsonify({"status": "error", "message": "Fase no encontrada"}), 404

    @app.route("/_test/reset_states", methods=["POST"])
    def reset_mock_states():
        global MOCK_TASK_STATES
        MOCK_TASK_STATES = {
            "fase_1": {"estado": "IDLE", "resultado": "En espera (Mock)"},
            "fase_2": {"estado": "IDLE", "resultado": "En espera (Mock)"},
            "fase_3": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        }
        return jsonify({"status": "success", "states": MOCK_TASK_STATES})


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
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()

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
        directory=config.DOCUMENTOS_OUTPUT_DIR, path=nombre_archivo, as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
