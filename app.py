"""Controlador principal de la aplicación Flask."""

import os
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

import config
import db_manager
import gestor_almacenamiento
import gestor_tareas
import session_manager
import utils
from catalogos.abogados import ABOGADOS
from catalogos.dependencias import DEPENDENCIAS_POR_LOCALIDAD
from catalogos.localidades import LOCALIDADES
from catalogos.tipos_juicio import TIPOS_JUICIO
from tasks import (
    fase_1_lista_task,
    fase_2_movimientos_task,
    fase_3_documentos_task,
    fase_busqueda_avanzada_task,
    fase_descarga_publica_task,
    fase_publica_task,
    fase_unico_task,
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod-MUY-SECRETO"
)


class LoginForm(FlaskForm):
    """Formulario de autenticación del sistema."""

    username = StringField("Usuario (Intranet)", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")


def login_required(f):
    """Decorador para restringir el acceso a usuarios no autenticados."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "siped_cookies" not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if "siped_cookies" in session:
        return redirect(url_for("indice"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        app.logger.info("Intento de login para usuario: %s", username)
        cookies_dict = session_manager.autenticar_en_siped(username, password)

        if cookies_dict:
            session["siped_cookies"] = cookies_dict
            session["username"] = username
            app.logger.info("Login exitoso para usuario: %s", username)
            flash(f"Bienvenido, {username}! Sesión iniciada.", "success")
            return redirect(url_for("indice"))

        app.logger.warning("Login fallido para usuario: %s", username)
        flash("Error de autenticación. Usuario o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    username = session.get("username")
    session.pop("siped_cookies", None)
    session.pop("username", None)
    app.logger.info("Sesión cerrada para usuario: %s", username)
    flash("Sesión cerrada exitosamente.", "success")
    return redirect(url_for("login"))


@app.route("/fragmento/mensajes")
def fragmento_mensajes():
    return render_template("_fragmento_mensajes.html")


@app.route("/")
@login_required
def indice():
    usuario = session.get("username")
    ruta_usuario = utils.obtener_ruta_usuario(usuario)

    lista_pdf = gestor_almacenamiento.listar_archivos_pdf(usuario)
    existe_maestro = gestor_almacenamiento.verificar_csv_maestro(usuario)
    lista_movimientos = gestor_almacenamiento.listar_archivos_movimientos(usuario)

    if lista_movimientos:
        directorio_movimientos = os.path.join(
            ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR
        )
        lista_movimientos.sort(
            key=lambda x: (
                os.path.getmtime(os.path.join(directorio_movimientos, x))
                if os.path.exists(os.path.join(directorio_movimientos, x))
                else 0
            ),
            reverse=True,
        )

    lista_busquedas = gestor_almacenamiento.listar_archivos_busqueda(usuario)
    ruta_publico_csv = os.path.join(ruta_usuario, "expedientes_publicos.csv")
    existe_publico_csv = os.path.exists(ruta_publico_csv)

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
        "fase_publica": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_publica"), "fase_publica"
        ),
        "fase_busqueda_avanzada": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_busqueda_avanzada"),
            "fase_busqueda_avanzada",
        ),
        "fase_descarga_publica": gestor_tareas.obtener_estado_tarea(
            gestor_tareas.obtener_id_tarea("fase_descarga_publica"),
            "fase_descarga_publica",
        ),
    }

    return render_template(
        "index.html",
        archivos_pdf=lista_pdf,
        existe_maestro=existe_maestro,
        existe_publico_csv=existe_publico_csv,
        lista_busquedas=lista_busquedas,
        lista_movimientos=lista_movimientos,
        estados_tareas=estados_tareas,
        username=session.get("username"),
        expedientes_disponibles=expedientes_disponibles,
        localidades=LOCALIDADES,
        tipos_juicio=TIPOS_JUICIO,
        abogados=ABOGADOS,
        dependencias=DEPENDENCIAS_POR_LOCALIDAD,
    )


@app.route("/iniciar/<nombre_fase>", methods=["POST"])
@login_required
def iniciar_fase(nombre_fase):
    mapa_tareas = {
        "fase_1": fase_1_lista_task,
        "fase_2": fase_2_movimientos_task,
        "fase_3": fase_3_documentos_task,
        "fase_publica": fase_publica_task,
    }

    if nombre_fase not in mapa_tareas:
        app.logger.error("Fase desconocida solicitada: %s", nombre_fase)
        flash(f"Fase '{nombre_fase}' no reconocida.", "error")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )

    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash(f"La Fase {nombre_fase} ya está en curso.", "warning")
        return render_template("_fragmento_mensajes.html"), 200

    cookies_del_usuario = session["siped_cookies"]
    usuario = session["username"]

    tarea = mapa_tareas[nombre_fase].delay(
        cookies=cookies_del_usuario, username=usuario
    )
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)

    etiqueta = (
        nombre_fase.split("_")[1].capitalize() if "_" in nombre_fase else nombre_fase
    )
    flash(f"Proceso {etiqueta} iniciado.", "success")
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
        flash("Actualización en curso. Por favor, aguarde.", "warning")
        return render_template("_fragmento_mensajes.html"), 200

    usuario = session["username"]
    cookies_del_usuario = session["siped_cookies"]

    tarea = fase_unico_task.delay(
        cookies=cookies_del_usuario, nro_expediente=nro_expediente, username=usuario
    )
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)

    app.logger.info(
        "Actualización forzada encolada para expediente %s (Usuario: %s)",
        nro_expediente,
        usuario,
    )
    flash(
        f"Actualizando movimientos y consolidando expediente {nro_expediente} en segundo plano...",
        "success",
    )
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/descargar_por_expediente/<path:nro_expediente>")
@login_required
def descargar_por_expediente(nro_expediente):
    usuario = session["username"]
    ruta_usuario = utils.obtener_ruta_usuario(usuario)

    try:
        expedientes = db_manager.obtener_expedientes(usuario, origen="PRIVADO")
        expediente_data = next(
            (e for e in expedientes if e["expediente"] == nro_expediente), None
        )
    except SQLAlchemyError:
        expediente_data = None

    if not expediente_data:
        ruta_csv = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)
        expedientes_csv = utils.leer_csv_a_diccionario(ruta_csv)
        expediente_data = next(
            (
                e
                for e in (expedientes_csv or [])
                if e.get("expediente") == nro_expediente
            ),
            None,
        )

    if not expediente_data:
        app.logger.error(
            "No se encontró data para descargar expediente: %s", nro_expediente
        )
        abort(404)

    nro_limpio = utils.limpiar_nombre_archivo(nro_expediente)
    caratula_limpia = utils.limpiar_nombre_archivo(
        expediente_data.get("caratula", "SIN_CARATULA")
    )
    nombre_pdf = f"{nro_limpio} - {caratula_limpia} (Consolidado).pdf"

    directorio = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)
    ruta_completa = os.path.join(directorio, nombre_pdf)

    if not os.path.exists(ruta_completa):
        app.logger.error(
            "El archivo físico no existe tras la actualización: %s", ruta_completa
        )
        abort(404)

    respuesta = send_from_directory(
        directory=directorio, path=nombre_pdf, as_attachment=True
    )
    respuesta.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta


@app.route("/iniciar_busqueda_avanzada", methods=["POST"])
@login_required
def iniciar_busqueda_avanzada():
    nombre_fase = "fase_busqueda_avanzada"
    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )

    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash("Búsqueda Avanzada en curso.", "warning")
        return render_template("_fragmento_mensajes.html"), 200

    tarea = fase_busqueda_avanzada_task.delay(
        cookies=session["siped_cookies"],
        username=session["username"],
        filtros=request.form.to_dict(),
    )
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)

    flash("Búsqueda iniciada.", "success")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/fragmento/opciones_busqueda_avanzada")
@login_required
def opciones_busqueda_avanzada():
    usuario = session.get("username")
    try:
        expedientes = db_manager.obtener_expedientes(
            usuario, origen="BUSQUEDA_AVANZADA"
        )
    except SQLAlchemyError:
        return '<option value="">Base de datos ocupada. Reintentando...</option>'

    opciones = ['<option value="">Seleccione un expediente...</option>']
    for exp in expedientes:
        val = exp.get("link_detalle", "")
        text = f"{exp.get('expediente', '')} - {exp.get('caratula', '')}"
        opciones.append(f'<option value="{val}">{text}</option>')

    return "\n".join(opciones)


@app.route("/iniciar_descarga_publico", methods=["POST"])
@login_required
def iniciar_descarga_publico():
    link_detalle = request.form.get("link_detalle_seleccionado")
    nombre_fase = "fase_descarga_publica"

    if not link_detalle:
        flash("Debe seleccionar un expediente.", "warning")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )
    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash("Descarga pública en curso.", "warning")
        return render_template("_fragmento_mensajes.html"), 200

    tarea = fase_descarga_publica_task.delay(
        cookies=session["siped_cookies"],
        link_detalle=link_detalle,
        username=session["username"],
    )
    gestor_tareas.registrar_tarea_iniciada(nombre_fase, tarea)

    flash("Iniciando descarga pública...", "success")
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/resetear_estado/<nombre_fase>")
@login_required
def resetear_estado(nombre_fase):
    gestor_tareas.resetear_id_tarea(nombre_fase)
    flash("Estado reseteado.", "info")
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


@app.route("/fragmento/busquedas")
@login_required
def fragmento_busquedas():
    usuario = session.get("username")
    lista_busquedas = gestor_almacenamiento.listar_archivos_busqueda(usuario)
    return render_template("_fragmento_busquedas.html", lista_busquedas=lista_busquedas)


@app.route("/descargar/<tipo>/<nombre_archivo>")
@login_required
def descargar_archivo(tipo, nombre_archivo):
    usuario = session.get("username")
    ruta_usuario = utils.obtener_ruta_usuario(usuario)
    directorio = None

    if tipo == "maestro":
        if nombre_archivo in [
            config.LISTA_EXPEDIENTES_CSV,
            "expedientes_publicos.csv",
        ] or nombre_archivo.startswith("busqueda_"):
            directorio = ruta_usuario
    elif tipo == "movimientos":
        directorio = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    elif tipo == "documentos":
        directorio = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    if not directorio or not os.path.exists(os.path.join(directorio, nombre_archivo)):
        abort(404)

    respuesta = send_from_directory(
        directory=directorio, path=nombre_archivo, as_attachment=True
    )
    respuesta.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta


@app.route("/debug/<path:nro_expediente>")
@login_required
def debug_expediente(nro_expediente):
    usuario = session.get("username")
    try:
        expedientes = db_manager.obtener_expedientes(usuario, origen="PRIVADO")
        exp = next((e for e in expedientes if e["expediente"] == nro_expediente), None)

        if not exp:
            return f"Expediente '{nro_expediente}' no encontrado en la base de datos para el usuario '{usuario}'."

        movs = db_manager.obtener_movimientos(exp["id"])

        html = "<div style='font-family: sans-serif; padding: 20px;'>"
        html += f"<h2>Diagnóstico de Expediente: {nro_expediente}</h2>"
        html += f"<p><strong>Total de movimientos registrados en la BD:</strong> {len(movs)}</p>"
        html += "<h3>Últimos 15 movimientos:</h3>"
        html += "<table border='1' cellpadding='8' style='border-collapse: collapse; text-align: left;'>"
        html += "<tr style='background-color: #f2f2f2;'><th>Fecha</th><th>Tiene Link PDF</th><th>Nombre del Escrito</th><th>Estado</th></tr>"

        for m in movs[-15:]:
            tiene_link = "SÍ" if m.get("link_escrito") else "NO"
            color = "green" if tiene_link == "SÍ" else "red"
            html += f"<tr><td>{m.get('fecha_presentacion', '')}</td><td style='color: {color}; font-weight: bold;'>{tiene_link}</td><td>{m.get('nombre_escrito', '')}</td><td>{m.get('estado', '')}</td></tr>"

        html += "</table></div>"
        return html

    except Exception as e:
        return f"Error al consultar la base de datos: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

