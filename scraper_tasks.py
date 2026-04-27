# scraping_siped/scraper_tasks.py
import time
from urllib.parse import urljoin
import parsers
import config

# ... (mantener funciones descargar_archivo, raspar_lista_expedientes, etc.) ...

def raspar_busqueda_publica_masiva(session, id_localidad="18"):
    """
    Extrae el listado masivo utilizando el mismo metodo de la Fase 1:
    Diccionario de parametros y busqueda dinamica del boton 'siguiente'.
    """
    url_publica = f"{config.BASE_URL}/siped/expediente/buscar/submit.php"
    
    # Parametros iniciales tal como los enviaria el formulario de la intranet
    params = {
        "id_localidad": id_localidad,
        "id_dependencia": "",
        "nro_expediente": "",
        "anio": "",
        "cmb_documental": "",
        "filtro_archivados": "todos",
        "juicio": "",
        "texto": "",
        "organismo_origen": "",
        "id_abogado": "",
        "txt_abogado": "",
        "abogado": "",
        "dnij": "",
        "apellidoj": "",
        "nombresj": "",
        "fecha_alta_dia_desde": "0",
        "fecha_alta_mes_desde": "",
        "fecha_alta_anio_desde": "",
        "fecha_alta_dia_hasta": "0",
        "fecha_alta_mes_hasta": "",
        "fecha_alta_anio_hasta": "",
        "ordenar_por": "exp_numero",
        "orden": "ASC",
        "inicio": 0
    }
    
    expedientes_totales = []
    page_count = 1
    vistos = set()

    while True:
        print(f"Obteniendo pagina publica {page_count} (inicio={params['inicio']})...")
        
        try:
            # Enviamos los parametros usando el metodo de la Fase 1
            response = session.get(url_publica, params=params, timeout=30)
            response.raise_for_status()
            
            html = response.text
            expedientes_pagina = parsers.parsear_lista_publica(html)
            
            if not expedientes_pagina:
                print("  > No se encontraron mas registros.")
                break

            # Verificacion de duplicados para evitar bucles infinitos
            ids_actuales = [e.get("expediente") for e in expedientes_pagina if e.get("expediente")]
            if vistos.intersection(ids_actuales):
                print("  > Se detectaron registros repetidos. Fin de la extraccion.")
                break
            vistos.update(ids_actuales)

            expedientes_totales.extend(expedientes_pagina)
            print(f"  > Se extrajeron {len(expedientes_pagina)} expedientes.")
            
            # Usamos el buscador universal de 'siguiente' (Metodo Fase 1)
            next_inicio = parsers.encontrar_siguiente_inicio_universal(html)
            
            if next_inicio and next_inicio > params["inicio"]:
                params["inicio"] = next_inicio
                page_count += 1
                time.sleep(0.5)
            else:
                print("  > No se detecto boton de pagina siguiente.")
                break
                
        except Exception as e:
            print(f"Error fatal en la extraccion masiva: {e}")
            break

    print(f"\nExtraccion finalizada. Total: {len(expedientes_totales)}")
    return expedientes_totales