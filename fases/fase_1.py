"""Módulo correspondiente a la Fase 1: Extracción de lista de expedientes privados."""

import os
import requests
from celery.utils.log import get_task_logger

import config
import db_manager
import scraper_tasks
import utils
from utils import manejar_fase_con_sesion

logger = get_task_logger(__name__)


@manejar_fase_con_sesion("FASE 1: OBTENER LISTA DE EXPEDIENTES")
def ejecutar_fase_1_lista(session: requests.Session, username: str) -> str:
    """
    Ejecuta la descarga y almacenamiento de la lista principal de expedientes.

    Args:
        session: Sesión HTTP activa.
        username: Identificador del usuario actual.

    Returns:
        Cadena de texto con el resultado de la operación.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    lista_expedientes = scraper_tasks.raspar_lista_expedientes(session)

    if lista_expedientes:
        utils.guardar_a_csv(
            lista_expedientes, config.LISTA_EXPEDIENTES_CSV, subdirectory=ruta_usuario
        )

        db_manager.upsert_expedientes(username, lista_expedientes, origen="PRIVADO")

        ruta_completa = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)
        return f"Lista de expedientes guardada en DB y en '{ruta_completa}'. Total: {len(lista_expedientes)}"

    return "No se encontraron expedientes."

