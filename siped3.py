import requests
import os
import re
import csv
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- Configuración ---
load_dotenv()
BASE_URL = "https://intranet.jussantacruz.gob.ar"
LOGIN_PORTAL_URL = f"{BASE_URL}/servicios/controli2.php"
LISTA_URL = f"{BASE_URL}/siped/expediente/buscar/submit_buscar_abogado.php"
AJAX_URL = f"{BASE_URL}/siped/expediente/buscar/ver_mas_escritosAjax.php"

credenciales = {
    "usuario": os.getenv("USUARIO_INTRANET"),
    "pass": os.getenv("CLAVE_INTRANET"),
}

browser_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange=vb3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}


# ---
# --- ¡¡¡NUEVA FUNCIÓN!!! ---
# ---
def sanitize_filename(name):
    """
    Limpia un string para que sea un nombre de archivo válido.
    """
    if not name:
        name = "SIN_NOMBRE"
    # Reemplazar '/' por '-' (común en números de expediente)
    name = name.replace("/", "-")
    # Eliminar otros caracteres ilegales
    name = re.sub(r'[\\*?:"<>|]', "", name)
    # Truncar para evitar nombres de archivo demasiado largos
    return name[:150].strip()


# ---
# --- ¡¡¡FUNCIÓN MODIFICADA!!! ---
# ---
def save_to_csv(data, filename):
    """
    Guarda una lista de diccionarios en un archivo CSV dentro de un subdirectorio.
    """
    output_dir = "movimientos_expedientes"

    if not data:
        print(f"  > No hay datos para guardar en {filename}.")
        return

    try:
        # Crear el directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        print(f"  > Guardando {len(data)} filas en {filepath}...")

        headers = data[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

    except Exception as e:
        print(f"  > Error al guardar CSV: {e}")


# --- Funciones Helper (Navegación) ---
# (Idénticas a v10)
def get_meta_refresh_url(html_text, base_path):
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
                return f"{BASE_URL}{url}"
            if not url.startswith("http"):
                return f"{base_path}/{url}"
            return url
    return None


def get_siped_token_link(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    siped_link = soup.find("a", href=re.compile(r"/siped\?token="))
    if siped_link:
        url = siped_link.get("href")
        if url.startswith("/"):
            return f"{BASE_URL}{url}"
        if not url.startswith("http"):
            return f"{BASE_URL}/{url}"
        return url
    return None


# --- Funciones Helper (Scraping Lista) ---
# (Idénticas a v10)
def parse_expedientes_from_html(html_text, page_url):
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
                link_detalle = urljoin(page_url, relative_url)
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


def find_next_page_inicio(html_text):
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


# --- Funciones Helper (Scraping Detalle) ---
# (Idénticas a v10)
def get_ajax_params_from_detail(html_detalle):
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


def parse_movimientos_from_ajax(html_movimientos, nro_expediente):
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
                link_escrito = form_tag.get("action")
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


# --- Inicio del Scraper ---
def main():
    print(f"Iniciando scraper...")
    if not credenciales.get("usuario") or not credenciales.get("pass"):
        print("--- ¡ERROR DE CONFIGURACIÓN! ---")
        exit()

    try:
        with requests.Session() as s:
            s.headers.update(browser_headers)

            # --- FASES 1-4: LOGIN Y NAVEGACIÓN ---
            print(f"Usando usuario: {credenciales.get('usuario')}")
            r_login = s.post(LOGIN_PORTAL_URL, data=credenciales)
            r_login.raise_for_status()
            print("Login POST enviado.")

            url_inicio = get_meta_refresh_url(r_login.text, f"{BASE_URL}/servicios")
            if not url_inicio:
                exit("Error: no se pudo encontrar url_inicio")
            print(f"Siguiendo redirección a (Página de Menú)...")
            r_menu = s.get(url_inicio)
            r_menu.raise_for_status()

            url_token = get_siped_token_link(r_menu.text)
            if not url_token:
                exit("Error: no se pudo encontrar url_token")
            print(f"Enlace al token encontrado, siguiendo...")
            r_token_page = s.get(url_token)
            r_token_page.raise_for_status()

            url_dashboard = get_meta_refresh_url(r_token_page.text, f"{BASE_URL}/siped")
            if not url_dashboard:
                exit("Error: no se pudo encontrar url_dashboard")
            print(f"Siguiendo redirección al Dashboard...")
            r_dashboard = s.get(url_dashboard)
            r_dashboard.raise_for_status()
            print("¡Éxito! Aterrizado en el Dashboard (frame_principal).")

            # --- FASE 5: BUCLE DE PAGINACIÓN (LISTA DE EXPEDIENTES) ---
            print("\n--- Iniciando Fase 5: Paginación de Lista de Expedientes ---")
            all_expedientes_list = []
            current_inicio = 0
            page_count = 1

            while True:
                print(
                    f"Obteniendo página de lista {page_count} (inicio={current_inicio})..."
                )
                params = {"inicio": current_inicio}
                r_lista = s.get(LISTA_URL, params=params)
                r_lista.raise_for_status()
                expedientes_en_esta_pagina = parse_expedientes_from_html(
                    r_lista.text, LISTA_URL
                )
                if expedientes_en_esta_pagina:
                    all_expedientes_list.extend(expedientes_en_esta_pagina)
                    print(
                        f"  > Se encontraron {len(expedientes_en_esta_pagina)} expedientes."
                    )
                else:
                    print("  > No se encontraron expedientes en esta página.")
                next_inicio = find_next_page_inicio(r_lista.text)
                if next_inicio is not None:
                    current_inicio = next_inicio
                    page_count += 1
                else:
                    print(
                        "\nNo se encontró el botón 'SIGUIENTE'. Fin de la paginación de expedientes."
                    )
                    break

            # --- FASE 6: GUARDAR CSV (LISTA) ---
            print("\n--- Paginación Completada ---")
            print(f"Total de expedientes extraídos: {len(all_expedientes_list)}")

            if all_expedientes_list:
                # Sigue guardando el CSV maestro
                save_to_csv(all_expedientes_list, "expedientes_completos.csv")

                # ---
                # --- ¡¡¡FASE 7 MODIFICADA!!! ---
                # ---
                print(
                    "\n--- Iniciando Fase 7: Extracción de Movimientos (Archivos Individuales) ---"
                )

                # Bucle por cada expediente encontrado
                for i, expediente in enumerate(all_expedientes_list):
                    print(
                        f"\nProcesando Expediente {i + 1}/{len(all_expedientes_list)}: {expediente['expediente']}"
                    )

                    try:
                        # 1. Obtener todos los movimientos para ESTE expediente
                        movements = get_expediente_movimientos(s, expediente)

                        if movements:
                            print(f"  > Se encontraron {len(movements)} movimientos.")

                            # 2. Crear nombre de archivo dinámico y sanitizado
                            nro = sanitize_filename(expediente.get("expediente"))
                            caratula = sanitize_filename(expediente.get("caratula"))
                            filename = f"{nro} - {caratula}.csv"

                            # 3. Guardar en su propio CSV
                            save_to_csv(movements, filename)

                        else:
                            print(
                                f"  > No se encontraron movimientos para este expediente."
                            )

                    except Exception as e:
                        print(
                            f"  > ERROR Inesperado al procesar {expediente['expediente']}: {e}"
                        )
                        # Continuar con el siguiente expediente

            else:
                print("No se extrajo ningún expediente.")

            print("\n--- SCRIPT COMPLETADO ---")

    except requests.exceptions.RequestException as e:
        print(f"\nError fatal de conexión (HTTP): {e}")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback

        traceback.print_exc()


def get_expediente_movimientos(session, expediente_dict):
    """
    Función 'trabajadora' que contiene toda la lógica para
    obtener los movimientos de UN solo expediente.
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
    ajax_params_base = get_ajax_params_from_detail(html_detalle)  # <-- Usa el parser
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

        r_movimientos = session.get(AJAX_URL, params=ajax_params)
        movimientos_html = r_movimientos.text

        if len(movimientos_html) < 200:
            break  # No hay más movimientos

        movimientos_de_pagina = parse_movimientos_from_ajax(
            movimientos_html, expediente_nro
        )

        if not movimientos_de_pagina:
            break

        movimientos_del_expediente.extend(movimientos_de_pagina)
        offset += 10  # Asumimos paginación de 10
        mov_page_count += 1
        time.sleep(0.25)  # Pausa cortés

    return movimientos_del_expediente


# --- Punto de entrada ---
if __name__ == "__main__":
    main()
