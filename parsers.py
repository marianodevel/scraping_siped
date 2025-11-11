# parsers.py
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import config


def get_meta_refresh_url(html_text, base_path):
    """Extrae la URL de una etiqueta meta refresh."""
    soup = BeautifulSoup(html_text, "html.parser")
    meta_tag = soup.find(
        "meta", attrs={"http-equiv": re.compile(r"refresh", re.IGNORECASE)}
    )
    if meta_tag:
        content = meta_tag.get("content", "")
        match = re.search(r"url=(.*)", content, re.IGNORECASE)
        if match:
            url = match.group(1).strip().replace("'", "").replace('"', "")
            if url.startswith("/"):
                return f"{config.BASE_URL}{url}"
            if not url.startswith("http"):
                return f"{base_path}/{url}"
            return url
    return None


def get_siped_token_link(html_text):
    """Extrae el enlace <a> que contiene el token de SIPED."""
    soup = BeautifulSoup(html_text, "html.parser")
    siped_link = soup.find("a", href=re.compile(r"/siped\?token="))
    if siped_link:
        url = siped_link.get("href")
        if url.startswith("/"):
            return f"{config.BASE_URL}{url}"
        if not url.startswith("http"):
            return f"{config.BASE_URL}/{url}"
        return url
    return None


def parse_expediente_list_page(html_text):
    """Parsea la tabla de expedientes y devuelve una lista de dicts."""
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table", class_="table-striped")
    if not table:
        return []
    expedientes_en_pagina = []

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) == 8:
            link_tag = cols[0].find("a")
            link_detalle = None
            if link_tag and link_tag.get("href"):
                relative_url = link_tag.get("href")
                # Unimos la URL base de la lista con la URL relativa del link
                link_detalle = urljoin(config.LISTA_EXPEDIENTES_URL, relative_url)

            exp_data = {
                "expediente": cols[0].text.strip(),
                "link_detalle": link_detalle,
                "caratula": cols[1].text.strip(),
                "partes": cols[2].text.strip(),
                "estado": cols[3].text.strip(),
                "fec_ult_mov": cols[4].text.strip(),
                "localidad": cols[5].text.strip(),
                "dependencia": cols[6].text.strip(),
                "secretaria": cols[7].text.strip(),
            }
            expedientes_en_pagina.append(exp_data)
    return expedientes_en_pagina


def find_next_list_page_inicio(html_text):
    """Encuentra el valor 'inicio' del botón SIGUIENTE."""
    soup = BeautifulSoup(html_text, "html.parser")

    def is_real_next_button(tag):
        if tag.name != "button":
            return False
        if "SIGUIENTE" not in tag.get_text(strip=True):
            return False
        onclick_attr = tag.get("onclick", "")
        if not re.search(r"document\.form\.inicio\.value=(\d+)", str(onclick_attr)):
            return False
        return True

    next_button = soup.find(is_real_next_button)
    if next_button:
        onclick_attr = next_button.get("onclick", "")
        match = re.search(r"document\.form\.inicio\.value=(\d+)", onclick_attr)
        if match:
            return int(match.group(1))
    return None


def parse_detail_page_for_ajax_params(html_detalle):
    """Extrae los parámetros dinámicos para la llamada AJAX 'vermas'."""
    params = {}
    soup = BeautifulSoup(html_detalle, "html.parser")

    input_id = soup.find("input", {"name": "id"})
    if input_id:
        params["exp_id"] = input_id.get("value")
        params["id_cd"] = input_id.get("value")

    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "ver_mas_escritosAjax.php" in script.string:
            match_dep_id = re.search(r"dependencia_ide=(\d+)", script.string)
            if match_dep_id:
                params["dependencia_ide"] = match_dep_id.group(1)

            match_tj_fuero = re.search(r"tj_fuero=(\d+)", script.string)
            if match_tj_fuero:
                params["tj_fuero"] = match_tj_fuero.group(1)

            match_org_origen = re.search(r"exp_organismo_origen=(\d+)", script.string)
            if match_org_origen:
                params["exp_organismo_origen"] = match_org_origen.group(1)

            if all(
                k in params
                for k in ["dependencia_ide", "tj_fuero", "exp_organismo_origen"]
            ):
                break
    return params


