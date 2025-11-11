# scraper_tasks.py
import time
from urllib.parse import urljoin
import parsers
import config
from bs4 import BeautifulSoup


def scrape_lista_expedientes(session):
    """
    Recorre todas las páginas de la lista de expedientes y devuelve una
    lista completa de todos los expedientes encontrados.
    """
    all_expedientes_list = []
    current_inicio = 0
    page_count = 1

    while True:
        print(f"Obteniendo página de lista {page_count} (inicio={current_inicio})...")
        params = {"inicio": current_inicio}
        try:
            r_lista = session.get(config.LISTA_EXPEDIENTES_URL, params=params)
            r_lista.raise_for_status()

            expedientes_en_pagina = parsers.parse_expediente_list_page(r_lista.text)
            if not expedientes_en_pagina:
                print("  > No se encontraron más expedientes.")
                break

            all_expedientes_list.extend(expedientes_en_pagina)
            print(f"  > Se encontraron {len(expedientes_en_pagina)} expedientes.")

            next_inicio = parsers.find_next_list_page_inicio(r_lista.text)
            if next_inicio is not None:
                current_inicio = next_inicio
                page_count += 1
            else:
                break  # Fin de la paginación

        except Exception as e:
            print(f"Error al obtener la página {page_count}: {e}")
            break  # Detener el bucle si una página falla

    print(f"\nFin de la paginación de expedientes. Total: {len(all_expedientes_list)}")
    return all_expedientes_list


def scrape_movimientos_de_expediente(session, expediente_dict):
    """
    Obtiene todos los movimientos para UN solo expediente.
    """
    link_contenedor = expediente_dict.get("link_detalle")
    expediente_nro = expediente_dict.get("expediente")

    if not link_contenedor:
        print(f"  > ADVERTENCIA: No se encontró 'link_detalle' para {expediente_nro}.")
        return []

    # 1. Visitar el contenedor de frames
    r_frameset = session.get(link_contenedor)
    soup_frameset = BeautifulSoup(r_frameset.text, "html.parser")

    # 2. Encontrar el frame 'sup'
    frame_sup = soup_frameset.find("frame", attrs={"name": "sup"})
    if not (frame_sup and frame_sup.get("src")):
        print(
            f"  > ERROR: No se pudo encontrar el <frame name='sup'> en {expediente_nro}."
        )
        return []

    # 3. Visitar la URL del contenido real
    url_contenido_relativa = frame_sup.get("src")
    url_contenido_real = urljoin(link_contenedor, url_contenido_relativa)
    r_detalle_real = session.get(url_contenido_real)
    html_detalle = r_detalle_real.text

    # 4. Extraer los parámetros para la llamada AJAX
    ajax_params_base = parsers.parse_detail_page_for_ajax_params(html_detalle)
    if "exp_id" not in ajax_params_base:
        print(
            f"  > ERROR: No se pudieron extraer los params de AJAX para {expediente_nro}."
        )
        return []

    # 5. Bucle de paginación de MOVIMIENTOS
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

        # El HTML vacío (o casi vacío) indica el fin
        if len(movimientos_html) < 200:
            break

        movimientos_de_pagina = parsers.parse_movimientos_from_ajax_html(
            movimientos_html, expediente_nro
        )

        if not movimientos_de_pagina:
            break  # No se pudo parsear, fin

        movimientos_del_expediente.extend(movimientos_de_pagina)
        offset += 10  # Asumimos paginación de 10
        mov_page_count += 1
        time.sleep(0.25)  # Pausa cortés para no saturar el servidor

    return movimientos_del_expediente


def scrape_document_content(session, document_url):
    """
    Visita la URL de un escrito (documento/movimiento) y
    extrae todos sus datos estructurados usando el parser.
    Devuelve un diccionario.
    """
    if not document_url or not document_url.strip():
        print("   > ADVERTENCIA: No se proporcionó URL para el documento.")
        return None

    try:
        # La URL ya viene absoluta desde el parser de movimientos
        r_documento = session.get(document_url)
        r_documento.raise_for_status()

        # Usar el nuevo parser de página de documento
        document_data = parsers.parse_document_page(r_documento.text)
        return document_data

    except Exception as e:
        print(
            f"   > ERROR al obtener el contenido del documento en {document_url}: {e}"
        )
        return None
