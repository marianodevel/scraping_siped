# gestor_tareas.py
from tasks import fase_1_lista_task
from celery.result import AsyncResult

# Almacenaremos el ID de la última tarea encolada para cada fase.
# AGREGAMOS 'fase_unico'
ULTIMOS_IDS_TAREAS = {
    "fase_1": None,
    "fase_2": None,
    "fase_3": None,
    "fase_unico": None,
}


def obtener_estado_tarea(id_tarea, nombre_fase):
    """
    Consulta el estado de una tarea Celery y limpia el ID si la tarea ha finalizado.
    """
    global ULTIMOS_IDS_TAREAS

    if not id_tarea:
        return {"estado": "IDLE", "resultado": "En espera"}

    # Se consulta el estado usando la aplicación Celery registrada en tasks.py
    tarea = AsyncResult(id_tarea, app=fase_1_lista_task.app)

    datos_estado = {"estado": tarea.state, "resultado": str(tarea.result)}

    # LÓGICA DE LIMPIEZA
    if tarea.state in ["SUCCESS", "FAILURE", "REVOKED"]:
        try:
            tarea.forget()
        except Exception:
            pass

        ULTIMOS_IDS_TAREAS[nombre_fase] = None
        datos_estado["recargar"] = True

        if tarea.state == "SUCCESS" and (
            not datos_estado["resultado"] or datos_estado["resultado"] == "None"
        ):
            datos_estado["resultado"] = "Completado"

        return datos_estado

    if tarea.state == "PENDING" and (
        not datos_estado["resultado"] or datos_estado["resultado"] == "None"
    ):
        datos_estado["resultado"] = "En cola..."

    if tarea.state == "STARTED" and (
        not datos_estado["resultado"] or datos_estado["resultado"] == "None"
    ):
        datos_estado["resultado"] = "Procesando..."

    return datos_estado


def registrar_tarea_iniciada(nombre_fase, tarea_objeto):
    """
    Guarda el ID de la tarea recién iniciada en el gestor global.
    """
    global ULTIMOS_IDS_TAREAS
    ULTIMOS_IDS_TAREAS[nombre_fase] = tarea_objeto.id


def obtener_id_tarea(nombre_fase):
    """
    Devuelve el ID de la última tarea iniciada.
    """
    return ULTIMOS_IDS_TAREAS.get(nombre_fase)


def resetear_id_tarea(nombre_fase):
    """
    Fuerza el ID de la tarea a None (usado en la ruta /resetear_estado).
    """
    global ULTIMOS_IDS_TAREAS
    ULTIMOS_IDS_TAREAS[nombre_fase] = None
