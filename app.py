from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
    request,
)
import os
import config
from tasks import fase_1_lista_task, fase_2_movimientos_task, fase_3_documentos_task
import gestor_tareas
import gestor_almacenamiento
from celery.result import AsyncResult  # Se mantiene la importación para AsyncResult

# --- Configuración de Flask ---
app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod"
)

# Almacenaremos el ID de la última tarea encolada para cada fase.
ULTIMOS_IDS_TAREAS = {"fase_1": None, "fase_2": None, "fase_3": None}

# --- Funciones Auxiliares ---


def obtener_estado_tarea(id_tarea, nombre_fase):
    """
    Consulta el estado de una tarea Celery y limpia el ID si la tarea ha finalizado.
    """
    global ULTIMOS_IDS_TAREAS

    if not id_tarea:
        return {"estado": "SUCCESS", "resultado": "IDLE"}

    tarea = AsyncResult(id_tarea, app=fase_1_lista_task.app)

    datos_estado = {"estado": tarea.state, "resultado": str(tarea.result)}

    # LÓGICA DE LIMPIEZA: Si el estado es final, limpiamos el ID global
    if tarea.state in ["SUCCESS", "FAILURE", "REVOKED"]:
        ULTIMOS_IDS_TAREAS[nombre_fase] = None
        datos_estado["recargar"] = True  # Indicador de recarga para el frontend
        return datos_estado

    return datos_estado


# --- Rutas de la Aplicación (Endpoints) ---


@app.route("/fragmento/mensajes")
def fragmento_mensajes():
    """Devuelve el fragmento HTML de los mensajes flash."""
    return render_template("_fragmento_mensajes.html")


@app.route("/")
def indice():
    """
    Ruta principal. Muestra la página de inicio.
    """
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()

    estados_tareas = {
        "fase_1": obtener_estado_tarea(ULTIMOS_IDS_TAREAS["fase_1"], "fase_1"),
        "fase_2": obtener_estado_tarea(ULTIMOS_IDS_TAREAS["fase_2"], "fase_2"),
        "fase_3": obtener_estado_tarea(ULTIMOS_IDS_TAREAS["fase_3"], "fase_3"),
    }

    return render_template(
        "index.html",
        archivos_pdf=lista_pdf,
        estados_tareas=estados_tareas,
        credenciales_establecidas=True,
    )


@app.route("/iniciar/<nombre_fase>", methods=["POST"])
def iniciar_fase(nombre_fase):
    """
    Ruta genérica para iniciar cualquier fase.
    NOTA: Eliminamos el redirect y devolvemos el fragmento de mensaje.
    """
    global ULTIMOS_IDS_TAREAS

    mapa_tareas = {
        "fase_1": fase_1_lista_task,
        "fase_2": fase_2_movimientos_task,
        "fase_3": fase_3_documentos_task,
    }

    if nombre_fase not in mapa_tareas:
        flash(f"Fase '{nombre_fase}' no reconocida.", "error")
        return render_template("_fragmento_mensajes.html"), 400

    estado_actual = obtener_estado_tarea(
        ULTIMOS_IDS_TAREAS.get(nombre_fase), nombre_fase
    )
    if estado_actual["estado"] in ["PENDING", "STARTED", "RETRY"]:
        flash(
            f"La Fase {nombre_fase.split('_')[1]} ya está en curso (Estado: {estado_actual['estado']}).",
            "warning",
        )
        return render_template("_fragmento_mensajes.html"), 200

    # Encolar la tarea
    tarea = mapa_tareas[nombre_fase].delay()
    ULTIMOS_IDS_TAREAS[nombre_fase] = tarea.id

    flash(f"Fase {nombre_fase.split('_')[1]} iniciada con ID: {tarea.id}", "success")

    # IMPORTANTE: Devolvemos el fragmento y un código 200. No hay redirección.
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/resetear_estado/<nombre_fase>")
def resetear_estado(nombre_fase):
    """
    Ruta de utilidad para resetear manualmente el ID de la última tarea.
    NOTA: Eliminamos el redirect y devolvemos el fragmento de mensaje.
    """
    if nombre_fase in gestor_tareas.ULTIMOS_IDS_TAREAS:
        gestor_tareas.resetear_id_tarea(nombre_fase)
        flash(f"Estado de {nombre_fase} reseteado manualmente.", "info")
    else:
        flash("Fase no válida para resetear.", "error")

    # Devolvemos el fragmento para la actualización asíncrona
    return render_template("_fragmento_mensajes.html"), 200


@app.route("/fragmento/estado/<nombre_fase>")
def fragmento_estado(nombre_fase):
    """
    Devuelve el fragmento HTML del estado y resultado de una fase específica.
    """
    estado = gestor_tareas.obtener_estado_tarea(
        gestor_tareas.obtener_id_tarea(nombre_fase), nombre_fase
    )

    return render_template("_fragmento_estado.html", id_fase=nombre_fase, estado=estado)


@app.route("/fragmento/pdfs")
def fragmento_pdfs():
    """
    Devuelve el fragmento HTML de la lista de PDFs.
    """
    lista_pdf = gestor_almacenamiento.listar_archivos_pdf()

    return render_template("_fragmento_pdfs.html", archivos_pdf=lista_pdf)


@app.route("/estado_tarea/<nombre_fase>")
def verificar_estado_tarea(nombre_fase):
    """
    Endpoint para que el frontend pueda consultar el estado de una tarea (JSON).
    """
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
