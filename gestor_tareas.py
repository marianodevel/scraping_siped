# gestor_tareas.py
from tasks import fase_1_lista_task
from celery.result import AsyncResult

ULTIMOS_IDS_TAREAS = {
    "fase_1": None,
    "fase_2": None,
    "fase_3": None,
    "fase_unico": None,
    "fase_publica": None,
    "fase_busqueda_avanzada": None,
}

def obtener_estado_tarea(id_tarea, nombre_fase):
    global ULTIMOS_IDS_TAREAS
    if not id_tarea:
        return {"estado": "IDLE", "resultado": "En espera"}
    
    tarea = AsyncResult(id_tarea, app=fase_1_lista_task.app)
    datos_estado = {"estado": tarea.state, "resultado": str(tarea.result)}
    
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
    global ULTIMOS_IDS_TAREAS
    ULTIMOS_IDS_TAREAS[nombre_fase] = tarea_objeto.id

def obtener_id_tarea(nombre_fase):
    return ULTIMOS_IDS_TAREAS.get(nombre_fase)

def resetear_id_tarea(nombre_fase):
    global ULTIMOS_IDS_TAREAS
    ULTIMOS_IDS_TAREAS[nombre_fase] = None