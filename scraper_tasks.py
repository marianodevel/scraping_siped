"""Módulo central para la orquestación de tareas de web scraping del sistema."""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

import config
import parsers
from logger import get_logger

logger = get_logger(__name__)


def descargar_archivo(session: requests.Session, url: str, ruta_destino: str) -> bool:
    """
    Ejecuta la descarga de un archivo remoto hacia el almacenamiento local.

    Args:
        session: Sesión HTTP activa.
        url: Dirección remota del archivo.
        ruta_destino: Ruta absoluta donde se escribirá el archivo localmente.

    Returns:
        bool: True si el archivo se guardó correctamente, False en caso de error.
    """
    url = url.strip()
    try:
        with session.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(ruta_destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except requests.RequestException as e:
        logger.error("Error descargando archivo desde %s: %s", url, e)
        return False


def raspar_lista_expedientes(session: requests.Session) -> List[Dict[str, str]]:
    """
    Itera a lo largo de la paginación privada extrayendo el registro de expedientes.

    Args:
        session: Sesión HTTP activa y autenticada.

    Returns:
        Lista completa de expedientes procesados.
    """
    all_expedientes_list = []
    current_inicio = 0
    page_count = 1

    while True:
        logger.info(
            "Obteniendo página de lista %d (inicio=%d)...", page_count, current_inicio
        )
        params = {"inicio": current_inicio}

        try:
            r_lista = session.get(
                config.LISTA_EXPEDIENTES_URL, params=params, timeout=30
            )
            r_lista.raise_for_status()

            expedientes_en_pagina = parsers.parsear_lista_expedientes(r_lista.text)
            if not expedientes_en_pagina:
                logger.info("No se encontraron más expedientes.")
                break

            all_expedientes_list.extend(expedientes_en_pagina)
            logger.info("Se encontraron %d expedientes.", len(expedientes_en_pagina))

            next_inicio = parsers.encontrar_siguiente_pagina_inicio(r_lista.text)
            if next_inicio is not None:
                current_inicio = next_inicio
                page_count += 1
            else:
                break

        except requests.RequestException as e:
            logger.error("Error al obtener la página %d: %s", page_count, e)
            break

    logger.info(
        "Fin de la paginación de expedientes. Total: %d", len(all_expedientes_list)
    )
    return all_expedientes_list


def raspar_movimientos_de_expediente(
    session: requests.Session, expediente_dict: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Reconstruye el historial de movimientos de un expediente específico.

    Args:
        session: Sesión HTTP activa.
        expediente_dict: Diccionario contenedor con metadatos del expediente.

    Returns:
        Lista de movimientos documentados o lista vacía en caso de no encontrarlos.
    """
    link_contenedor = expediente_dict.get("link_detalle")
    expediente_nro = expediente_dict.get("expediente", "Desconocido")

    if not link_contenedor:
        logger.warning(
            "No se encontró 'link_detalle' para el expediente %s.", expediente_nro
        )
        return []

    try:
        r_frameset = session.get(link_contenedor, timeout=30)
        r_frameset.raise_for_status()
        soup_frameset = BeautifulSoup(r_frameset.text, "html.parser")

        frame_sup = soup_frameset.find("frame", attrs={"name": "sup"})
        if not (frame_sup and frame_sup.get("src")):
            logger.error(
                "No se pudo encontrar el marco superior en %s.", expediente_nro
            )
            return []

        url_contenido_real = urljoin(link_contenedor, frame_sup.get("src"))
        r_detalle_real = session.get(url_contenido_real, timeout=30)
        r_detalle_real.raise_for_status()

        ajax_params_base = parsers.parsear_detalle_para_ajax_params(r_detalle_real.text)
        if "exp_id" not in ajax_params_base:
            logger.error(
                "No se pudieron extraer los parámetros AJAX base para %s.",
                expediente_nro,
            )
            return []

        offset = 0
        mov_page_count = 1
        movimientos_del_expediente = []

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

            r_movimientos = session.get(
                config.AJAX_MOVIMIENTOS_URL, params=ajax_params, timeout=30
            )
            movimientos_html = r_movimientos.text

            if len(movimientos_html) < 200:
                break

            movimientos_de_pagina = parsers.parsear_movimientos_de_ajax_html(
                movimientos_html, expediente_nro
            )
            if not movimientos_de_pagina:
                break

            movimientos_del_expediente.extend(movimientos_de_pagina)
            offset += 10
            mov_page_count += 1
            time.sleep(0.25)

        return movimientos_del_expediente

    except requests.RequestException as e:
        logger.error("Error de red procesando expediente %s: %s", expediente_nro, e)
        return []


def raspar_contenido_documento(
    session: requests.Session, document_url: str
) -> Optional[Dict[str, Any]]:
    """
    Procesa la vista documental para extraer rutas de descarga finales.

    Args:
        session: Sesión HTTP activa.
        document_url: URL que contiene la vista previa del documento.

    Returns:
        Diccionario con las URLs normalizadas de los documentos o None en caso de fallo.
    """
    if not document_url or not document_url.strip():
        logger.warning("No se proporcionó URL válida para el documento.")
        return None

    try:
        r_documento = session.get(document_url, timeout=30)
        r_documento.raise_for_status()
        return parsers.parsear_pagina_documento(r_documento.text)
    except requests.RequestException as e:
        logger.error(
            "Error al obtener el contenido documental en %s: %s", document_url, e
        )
        return None


def raspar_busqueda_parametrizada(
    session: requests.Session, filtros_usuario: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Lleva a cabo consultas masivas enviando parámetros definidos en los diccionarios de la fase de búsqueda pública.

    Args:
        session: Sesión HTTP activa.
        filtros_usuario: Criterios seleccionados para la consulta remota.

    Returns:
        Lista de expedientes resultantes del mapeo de los filtros procesados.
    """
    url_submit = f"{config.BASE_URL}/siped/expediente/buscar/submit.php"

    payload = {
        "id_localidad": filtros_usuario.get("id_localidad", "18"),
        "id_dependencia": filtros_usuario.get("id_dependencia", ""),
        "nro_expediente": filtros_usuario.get("nro_expediente", ""),
        "anio": filtros_usuario.get("anio", ""),
        "cmb_documental": filtros_usuario.get("cmb_documental", ""),
        "filtro_archivados": filtros_usuario.get("filtro_archivados", "todos"),
        "juicio": filtros_usuario.get("juicio", ""),
        "texto": filtros_usuario.get("texto", ""),
        "organismo_origen": filtros_usuario.get("organismo_origen", "2"),
        "id_abogado": filtros_usuario.get("id_abogado", ""),
        "txt_abogado": filtros_usuario.get("txt_abogado", ""),
        "abogado": filtros_usuario.get("abogado", ""),
        "dnij": filtros_usuario.get("dnij", ""),
        "apellidoj": filtros_usuario.get("apellidoj", ""),
        "nombresj": filtros_usuario.get("nombresj", ""),
        "fecha_alta_dia_desde": filtros_usuario.get("fecha_alta_dia_desde", "0"),
        "fecha_alta_mes_desde": filtros_usuario.get("fecha_alta_mes_desde", ""),
        "fecha_alta_anio_desde": filtros_usuario.get("fecha_alta_anio_desde", ""),
        "date": "",
        "fecha_alta_dia_hasta": filtros_usuario.get("fecha_alta_dia_hasta", "0"),
        "fecha_alta_mes_hasta": filtros_usuario.get("fecha_alta_mes_hasta", ""),
        "fecha_alta_anio_hasta": filtros_usuario.get("fecha_alta_anio_hasta", ""),
        "ordenar_por": "exp_numero",
        "orden": "ASC",
        "inicio": 0,
    }

    all_expedientes = []
    page_count = 1
    vistos = set()

    while True:
        logger.info(
            "Obteniendo página de búsqueda avanzada %d (inicio=%s)...",
            page_count,
            payload["inicio"],
        )
        try:
            respuesta = session.get(url_submit, params=payload, timeout=30)
            respuesta.raise_for_status()

            expedientes_pagina = parsers.parsear_lista_publica(respuesta.text)

            if not expedientes_pagina:
                logger.info("No se encontraron más registros para esta búsqueda.")
                break

            ids_actuales = [
                e.get("expediente") for e in expedientes_pagina if e.get("expediente")
            ]
            if vistos.intersection(ids_actuales):
                logger.warning(
                    "Ciclo de paginación detectado. Abortando extracción para prevenir bucle."
                )
                break

            vistos.update(ids_actuales)
            all_expedientes.extend(expedientes_pagina)
            logger.info(
                "Se extrajeron %d expedientes en esta etapa.", len(expedientes_pagina)
            )

            next_inicio = parsers.encontrar_siguiente_inicio_universal(respuesta.text)
            if next_inicio is not None and next_inicio > payload["inicio"]:
                payload["inicio"] = next_inicio
                page_count += 1
                time.sleep(0.5)
            else:
                break

        except requests.RequestException as e:
            logger.error("Error de comunicación en la búsqueda avanzada: %s", e)
            break

    logger.info(
        "Búsqueda avanzada finalizada. Total registros recabados: %d",
        len(all_expedientes),
    )
    return all_expedientes

