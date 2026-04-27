import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import config

def obtener_url_meta_refresh(html_text, base_path):
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

def obtener_enlace_token_siped(html_text):
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

def parsear_lista_expedientes(html_text):
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

def encontrar_siguiente_pagina_inicio(html_text):
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

def parsear_detalle_para_ajax_params(html_detalle):
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

def parsear_movimientos_de_ajax_html(html_movimientos, nro_expediente):
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
                link_escrito = urljoin(
                    config.AJAX_MOVIMIENTOS_URL, form_tag.get("action")
                )

            font_tag = cols[6].find("font")
            descripcion = font_tag.get("title", "").strip() if font_tag else cols[6].get_text(strip=True)

            mov_data = {
                "expediente_nro": nro_expediente,
                "nombre_escrito": cols[1].text.strip(),
                "link_escrito": link_escrito,
                "fecha_presentacion": cols[2].text.strip(),
                "tipo": cols[3].text.strip(),
                "estado": cols[4].text.strip(),
                "generado_por": cols[5].text.strip(),
                "descripcion": descripcion,
                "fecha_firma": cols[7].text.strip(),
                "fecha_publicacion": cols[8].text.strip(),
            }
            movimientos_list.append(mov_data)
    return movimientos_list

def normalizar_url_pdf(url, tipo):
    if not url:
        return None

    url = url.strip()

    if not url.startswith("http"):
        url = urljoin(config.BASE_URL, url)

    parsed = urlparse(url)
    path = parsed.path

    if tipo == "principal" and "pdfabogado" in path:
        if "/siped/agrega_plantilla/" not in path:
            new_path = path.replace("/agrega_plantilla/", "/siped/agrega_plantilla/")

            if new_path == path:
                if path.startswith("/pdfabogado"):
                    new_path = "/siped/agrega_plantilla" + path
                elif "siped" not in path:
                    new_path = "/siped/agrega_plantilla/" + path.lstrip("/")

            url = urlunparse(parsed._replace(path=new_path))

    elif tipo == "adjunto" and "ver_adjunto_escrito.php" in path:
        if "/siped/expediente/buscar/" not in path:
            new_path = path
            if "/ver_adjunto_escrito.php" in path:
                if not path.startswith("/siped/"):
                    new_path = "/siped/expediente/buscar/ver_adjunto_escrito.php"

            url = urlunparse(parsed._replace(path=new_path))

    return url

def parsear_pagina_documento(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    data = {
        "firmantes": [],
        "url_pdf_principal": None,
        "adjuntos": [],
        "texto_providencia": "Se prioriza descarga de PDF.",
        "expediente_nro": None,
        "caratula": None,
    }

    try:
        titulo_div = soup.find("div", class_="titulo")
        if titulo_div:
            h2_expediente = titulo_div.find("h2")
            if h2_expediente:
                exp_nro = h2_expediente.get_text(strip=True)
                match = re.search(r"(\d{4,6}/\d{4})", exp_nro)
                data["expediente_nro"] = match.group(0) if match else exp_nro

        table_expediente = soup.find("img", {"src": re.compile(r"SCescudo\.png")})
        if table_expediente:
            table_expediente = table_expediente.find_parent("table")

        if table_expediente:
            rows = table_expediente.find_all("tr")
            if len(rows) > 5:
                if not data["expediente_nro"]:
                    exp_tag = rows[1].find("strong")
                    if exp_tag:
                        data["expediente_nro"] = (
                            exp_tag.get_text(strip=True)
                            .replace("Expediente:", "")
                            .strip()
                        )
                car_tag = rows[5].find("strong")
                if car_tag:
                    data["caratula"] = (
                        car_tag.get_text(strip=True).replace("Cáratula:", "").strip()
                    )

        btn_pdf = soup.find("a", href=re.compile(r"pdfabogado.*\.php"))
        if btn_pdf:
            href = btn_pdf.get("href")
            data["url_pdf_principal"] = normalizar_url_pdf(href, "principal")

        tds_adjuntos = soup.find_all("td", class_="alert-warning")
        seen_urls = set()

        for td in tds_adjuntos:
            link = td.find("a")
            if link and link.get("href"):
                href = link.get("href")
                if "ver_adjunto_escrito.php" in href:
                    full_url = normalizar_url_pdf(href, "adjunto")

                    if full_url and full_url not in seen_urls:
                        nombre_adjunto = link.get_text(strip=True)
                        data["adjuntos"].append(
                            {"nombre": nombre_adjunto, "url": full_url}
                        )
                        seen_urls.add(full_url)

        table_firmantes = soup.find(
            "strong", string=re.compile(r"Firmado electrónicamente por")
        )
        if table_firmantes:
            table_firmantes = table_firmantes.find_parent("table")

        if table_firmantes:
            header_row = table_firmantes.find("td", string=re.compile(r"Cargo"))
            if header_row:
                for row in header_row.find_parent("tr").find_next_siblings("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 3:
                        cargo = cols[0].get_text(strip=True)
                        nombre = cols[1].get_text(strip=True)
                        fecha = cols[2].get_text(strip=True)
                        if cargo and nombre:
                            data["firmantes"].append(
                                {"cargo": cargo, "nombre": nombre, "fecha": fecha}
                            )

    except Exception as e:
        print(f"   > !!! Error parseando HTML del documento: {e}")

    return data

def parsear_lista_publica(html_content):
    """
    Extrae los expedientes de la tabla de resultados públicos (7 columnas).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    tabla = soup.find('table', class_='table-striped')
    expedientes = []

    if not tabla:
        return expedientes

    filas = tabla.find('tbody').find_all('tr') if tabla.find('tbody') else tabla.find_all('tr')

    for fila in filas:
        columnas = fila.find_all(['td', 'th'])
        if not columnas or columnas[0].name == 'th':
            continue

        if len(columnas) >= 7:
            btn_link = columnas[0].find('button', onclick=True)
            exp_id = None
            link_detalle = None
            
            span_text = columnas[0].find('span')
            if span_text:
                 numero_exp = span_text.get_text(strip=True)
            else:
                 numero_exp = columnas[0].get_text(strip=True)

            if btn_link:
                match = re.search(r"id=(\d+)", btn_link['onclick'])
                if match:
                    exp_id = match.group(1)
                    link_detalle = f"../expediente/buscar/DetalleExpediente.php?id={exp_id}"

            caratula = columnas[1].get_text(strip=True)
            partes_count = columnas[2].get_text(strip=True)
            fecha_alta = columnas[3].get_text(strip=True)
            localidad = columnas[4].get_text(strip=True)
            dependencia = columnas[5].get_text(strip=True)
            secretaria = columnas[6].get_text(strip=True)

            expedientes.append({
                "exp_id": exp_id,
                "expediente": numero_exp,
                "caratula": caratula,
                "partes_count": partes_count,
                "fecha_alta": fecha_alta,
                "localidad": localidad,
                "dependencia": dependencia,
                "secretaria": secretaria,
                "link_detalle": urljoin(config.LISTA_EXPEDIENTES_URL, link_detalle) if link_detalle else None
            })

    return expedientes

def parsear_paginacion_publica(html_content):
    """
    Extrae el valor del parámetro 'inicio' del botón SIGUIENTE para el próximo GET.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    botones = soup.find_all('button', class_='botones_inicio_fin')
    for btn in botones:
        if 'SIGUIENTE' in btn.get_text():
            if btn.has_attr('onclick'):
                match = re.search(r"inicio=(\d+)", btn['onclick'])
                if match:
                    return int(match.group(1))
    return None