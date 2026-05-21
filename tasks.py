"""Módulo de definición de tareas asíncronas para Celery."""

import os
from typing import Any, Dict
from celery import Celery

from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos
from fases.fase_unico import ejecutar_fase_unico
from fases.fase_publica_1 import ejecutar_fase_publica
from fases.fase_busqueda_avanzada import ejecutar_fase_busqueda_avanzada
from fases.fase_descarga_publica import ejecutar_fase_descarga_publica

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task(name="tasks.fase_1_lista_task", bind=True)
def fase_1_lista_task(self, cookies: dict, username: str) -> str:
    """Ejecuta la extracción asíncrona de la bandeja privada."""
    return ejecutar_fase_1_lista(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_2_movimientos_task", bind=True)
def fase_2_movimientos_task(self, cookies: dict, username: str) -> str:
    """Ejecuta la sincronización asíncrona de movimientos de la bandeja privada."""
    return ejecutar_fase_2_movimientos(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_3_documentos_task", bind=True)
def fase_3_documentos_task(self, cookies: dict, username: str) -> str:
    """Ejecuta la descarga y consolidación masiva de documentos en segundo plano."""
    return ejecutar_fase_3_documentos(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_unico_task", bind=True)
def fase_unico_task(self, cookies: dict, nro_expediente: str, username: str) -> str:
    """Ejecuta la actualización integral de un único expediente privado."""
    return ejecutar_fase_unico(
        cookies=cookies, nro_expediente_objetivo=nro_expediente, username=username
    )


@celery_app.task(name="tasks.fase_publica_task", bind=True)
def fase_publica_task(self, cookies: dict, username: str) -> Dict[str, Any]:
    """Ejecuta la extracción masiva del directorio público por localidades."""
    return ejecutar_fase_publica(cookies=cookies, username=username)


@celery_app.task(name="tasks.fase_busqueda_avanzada_task", bind=True)
def fase_busqueda_avanzada_task(
    self, cookies: dict, username: str, filtros: Dict[str, Any]
) -> Dict[str, Any]:
    """Ejecuta una búsqueda filtrada en el directorio público."""
    return ejecutar_fase_busqueda_avanzada(
        cookies=cookies, username=username, filtros=filtros
    )


@celery_app.task(name="tasks.fase_descarga_publica_task", bind=True)
def fase_descarga_publica_task(
    self, cookies: dict, link_detalle: str, username: str
) -> str:
    """Ejecuta la descarga y consolidación de un expediente público específico."""
    return ejecutar_fase_descarga_publica(
        cookies=cookies, link_detalle_objetivo=link_detalle, username=username
    )

