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

# --- Imports para Formularios ---
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


# ==========================================================
# ===== INICIO DE LA SOLUCIÓN: AUTO-SIMULACIÓN EN TEST =====
# ==========================================================
# Comprobar si estamos en modo "testing" (definido en conftest.py)
if os.environ.get("FLASK_ENV") == "testing":
    print("=" * 50)
    print("¡¡¡ATENCIÓN: SERVIDOR EN MODO DE PRUEBA!!!")
    print("Reemplazando 'session_manager', 'gestor_tareas' y 'tasks' con simulaciones.")
    print("=" * 50)

    # 1. Mock Session Manager (como antes)
    class MockSessionManager:
        def autenticar_en_siped(self, username, password):
            """Simula la autenticación."""
            print(f"AUTENTICACIÓN SIMULADA para {username}...")
            if password in ["testpass", "pass", "test_password"]:
                return {"siped_cookies": "mock-cookie-para-" + username}
            return None

    # Sobrescribir la variable del módulo importado
    session_manager = MockSessionManager()

    # 2. Mock Gestor Tareas
    # (Este es el estado global simulado que controlará el test)
    MOCK_TASK_STATES = {
        "fase_1": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        "fase_2": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        "fase_3": {"estado": "IDLE", "resultado": "En espera (Mock)"},
    }

    class MockGestorTareas:
        def obtener_estado_tarea(self, task_id, nombre_fase):
            """Devuelve el estado desde el diccionario MOCK_TASK_STATES"""
            print(
                f"MOCK: Obteniendo estado para {nombre_fase}: {MOCK_TASK_STATES.get(nombre_fase)}"
            )
            return MOCK_TASK_STATES.get(
                nombre_fase, {"estado": "FAILURE", "resultado": "Fase desconocida"}
            )

        def registrar_tarea_iniciada(self, nombre_fase, tarea):
            """Al iniciar, simula ponerla en PENDING"""
            print(f"MOCK: Registrando tarea {nombre_fase} con ID {tarea.id}")
            # El estado real lo pondrá el click, pero el poll siguiente lo verá
            MOCK_TASK_STATES[nombre_fase] = {
                "estado": "STARTED",
                "resultado": "En cola (Mock)...",
            }  # <--- CAMBIO a STARTED

        def obtener_id_tarea(self, nombre_fase):
            """Devuelve un ID falso"""
            return f"mock-id-{nombre_fase}"

        def resetear_id_tarea(self, nombre_fase):
            print(f"MOCK: Reseteando estado de {nombre_fase}")
            MOCK_TASK_STATES[nombre_fase] = {
                "estado": "IDLE",
                "resultado": "En espera (Mock)",
            }

    # Sobrescribir la variable del módulo importado
    gestor_tareas = MockGestorTareas()

    # 3. Mock Tasks (Celery)
    # Simulamos el objeto 'tarea' que devuelve .delay()
    class MockTask:
        def __init__(self, task_id):
            self.id = task_id

        @classmethod
        def delay(cls, *args, **kwargs):
            # Crea una tarea con un ID falso y la devuelve
            task_id = f"mock-celery-id-{cls.name}"
            print(f"MOCK: Tarea {cls.name} .delay() llamada.")
            # La simulación de 'registrar_tarea_iniciada' se encargará del estado
            return MockTask(task_id)

    # Creamos clases falsas con el atributo 'name' para simular
    class MockFase1(MockTask):
        name = "fase_1"

    class MockFase2(MockTask):
        name = "fase_2"

    class MockFase3(MockTask):
        name = "fase_3"

    # Sobrescribir las variables de las tareas importadas
    fase_1_lista_task = MockFase1
    fase_2_movimientos_task = MockFase2
    fase_3_documentos_task = MockFase3
# ========================================================
# ===== FIN DE LA SOLUCIÓN: AUTO-SIMULACIÓN EN TEST =====
# ========================================================


# --- Configuración de Flask ---
app = Flask(__name__)
# La 'secret_key' es VITAL para que funcione la sesión de Flask
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod-MUY-SECRETO"
)


# ========================================================
# ===== INICIO DE ENDPOINTS DE CONTROL PARA TESTS =====
# ========================================================
if os.environ.get("FLASK_ENV") == "testing":

    @app.route("/_test/set_state", methods=["POST"])
    def set_mock_state():
        """
        Un endpoint solo para tests que permite a Selenium (Proceso 1)
        controlar el estado de las tareas del servidor (Proceso 2).
        """
        data = request.json
        fase = data.get("fase")
        estado = data.get("estado")
        resultado = data.get("resultado")

        if fase in MOCK_TASK_STATES:
            MOCK_TASK_STATES[fase] = {"estado": estado, "resultado": resultado}
            print(f"MOCK: Estado de {fase} forzado a: {MOCK_TASK_STATES[fase]}")
            return jsonify(
                {"status": "success", "fase": fase, "new_state": MOCK_TASK_STATES[fase]}
            )
        return jsonify({"status": "error", "message": "Fase no encontrada"}), 404

    @app.route("/_test/reset_states", methods=["POST"])
    def reset_mock_states():
        """Resetea todos los estados a IDLE para el proximo test"""
        global MOCK_TASK_STATES
        MOCK_TASK_STATES = {
            "fase_1": {"estado": "IDLE", "resultado": "En espera (Mock)"},
            "fase_2": {"estado": "IDLE", "resultado": "En espera (Mock)"},
            "fase_3": {"estado": "IDLE", "resultado": "En espera (Mock)"},
        }
        print("MOCK: Todos los estados de tareas reseteados a IDLE")
        return jsonify({"status": "success", "states": MOCK_TASK_STATES})
