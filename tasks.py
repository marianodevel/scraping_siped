# tasks.py
import os
from celery import Celery
from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos
from fases.fase_unico import ejecutar_fase_unico

# --- Configuración de Celery ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Definición de las Tareas ---


@celery_app.task(name="tasks.fase_1_lista_task", bind=True)
def fase_1_lista_task(self, cookies, username):
    """
    Tarea de Celery para la Fase 1: Obtener lista maestra.
    """
    return ejecutar_fase_1_lista(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_2_movimientos_task", bind=True)
def fase_2_movimientos_task(self, cookies, username):
    """
    Tarea de Celery para la Fase 2: Descargar movimientos individuales (CSV).
    """
    return ejecutar_fase_2_movimientos(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_3_documentos_task", bind=True)
def fase_3_documentos_task(self, cookies, username):
    """
    Tarea de Celery para la Fase 3: Descargar documentos de texto y compilar PDFs.
    """
    return ejecutar_fase_3_documentos(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_unico_task", bind=True)
def fase_unico_task(self, cookies, nro_expediente, username):
    """
    Tarea de Celery para Procesar un Único Expediente.
    """
    return ejecutar_fase_unico(
        cookies=cookies, nro_expediente_objetivo=nro_expediente, username=username
    )
