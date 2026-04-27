# scraping_siped/parsers.py
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import config

# ... (mantener funciones anteriores: obtener_url_meta_refresh, etc.) ...

def encontrar_siguiente_inicio_universal(html_text):
    """
    Busca el valor de 'inicio' para la siguiente pagina. 
    Funciona tanto para la Fase 1 (form.inicio) como para la Fase Publica (window.location).
    """
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Buscamos cualquier etiqueta que contenga el texto SIGUIENTE
    # SIPED usa <button> o <a> dependiendo del contexto
    for element in soup.find_all(['button', 'a', 'input']):
        texto = element.get_text(strip=True).upper()
        valor = str(element.get('value', '')).upper()
        
        if 'SIGUIENTE' in texto or 'SIGUIENTE' in valor:
            # Extraemos el atributo que contiene la logica de salto (onclick o href)
            contenido_logico = str(element.get('onclick', '')) + str(element.get('href', ''))
            
            # Buscamos el patron numerico despues de 'inicio=' o 'value='
            match = re.search(r"inicio[=\s'\"]+(\d+)", contenido_logico, re.IGNORECASE)
            if not match:
                match = re.search(r"value[=\s'\"]+(\d+)", contenido_logico, re.IGNORECASE)
            
            if match:
                return int(match.group(1))
                
    return None

def parsear_lista_publica(html_content):
    """
    Extrae los expedientes de la tabla de resultados publicos.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    # SIPED usa la misma clase CSS tanto en la parte privada como en la publica
    tabla = soup.find('table', class_='table-striped')
    expedientes = []

    if not tabla:
        return expedientes

    filas = tabla.find_all('tr')
    for fila in filas:
        columnas = fila.find_all(['td', 'th'])
        if not columnas or columnas[0].name == 'th':
            continue

        if len(columnas) >= 7:
            btn_link = columnas[0].find('button', onclick=True)
            exp_id = None
            link_detalle = None
            
            numero_exp = columnas[0].get_text(strip=True)

            if btn_link:
                match = re.search(r"id=(\d+)", btn_link['onclick'])
                if match:
                    exp_id = match.group(1)
                    link_detalle = f"../expediente/expediente/buscar/DetalleExpediente.php?id={exp_id}"

            expedientes.append({
                "exp_id": exp_id,
                "expediente": numero_exp,
                "caratula": columnas[1].get_text(strip=True),
                "partes_count": columnas[2].get_text(strip=True),
                "fecha_alta": columnas[3].get_text(strip=True),
                "localidad": columnas[4].get_text(strip=True),
                "dependencia": columnas[5].get_text(strip=True),
                "secretaria": columnas[6].get_text(strip=True),
                "link_detalle": urljoin(config.LISTA_EXPEDIENTES_URL, link_detalle) if link_detalle else None
            })
    return expedientes