def parse_movimientos_from_ajax_html(html_movimientos, nro_expediente):
    """Parsea la tabla de movimientos devuelta por AJAX."""
    soup = BeautifulSoup(html_movimientos, "html.parser")
    table = soup.find("table", class_="table-hover")
    if not table:
        return []
    movimientos_list = []

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 9:
            form_tag = cols[1].find("form")
            link_escrito = None
            if form_tag and form_tag.get("action"):
                # Construimos la URL absoluta del link del escrito
                link_escrito = urljoin(
                    config.AJAX_MOVIMIENTOS_URL, form_tag.get("action")
                )

            mov_data = {
                "expediente_nro": nro_expediente,
                "nombre_escrito": cols[1].text.strip(),
                "link_escrito": link_escrito,
                "fecha_presentacion": cols[2].text.strip(),
                "tipo": cols[3].text.strip(),
                "estado": cols[4].text.strip(),
                "generado_por": cols[5].text.strip(),
                "descripcion": cols[6].find("font").get("title", "").strip(),
                "fecha_firma": cols[7].text.strip(),
                "fecha_publicacion": cols[8].text.strip(),
            }
            movimientos_list.append(mov_data)
    return movimientos_list


# --- ¡NUEVA FUNCIÓN AÑADIDA! ---
def parse_document_page(html_text):
    """
    Extrae todos los datos estructurados de la página de un escrito.
    Devuelve un diccionario.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    data = {"firmantes": []}

    try:
        # --- 1. Extraer datos del Expediente (Primera tabla) ---
        # Buscamos la tabla que contiene el escudo de Santa Cruz
        table_expediente = soup.find("img", {"src": re.compile(r"SCescudo\.png")})
        if table_expediente:
            table_expediente = table_expediente.find_parent("table")

        if table_expediente:
            rows = table_expediente.find_all("tr")
            if len(rows) > 5:
                # Expediente: 18559/2024 (en rows[1])
                exp_tag = rows[1].find("strong", class_="Estilo1")
                if exp_tag:
                    data["expediente_nro"] = (
                        exp_tag.get_text(strip=True).replace("Expediente:", "").strip()
                    )

                # Dependencia (en rows[2])
                dep_tag = rows[2].find("strong")
                if dep_tag:
                    data["dependencia"] = dep_tag.get_text(strip=True)

                # Secretaría (en rows[3])
                sec_tag = rows[3].find("strong")
                if sec_tag:
                    data["secretaria"] = sec_tag.get_text(strip=True)

                # Carátula (en rows[5])
                car_tag = rows[5].find("strong")
                if car_tag:
                    data["caratula"] = (
                        car_tag.get_text(strip=True).replace("Cáratula:", "").strip()
                    )

        # --- 2. Extraer datos del Escrito (Segunda tabla) ---
        # Buscamos la tabla que contiene el "Código de Validación"
        table_documento = soup.find(
            "strong", string=re.compile(r"Código de Validación:")
        )
        if table_documento:
            table_documento = table_documento.find_parent("table")

        if table_documento:
            rows = table_documento.find_all("tr")
            if len(rows) > 1:
                cols = rows[1].find_all("td")
                if len(cols) > 0:
                    # Nombre: PE1239398-2025
                    data["nombre_escrito"] = (
                        cols[0].get_text(strip=True).replace("Nombre:", "").strip()
                    )

                # Código de Validación: 2u5vts
                cod_tag = rows[1].find("strong")
                if cod_tag:
                    data["codigo_validacion"] = (
                        cod_tag.get_text(strip=True)
                        .replace("Código de Validación:", "")
                        .strip()
                    )

        # --- 3. Extraer Texto de la Providencia (div#editor-container) ---
        editor = soup.find(id="editor-container")
        if editor:
            text = editor.get_text(separator="\n", strip=True)
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            data["texto_providencia"] = "\n".join(clean_lines)
        else:
            data["texto_providencia"] = (
                "ERROR: No se pudo encontrar el contenedor de texto."
            )

        # --- 4. Extraer Firmantes (Última tabla) ---
        table_firmantes = soup.find(
            "strong", string=re.compile(r"Firmado electrónicamente por")
        )
        if table_firmantes:
            table_firmantes = table_firmantes.find_parent("table")

        if table_firmantes:
            # Empezar a buscar desde la fila de títulos (Cargo, Apellido, Fecha)
            header_row = table_firmantes.find("td", string=re.compile(r"Cargo"))
            if header_row:
                # Iterar sobre las filas hermanas que vienen *después* de la cabecera
                for row in header_row.find_parent("tr").find_next_siblings("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 3:
                        cargo = cols[0].get_text(strip=True)
                        nombre = cols[1].get_text(strip=True)
                        fecha = cols[2].get_text(strip=True)
                        if cargo and nombre:  # Asegurarse de que no sea una fila vacía
                            data["firmantes"].append(
                                {"cargo": cargo, "nombre": nombre, "fecha": fecha}
                            )

    except Exception as e:
        print(f"   > !!! Error parseando HTML del documento: {e}")
        data["texto_providencia"] = f"ERROR AL PARSEAR HTML: {e}"

    return data
