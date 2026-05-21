"""Módulo para la sincronización y descarga de un expediente privado individual."""

import os
import time
import requests
from celery.utils.log import get_task_logger

import config
import db_manager
import scraper_tasks
import utils
from utils import manejar_fase_con_sesion

logger = get_task_logger(__name__)


@manejar_fase_con_sesion("FASE ÚNICA: PROCESAR UN EXPEDIENTE")
def ejecutar_fase_unico(
    session: requests.Session, nro_expediente_objetivo: str, username: str
) -> str:
    """
    Ejecuta el ciclo completo (movimientos, descargas y consolidación) para un solo expediente.

    Args:
        session: Sesión HTTP activa.
        nro_expediente_objetivo: Número exacto del expediente a procesar.
        username: Identificador del usuario actual.

    Returns:
        Cadena de texto con las métricas finales de la operación.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    expedientes = db_manager.obtener_expedientes(username, origen="PRIVADO")
    expediente_data = next(
        (e for e in expedientes if e.get("expediente") == nro_expediente_objetivo), None
    )

    if not expediente_data:
        return f"Error: El expediente '{nro_expediente_objetivo}' no se encontró en la base de datos."

    nro = utils.limpiar_nombre_archivo(expediente_data.get("expediente", "SIN_NRO"))
    caratula = utils.limpiar_nombre_archivo(
        expediente_data.get("caratula", "SIN_CARATULA")
    )
    nombre_base = f"{nro} - {caratula}"

    logger.info("Iniciando proceso para: %s", nombre_base)
    logger.info("  > Buscando movimientos nuevos...")

    movimientos_nuevos = scraper_tasks.raspar_movimientos_de_expediente(
        session, expediente_data
    )

    if movimientos_nuevos:
        logger.info(
            "  > Insertando %d movimientos en la base de datos.",
            len(movimientos_nuevos),
        )
        db_manager.upsert_movimientos(expediente_data.get("id"), movimientos_nuevos)

    movimientos_completos = db_manager.obtener_movimientos(expediente_data.get("id"))
    if not movimientos_completos:
        return f"Finalizado sin datos: No hay movimientos en el historial para {nro_expediente_objetivo}."

    movimientos_completos = list(reversed(movimientos_completos))

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    nombre_csv = f"{nombre_base}.csv"
    utils.guardar_a_csv(movimientos_completos, nombre_csv, subdirectory=dir_movimientos)

    logger.info("  > Gestionando descargas de PDF...")
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)
    ruta_carpeta_expediente = os.path.join(dir_docs, nombre_base)
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    for filename in os.listdir(ruta_carpeta_expediente):
        if filename.endswith(".pdf") and not filename.startswith("doc_"):
            os.remove(os.path.join(ruta_carpeta_expediente, filename))

    contador_documentos = 0
    total_descargados = 0

    for movimiento in movimientos_completos:
        url_doc = movimiento.get("link_escrito")
        if url_doc and url_doc.strip():
            contador_documentos += 1
            id_correlativo = f"doc_{str(contador_documentos).zfill(3)}"

            try:
                datos_documento = scraper_tasks.raspar_contenido_documento(
                    session, url_doc
                )
                if datos_documento:
                    pdfs = []
                    url_principal = datos_documento.get("url_pdf_principal")
                    if url_principal:
                        pdfs.append(
                            {
                                "url": url_principal,
                                "nombre": f"{id_correlativo}_principal.pdf",
                            }
                        )

                    for idx, adj in enumerate(datos_documento.get("adjuntos", [])):
                        nombre_adj = (
                            utils.limpiar_nombre_archivo(adj.get("nombre", ""))
                            .lower()
                            .replace(".pdf", "")
                            .replace(".", "")
                        )
                        pdfs.append(
                            {
                                "url": adj.get("url"),
                                "nombre": f"{id_correlativo}_adjunto_{idx + 1}_{nombre_adj}.pdf",
                            }
                        )

                    for p in pdfs:
                        ruta_pdf = os.path.join(ruta_carpeta_expediente, p["nombre"])
                        if not os.path.exists(ruta_pdf):
                            if scraper_tasks.descargar_archivo(
                                session, p["url"], ruta_pdf
                            ):
                                total_descargados += 1
                                time.sleep(0.2)

            except Exception as e:
                logger.error("    > Error procesando doc %s: %s", id_correlativo, e)

    logger.info("  > Generando PDF consolidado...")
    nombre_pdf_final = f"{nombre_base} (Consolidado).pdf"
    ruta_pdf_final = os.path.join(dir_docs, nombre_pdf_final)

    if os.path.exists(ruta_pdf_final):
        os.remove(ruta_pdf_final)

    utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)

    return f"Proceso completado. Descargas nuevas: {total_descargados}. Total histórico: {len(movimientos_completos)} movimientos."

