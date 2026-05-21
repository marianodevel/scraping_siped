"""Módulo para la descarga y consolidación de documentos de un expediente público."""

import os
import time
import requests
from celery.utils.log import get_task_logger

import config
import db_manager
import parsers
import scraper_tasks
import utils
from utils import manejar_fase_con_sesion

logger = get_task_logger(__name__)


@manejar_fase_con_sesion("FASE DESCARGA PUBLICA")
def ejecutar_fase_descarga_publica(
    session: requests.Session, link_detalle_objetivo: str, username: str
) -> str:
    """
    Ejecuta la extracción y consolidación en PDF de un expediente público específico.

    Args:
        session: Sesión HTTP activa.
        link_detalle_objetivo: URL exacta del detalle del expediente.
        username: Identificador del usuario actual.

    Returns:
        Cadena de texto informando el estado y la cantidad de descargas realizadas.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    expedientes = db_manager.obtener_expedientes(username, origen="BUSQUEDA_AVANZADA")
    expediente_data = next(
        (e for e in expedientes if e.get("link_detalle") == link_detalle_objetivo), None
    )

    if not expediente_data:
        return "Error: El expediente no se encontró en la base de datos."

    nro_expediente = expediente_data.get("expediente", "SIN_NRO")
    nro = utils.limpiar_nombre_archivo(nro_expediente)
    caratula = utils.limpiar_nombre_archivo(
        expediente_data.get("caratula", "SIN_CARATULA")
    )
    nombre_base = f"PUBLICO_{nro} - {caratula}"

    logger.info("Iniciando proceso para expediente público: %s", nombre_base)

    r_detalle = session.get(link_detalle_objetivo)
    html_detalle = r_detalle.text

    if '<frame name="sup"' in html_detalle.lower():
        movimientos = scraper_tasks.raspar_movimientos_de_expediente(
            session, expediente_data
        )
    else:
        ajax_params_base = parsers.parsear_detalle_para_ajax_params(html_detalle)
        if "exp_id" not in ajax_params_base:
            logger.error(
                "No se pudieron extraer los params de AJAX para %s.", nro_expediente
            )
            movimientos = []
        else:
            offset = 0
            mov_page_count = 1
            movimientos = []

            while True:
                ajax_params = ajax_params_base.copy()
                ajax_params.update(
                    {
                        "numerodemas": mov_page_count,
                        "offset": offset,
                        "usuariointerno": 0,
                        "tipof": "",
                        "estadose": "",
                        "descripcorta": "",
                        "contenido": "",
                        "pe": "",
                        "acumulados": "",
                    }
                )

                r_movs = session.get(config.AJAX_MOVIMIENTOS_URL, params=ajax_params)
                if len(r_movs.text) < 200:
                    break

                movs_pagina = parsers.parsear_movimientos_de_ajax_html(
                    r_movs.text, nro_expediente
                )
                if not movs_pagina:
                    break

                movimientos.extend(movs_pagina)
                offset += 10
                mov_page_count += 1
                time.sleep(0.25)

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    if movimientos:
        utils.guardar_a_csv(
            movimientos, f"{nombre_base}.csv", subdirectory=dir_movimientos
        )
        db_manager.upsert_movimientos(expediente_data.get("id"), movimientos)
    else:
        movimientos = db_manager.obtener_movimientos(expediente_data.get("id"))

    if not movimientos:
        return f"Finalizado sin datos: No hay movimientos para {nombre_base}."

    ruta_carpeta_expediente = os.path.join(dir_docs, nombre_base)
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    contador_documentos = 0
    total_descargados = 0

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
                                "nombre": f"{id_correlativo}_adj_{idx + 1}_{nombre_adj}.pdf",
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
                logger.error("Error procesando doc %s: %s", id_correlativo, e)

    nombre_pdf_final = f"{nombre_base} (Consolidado).pdf"
    ruta_pdf_final = os.path.join(dir_docs, nombre_pdf_final)

    if os.path.exists(ruta_pdf_final):
        os.remove(ruta_pdf_final)

    utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)
    return f"Proceso completado para {nombre_base}. Descargas: {total_descargados}."