# ========================================================
# ===== FIN DE ENDPOINTS DE CONTROL PARA TESTS =====
# ========================================================


# --- Definición del Formulario de Login ---
class LoginForm(FlaskForm):
    username = StringField("Usuario (Intranet)", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")


# --- Decorador de Autenticación ---
def login_required(f):
    """
    Decorador para proteger rutas. Verifica que las cookies de SIPED
    existan en la sesión de Flask.
    """

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
    """
    Ruta para manejar el login del usuario.
    Valida credenciales contra SIPED y guarda cookies en la sesión.
    """
    # Si el usuario ya está logueado, lo mandamos al inicio
    if "siped_cookies" in session:
        return redirect(url_for("indice"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        print(f"Intentando autenticar a {username}...")
        # NOTA: Esta llamada usará el MockSessionManager si estamos en modo test
        cookies_dict = session_manager.autenticar_en_siped(username, password)

        if cookies_dict:
            # ÉXITO: Guardamos las cookies en la sesión de Flask
            session["siped_cookies"] = cookies_dict
            session["username"] = username  # Guardamos el nombre de usuario
            flash(f"¡Bienvenido, {username}! Sesión iniciada.", "success")
            return redirect(url_for("indice"))
        else:
            # FALLO:
            flash("Error de autenticación. Usuario o contraseña incorrectos.", "error")

    # Si es GET o el formulario falló, mostramos la página de login
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    """Limpia la sesión de Flask y redirige al login."""
    session.pop("siped_cookies", None)
    session.pop("username", None)
    flash("Sesión cerrada exitosamente.", "success")
    return redirect(url_for("login"))


# --- Rutas de la Aplicación (Protegidas) ---


@app.route("/fragmento/mensajes")
def fragmento_mensajes():
    """Devuelve el fragmento HTML de los mensajes flash."""
    return render_template("_fragmento_mensajes.html")


@app.route("/")
@login_required  # <<< PROTEGER
def indice():
    """
    Ruta principal. Muestra la página de inicio.
    """
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()

    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
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
        username=session.get("username"),  # <<< Pasar username al template
    )


@app.route("/iniciar/<nombre_fase>", methods=["POST"])
@login_required  # <<< PROTEGER
def iniciar_fase(nombre_fase):
    """
    Ruta genérica para iniciar cualquier fase.
    """
    # NOTA: Este mapa usará las MockTasks si estamos en modo test
    mapa_tareas = {
        "fase_1": fase_1_lista_task,
        "fase_2": fase_2_movimientos_task,
        "fase_3": fase_3_documentos_task,
    }

    if nombre_fase not in mapa_tareas:
        flash(f"Fase '{nombre_fase}' no reconocida.", "error")
        return render_template("_fragmento_mensajes.html"), 400

    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
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
    # NOTA: Esta llamada usará la MockTask si estamos en modo test
    tarea = mapa_tareas[nombre_fase].delay(cookies=cookies_del_usuario)

    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)
    flash(f"Fase {nombre_fase.split('_')[1]} iniciada con ID: {tarea.id}", "success")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/resetear_estado/<nombre_fase>")
@login_required  # <<< PROTEGER
def resetear_estado(nombre_fase):
    """
    Ruta de utilidad para resetear manualmente el ID de la última tarea.
    """
    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
    gestor_tareas.resetear_id_tarea(nombre_fase)
    flash(f"Estado de {nombre_fase} reseteado manualmente.", "info")

    return render_template("_fragmento_mensajes.html"), 200


@app.route("/fragmento/estado/<nombre_fase>")
@login_required  # <<< PROTEGER
def fragmento_estado(nombre_fase):
    """
    Devuelve el fragmento HTML del estado y resultado de una fase específica.
    """
    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
    estado = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    return render_template("_fragmento_estado.html", id_fase=nombre_fase, estado=estado)


@app.route("/fragmento/pdfs")
@login_required  # <<< PROTEGER
def fragmento_pdfs():
    """
    Devuelve el fragmento HTML de la lista de PDFs.
    """
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()
    return render_template("_fragmento_pdfs.html", archivos_pdf=lista_pdf)


@app.route("/estado_tarea/<nombre_fase>")
@login_required  # <<< PROTEGER
def verificar_estado_tarea(nombre_fase):
    """
    Endpoint para que el frontend pueda consultar el estado de una tarea (JSON).
    """
    # NOTA: Esta llamada usará el MockGestorTareas si estamos en modo test
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
@login_required  # <<< PROTEGER
def descargar_archivo(nombre_archivo):
    """
    Ruta para servir archivos PDF de forma segura.
    """
    return send_from_directory(
        directory=config.DOCUMENTOS_OUTPUT_DIR, path=nombre_archivo, as_attachment=True
    )


# --- Bloque de Ejecución ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
