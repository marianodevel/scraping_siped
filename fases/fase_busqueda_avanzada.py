"""Módulo para la ejecución de consultas con filtros avanzados en el sistema."""

import os
from typing import Any, Dict
from celery.utils.log import get_task_logger

import db_manager
import scraper_tasks
import session_manager
import utils

logger = get_task_logger(__name__)


def ejecutar_fase_busqueda_avanzada(
    cookies: dict, username: str, filtros: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Realiza una búsqueda de expedientes utilizando parámetros específicos definidos por el usuario.

    Args:
        cookies: Diccionario con las cookies de sesión activa.
        username: Identificador del usuario actual.
        filtros: Diccionario con los parámetros de búsqueda a aplicar.

    Returns:
        Diccionario con el estado de la operación, total de resultados y archivo de volcado.
    """
    logger.info("--- Iniciando Búsqueda Avanzada para el usuario: %s ---", username)
    session = session_manager.crear_sesion_con_cookies(cookies)

    try:
        expedientes_filtrados = scraper_tasks.raspar_busqueda_parametrizada(
            session, filtros
        )
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = utils.generar_nombre_busqueda_avanzada(filtros)

        if expedientes_filtrados:
            utils.guardar_a_csv(
                expedientes_filtrados, nombre_archivo, subdirectory=ruta_usuario
            )

            db_manager.upsert_expedientes(
                username, expedientes_filtrados, origen="BUSQUEDA_AVANZADA"
            )

            logger.info(
                "Búsqueda avanzada guardada como '%s'. Total: %d",
                nombre_archivo,
                len(expedientes_filtrados),
            )
            return {
                "status": "success",
                "count": len(expedientes_filtrados),
                "file": nombre_archivo,
            }

        logger.warning("La búsqueda no arrojó resultados con esos parámetros.")
        return {"status": "empty", "count": 0}

    except Exception as e:
        logger.error("Error de ejecución en Búsqueda Avanzada: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}

