"""Módulo para la extracción masiva de expedientes de acceso público."""

import os
from typing import Any, Dict
from celery.utils.log import get_task_logger

import db_manager
import scraper_tasks
import session_manager
import utils
from catalogos.localidades import LOCALIDADES

logger = get_task_logger(__name__)


def ejecutar_fase_publica(cookies: dict, username: str) -> Dict[str, Any]:
    """
    Inicia la extracción estructurada de expedientes públicos iterando sobre el catálogo de localidades.

    Args:
        cookies: Diccionario con las cookies de sesión activa.
        username: Identificador del usuario actual.

    Returns:
        Diccionario con el estado de la operación, conteo de expedientes y archivo generado.
    """
    logger.info("--- Iniciando Fase Publica Masiva para el usuario: %s ---", username)
    session = session_manager.crear_sesion_con_cookies(cookies)

    try:
        expedientes_totales = []

        for id_loc, nombre_loc in LOCALIDADES.items():
            logger.info(
                "Extrayendo expedientes públicos de: %s (ID: %s)", nombre_loc, id_loc
            )

            filtros_loc = {"organismo_origen": "2", "id_localidad": str(id_loc)}

            expedientes_loc = scraper_tasks.raspar_busqueda_parametrizada(
                session, filtros_loc
            )

            if expedientes_loc:
                expedientes_totales.extend(expedientes_loc)
                logger.info(
                    "  > %d expedientes recuperados de %s.",
                    len(expedientes_loc),
                    nombre_loc,
                )
            else:
                logger.info("  > Sin resultados para %s.", nombre_loc)

        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = "expedientes_publicos.csv"

        if expedientes_totales:
            utils.guardar_a_csv(
                expedientes_totales, nombre_archivo, subdirectory=ruta_usuario
            )

            db_manager.upsert_expedientes(
                username, expedientes_totales, origen="PUBLICO"
            )

            logger.info(
                "Extracción publica finalizada. Total consolidado: %d",
                len(expedientes_totales),
            )
            return {
                "status": "success",
                "count": len(expedientes_totales),
                "file": nombre_archivo,
            }

        logger.warning("La extracción no devolvió resultados en ninguna localidad.")
        return {"status": "empty", "count": 0}

    except Exception as e:
        logger.error("Error de ejecución en Fase Publica: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}

