import time
from urllib.parse import urljoin
import parsers
import config
from bs4 import BeautifulSoup
from logger import get_logger

logger = get_logger(__name__)

def descargar_archivo(session, url, ruta_destino):
    url = url.strip()
    try:
        with session.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(ruta_destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error descargando archivo desde {url}: {e}")
        return False

def raspar_lista_expedientes(session):
    all_expedientes_list = []
    current_inicio = 0
    page_count = 1
    while True:
        logger.info(f"Obteniendo página de lista {page_count} (inicio={current_inicio})...")
        params = {"inicio": current_inicio}
        try:
            r_lista = session.get(config.LISTA_EXPEDIENTES_URL, params=params)
            r_lista.raise_for_status()
            expedientes_en_pagina = parsers.parsear_lista_expedientes(r_lista.text)
            if not expedientes_en_pagina:
                logger.info("No se encontraron más expedientes.")
                break
            all_expedientes_list.extend(expedientes_en_pagina)
            logger.info(f"Se encontraron {len(expedientes_en_pagina)} expedientes.")
            next_inicio = parsers.encontrar_siguiente_pagina_inicio(r_lista.text)
            if next_inicio is not None:
                current_inicio = next_inicio
                page_count += 1
            else:
                break
        except Exception as e:
            logger.error(f"Error al obtener la página {page_count}: {e}")
            break
    logger.info(f"Fin de la paginación de expedientes. Total: {len(all_expedientes_list)}")
    return all_expedientes_list

def raspar_movimientos_de_expediente(session, expediente_dict):
    link_contenedor = expediente_dict.get("link_detalle")
    expediente_nro = expediente_dict.get("expediente")
    if not link_contenedor:
        logger.warning(f"No se encontró 'link_detalle' para {expediente_nro}.")
        return []
    r_frameset = session.get(link_contenedor)
    soup_frameset = BeautifulSoup(r_frameset.text, "html.parser")
    frame_sup = soup_frameset.find("frame", attrs={"name": "sup"})
    if not (frame_sup and frame_sup.get("src")):
        logger.error(f"No se pudo encontrar el <frame name='sup'> en {expediente_nro}.")
        return []
    url_contenido_relativa = frame_sup.get("src")
    url_contenido_real = urljoin(link_contenedor, url_contenido_relativa)
    r_detalle_real = session.get(url_contenido_real)
    html_detalle = r_detalle_real.text
    ajax_params_base = parsers.parsear_detalle_para_ajax_params(html_detalle)
    if "exp_id" not in ajax_params_base:
        logger.error(f"No se pudieron extraer los params de AJAX para {expediente_nro}.")
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
        r_movimientos = session.get(config.AJAX_MOVIMIENTOS_URL, params=ajax_params)
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

def raspar_contenido_documento(session, document_url):
    if not document_url or not document_url.strip():
        logger.warning("No se proporcionó URL para el documento.")
        return None
    try:
        r_documento = session.get(document_url)
        r_documento.raise_for_status()
        document_data = parsers.parsear_pagina_documento(r_documento.text)
        return document_data
    except Exception as e:
        logger.error(f"Error al obtener el contenido del documento en {document_url}: {e}")
        return None

def raspar_busqueda_parametrizada(session, filtros_usuario):
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
        "inicio": 0
    }
    all_expedientes = []
    page_count = 1
    vistos = set()
    while True:
        logger.info(f"Obteniendo página de búsqueda avanzada {page_count} (inicio={payload['inicio']})...")
        try:
            respuesta = session.get(url_submit, params=payload, timeout=30)
            respuesta.raise_for_status()
            html = respuesta.text
            expedientes_pagina = parsers.parsear_lista_publica(html)
            
            if not expedientes_pagina:
                logger.info("No se encontraron más registros para esta búsqueda.")
                break
                
            ids_actuales = [e.get("expediente") for e in expedientes_pagina if e.get("expediente")]
            if vistos.intersection(ids_actuales):
                logger.warning("Bucle detectado. Fin de la extracción.")
                break
                
            vistos.update(ids_actuales)
            all_expedientes.extend(expedientes_pagina)
            logger.info(f"Se extrajeron {len(expedientes_pagina)} expedientes.")
            
            next_inicio = parsers.encontrar_siguiente_inicio_universal(html)
            if next_inicio is not None and next_inicio > payload["inicio"]:
                payload["inicio"] = next_inicio
                page_count += 1
                time.sleep(0.5)
            else:
                break
        except Exception as e:
            logger.error(f"Error fatal en la búsqueda avanzada: {e}")
            break
    logger.info(f"Búsqueda avanzada finalizada. Total: {len(all_expedientes)}")
    return all_expedientes