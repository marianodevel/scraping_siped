from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
)
import os
import config

# Importamos las *tareas* de Celery
from tasks import phase_1_list_task, phase_2_movements_task, phase_3_documents_task
from celery.result import AsyncResult  # Importación necesaria para consultar el estado

# --- Configuración de Flask ---
app = Flask(__name__)
# Usamos una clave secreta para la seguridad de los mensajes flash
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "desarrollo-secreto-cambiar-en-prod"
)

# Almacenaremos el ID de la última tarea encolada para cada fase.
LAST_TASK_IDS = {"phase_1": None, "phase_2": None, "phase_3": None}

# --- Funciones Auxiliares ---


def get_task_status(task_id, phase_name):
    """
    Consulta el estado de una tarea Celery y limpia el ID si la tarea ha finalizado.
    """
    global LAST_TASK_IDS

    if not task_id:
        # Tarea IDLE: nunca iniciada o reseteada.
        return {"state": "SUCCESS", "result": "IDLE"}

    # Usamos AsyncResult para consultar el estado del ID
    task = AsyncResult(task_id, app=phase_1_list_task.app)

    status_data = {"state": task.state, "result": task.result}

    # LÓGICA DE LIMPIEZA: Si el estado es final, limpiamos el ID global
    if task.state in ["SUCCESS", "FAILURE", "REVOKED"]:
        # Limpiamos el ID global de esta fase
        LAST_TASK_IDS[phase_name] = None

        # Devolvemos el estado final de la tarea
        return status_data

    return status_data


# --- Rutas de la Aplicación (Endpoints) ---


@app.route("/")
def index():
    """
    Ruta principal. Muestra la página de inicio con la lista de PDFs generados.
    """
    pdf_list = []
    output_dir = config.DOCUMENTOS_OUTPUT_DIR

    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            if item.endswith(".pdf"):
                pdf_list.append(item)

    # Obtener el estado actual de las tareas para la interfaz
    task_statuses = {
        "phase_1": get_task_status(LAST_TASK_IDS["phase_1"], "phase_1"),
        "phase_2": get_task_status(LAST_TASK_IDS["phase_2"], "phase_2"),
        "phase_3": get_task_status(LAST_TASK_IDS["phase_3"], "phase_3"),
    }

    return render_template(
        "index.html", pdf_files=sorted(pdf_list), task_statuses=task_statuses
    )


@app.route("/start/<phase>", methods=["POST"])
def start_phase(phase):
    """
    Ruta genérica para iniciar cualquier fase.
    """
    global LAST_TASK_IDS

    task_map = {
        "phase_1": phase_1_list_task,
        "phase_2": phase_2_movements_task,
        "phase_3": phase_3_documents_task,
    }

    if phase not in task_map:
        flash(f"Fase '{phase}' no reconocida.", "error")
        return redirect(url_for("index"))

    # Verificar si ya hay una tarea en curso
    current_status = get_task_status(LAST_TASK_IDS.get(phase), phase)
    if current_status["state"] in ["PENDING", "STARTED", "RETRY"]:
        flash(
            f"La Fase {phase.split('_')[1]} ya está en curso (Estado: {current_status['state']}).",
            "warning",
        )
        return redirect(url_for("index"))

    # Encolar la tarea
    task = task_map[phase].delay()
    LAST_TASK_IDS[phase] = task.id

    flash(f"Fase {phase.split('_')[1]} iniciada con ID: {task.id}", "success")

    return redirect(url_for("index"))


@app.route("/reset-task-status/<phase>")
def reset_task(phase):
    """
    Ruta de utilidad para resetear manualmente el ID de la última tarea.
    """
    global LAST_TASK_IDS
    if phase in LAST_TASK_IDS:
        LAST_TASK_IDS[phase] = None
        flash(f"Estado de {phase} reseteado manualmente.", "info")
    else:
        flash("Fase no válida para resetear.", "error")

    return redirect(url_for("index"))


@app.route("/task-status/<phase>")
def check_task_status(phase):
    """
    Endpoint para que el frontend pueda consultar el estado de una tarea.
    """
    status = get_task_status(LAST_TASK_IDS.get(phase), phase)
    # Si la tarea está finalizada (SUCCESS/FAILURE), recargamos la página para
    # actualizar la lista de PDFs y el estado del botón.
    if status["state"] in ["SUCCESS", "FAILURE", "REVOKED"]:
        # También devolvemos la URL de recarga para que JavaScript lo maneje
        status["refresh"] = True

    return jsonify(status)


# --- NUEVA RUTA PARA DESCARGA DE ARCHIVOS ---
@app.route("/download/<filename>")
def download_file(filename):
    """
    Ruta para servir archivos PDF de forma segura.
    """
    return send_from_directory(
        directory=config.DOCUMENTOS_OUTPUT_DIR,
        path=filename,
        as_attachment=True,  # Fuerza la descarga en lugar de mostrarlo en el navegador
    )


# --- FIN NUEVA RUTA ---

# --- Bloque de Ejecución ---

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
