"""Módulo correspondiente a la Fase 2: Extracción y actualización de movimientos."""

import os
import requests
from celery.utils.log import get_task_logger

import config
import db_manager
import scraper_tasks
import utils
from utils import manejar_fase_con_sesion

logger = get_task_logger(__name__)


@manejar_fase_con_sesion("FASE 2: OBTENER MOVIMIENTOS")
def ejecutar_fase_2_movimientos(session: requests.Session, username: str) -> str:
    """
    Extrae y sincroniza el historial de movimientos para cada expediente registrado.

    Args:
        session: Sesión HTTP activa.
        username: Identificador del usuario actual.

    Returns:
        Cadena de texto con el resultado y estadísticas de la operación.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    expedientes_a_procesar = db_manager.obtener_expedientes(username, origen="PRIVADO")

    if not expedientes_a_procesar:
        mensaje = f"Error: No se encontraron expedientes en la base de datos para {username}. Ejecute Fase 1 primero."
        logger.error(mensaje)
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    logger.info("Se encontraron %d expedientes para procesar.", total_expedientes)

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    os.makedirs(dir_movimientos, exist_ok=True)
    contador_movimientos = 0

    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente.get("expediente", "Desconocido")
        logger.info("Procesando %d/%d: %s", i + 1, total_expedientes, nro_expediente)

        nro = utils.limpiar_nombre_archivo(nro_expediente)
        caratula_limpia = utils.limpiar_nombre_archivo(
            expediente.get("caratula", "Sin Caratula")
        )
        nombre_archivo = f"{nro} - {caratula_limpia}.csv"

        logger.info("  > Extrayendo/Actualizando historial de '%s'...", nombre_archivo)

        try:
            movimientos = scraper_tasks.raspar_movimientos_de_expediente(
                session, expediente
            )

            if movimientos:
                utils.guardar_a_csv(
                    movimientos,
                    nombre_archivo,
                    subdirectory=dir_movimientos,
                )

                db_manager.upsert_movimientos(expediente.get("id"), movimientos)

                cantidad = len(movimientos)
                contador_movimientos += cantidad
                logger.info("  > Guardados/Actualizados %d movimientos.", cantidad)
            else:
                logger.info("  > No se encontraron movimientos.")

        except Exception as e:
            logger.error(
                "  > !!! ERROR al procesar %s: %s", nro_expediente, e, exc_info=True
            )

    return f"Proceso de actualización de movimientos completado. Movimientos analizados: {contador_movimientos}"

