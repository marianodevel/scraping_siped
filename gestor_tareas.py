# gestor_tareas.py
from tasks import fase_1_lista_task
from celery.result import AsyncResult  # FIX: Importación de la clase AsyncResult

# Almacenaremos el ID de la última tarea encolada para cada fase.
ULTIMOS_IDS_TAREAS = {"fase_1": None, "fase_2": None, "fase_3": None}


def obtener_estado_tarea(id_tarea, nombre_fase):
    """
    Consulta el estado de una tarea Celery y limpia el ID si la tarea ha finalizado.
    """
    global ULTIMOS_IDS_TAREAS

    if not id_tarea:
        # --- INICIO DE LA CORRECCIÓN ---
        # El estado inicial debe ser IDLE (o un sinónimo),
        # y el resultado debe ser descriptivo.
        return {"estado": "IDLE", "resultado": "En espera"}
        # --- FIN DE LA CORRECCIÓN ---

    # Se consulta el estado usando la aplicación Celery registrada en tasks.py
    tarea = AsyncResult(id_tarea, app=fase_1_lista_task.app)

    # Convertimos el resultado a string para evitar errores de serialización JSON
    datos_estado = {"estado": tarea.state, "resultado": str(tarea.result)}

    # LÓGICA DE LIMPIEZA
    if tarea.state in ["SUCCESS", "FAILURE", "REVOKED"]:
        # Se limpia el resultado de Redis para ahorrar memoria
        try:
            tarea.forget()
        except Exception:
            pass  # No es un error crítico si no se puede olvidar.

        ULTIMOS_IDS_TAREAS[nombre_fase] = None
        datos_estado["recargar"] = True  # Indicador de recarga para el frontend

        # Si la tarea fue exitosa pero no devolvió resultado, mostramos "Completado"
        if tarea.state == "SUCCESS" and (
            not datos_estado["resultado"] or datos_estado["resultado"] == "None"
        ):
            datos_estado["resultado"] = "Completado"

        return datos_estado

    # Si la tarea está PENDING (encolada pero no iniciada), mostramos "En cola"
    if tarea.state == "PENDING" and (
        not datos_estado["resultado"] or datos_estado["resultado"] == "None"
    ):
        datos_estado["resultado"] = "En cola..."

    # Si la tarea está STARTED (corriendo), mostramos "Procesando"
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
