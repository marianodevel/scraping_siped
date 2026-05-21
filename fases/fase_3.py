"""Módulo correspondiente a la Fase 3: Extracción y consolidación masiva de documentos PDF."""

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


@manejar_fase_con_sesion("FASE 3: OBTENER DOCUMENTOS PDF Y CONSOLIDAR")
def ejecutar_fase_3_documentos(session: requests.Session, username: str) -> str:
    """
    Recorre los expedientes privados registrados, descarga sus documentos adjuntos
    y genera un PDF consolidado por expediente.

    Args:
        session: Sesión HTTP activa y autenticada.
        username: Identificador del usuario actual.

    Returns:
        Cadena de texto indicando la finalización del proceso masivo.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    expedientes_a_procesar = db_manager.obtener_expedientes(username, origen="PRIVADO")

    if not expedientes_a_procesar:
        mensaje = (
            "Error: No se encontraron expedientes en la BD. Ejecute Fase 1 primero."
        )
        logger.error(mensaje)
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    logger.info("Se encontraron %d expedientes para procesar.", total_expedientes)

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente.get("expediente", "SIN_NRO")
        caratula_exp = expediente.get("caratula", "SIN_CARATULA")

        logger.info(
            "--- Procesando Expediente %d/%d: %s ---",
            i + 1,
            total_expedientes,
            nro_expediente,
        )

        nro = utils.limpiar_nombre_archivo(nro_expediente)
        caratula = utils.limpiar_nombre_archivo(caratula_exp)
        nombre_carpeta_expediente = f"{nro} - {caratula}"
        ruta_carpeta_expediente = os.path.join(dir_docs, nombre_carpeta_expediente)
        os.makedirs(ruta_carpeta_expediente, exist_ok=True)

        movimientos = db_manager.obtener_movimientos(expediente.get("id"))

        if not movimientos:
            nombre_csv = f"{nro} - {caratula}.csv"
            ruta_csv = os.path.join(dir_movimientos, nombre_csv)
            if os.path.exists(ruta_csv):
                movimientos = utils.leer_csv_a_diccionario(ruta_csv)

        if not movimientos:
            logger.warning(
                "  > No se encontraron movimientos en BD ni CSV para %s. Ejecute Fase 2.",
                nro_expediente,
            )
            continue

        logger.info(
            "  > Iniciando procesamiento de %d movimientos...", len(movimientos)
        )
        contador_documentos = 0
        total_pdfs_descargados = 0

        for movimiento in movimientos:
            url_doc = movimiento.get("link_escrito")
            if url_doc and url_doc.strip():
                contador_documentos += 1
                id_correlativo = str(contador_documentos).zfill(2)

                try:
                    datos_documento = scraper_tasks.raspar_contenido_documento(
                        session, url_doc
                    )
                    if datos_documento:
                        pdfs_a_descargar = []
                        url_main = datos_documento.get("url_pdf_principal")

                        if url_main:
                            nombre_pdf_main = f"{id_correlativo}_principal.pdf"
                            pdfs_a_descargar.append(
                                {
                                    "url": url_main,
                                    "nombre": nombre_pdf_main,
                                    "tipo": "Principal",
                                }
                            )

                        adjuntos = datos_documento.get("adjuntos", [])
                        if adjuntos:
                            for idx, adj in enumerate(adjuntos):
                                url_adj = adj.get("url")
                                nombre_orig = utils.limpiar_nombre_archivo(
                                    adj.get("nombre", "")
                                )
                                nombre_base = nombre_orig.replace(".PDF", "").replace(
                                    ".pdf", ""
                                )
                                nombre_archivo_adj = f"{id_correlativo}_adjunto_{idx + 1}_{nombre_base}.pdf"
                                pdfs_a_descargar.append(
                                    {
                                        "url": url_adj,
                                        "nombre": nombre_archivo_adj,
                                        "tipo": f"Adjunto {idx + 1}",
                                    }
                                )

                        if pdfs_a_descargar:
                            logger.info(
                                "    > Doc %s: Encontrados %d PDFs.",
                                id_correlativo,
                                len(pdfs_a_descargar),
                            )
                            for pdf_info in pdfs_a_descargar:
                                ruta_pdf = os.path.join(
                                    ruta_carpeta_expediente, pdf_info["nombre"]
                                )
                                if not os.path.exists(ruta_pdf):
                                    logger.info(
                                        "      > Descargando %s: %s",
                                        pdf_info["tipo"],
                                        pdf_info["nombre"],
                                    )
                                    if scraper_tasks.descargar_archivo(
                                        session, pdf_info["url"], ruta_pdf
                                    ):
                                        total_pdfs_descargados += 1
                                else:
                                    logger.info(
                                        "      > %s ya existe, saltando: %s",
                                        pdf_info["tipo"],
                                        pdf_info["nombre"],
                                    )
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(
                        "    > !!! ERROR (Doc %s) en %s: %s",
                        id_correlativo,
                        nro_expediente,
                        e,
                        exc_info=True,
                    )

        logger.info(
            "  > Descarga finalizada para %s. (Nuevos: %d)",
            nro_expediente,
            total_pdfs_descargados,
        )

        nombre_pdf_final = f"{nombre_carpeta_expediente} (Consolidado).pdf"
        ruta_pdf_final = os.path.join(dir_docs, nombre_pdf_final)
        archivos_existentes_en_carpeta = [
            f for f in os.listdir(ruta_carpeta_expediente) if f.lower().endswith(".pdf")
        ]

        if os.path.exists(ruta_pdf_final):
            logger.info(
                "  > PDF Consolidado '%s' ya existe, saltando fusión.", nombre_pdf_final
            )
        elif archivos_existentes_en_carpeta:
            utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)
        else:
            logger.warning("  > No hay PDFs para consolidar en %s.", nro_expediente)

    return f"Proceso de descarga y consolidación de PDFs completado. Total de expedientes: {total_expedientes}."

