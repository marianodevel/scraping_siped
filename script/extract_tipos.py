"""Script utilitario para la extracción y generación del catálogo de Tipos de Juicio."""

import json
from typing import Any, Dict, Optional
import requests

# Endpoint identificado en la ingeniería inversa
URL_ENDPOINT = "https://siped.jussantacruz.gov.ar/busqueda/get_tipos_juicio"


def fetch_tipos_juicio() -> Optional[Dict[str, str]]:
    """
    Realiza una petición al sistema judicial para obtener el catálogo completo de juicios.

    Returns:
        Diccionario con la respuesta JSON parseada o None si la conexión falla.
    """
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    try:
        response = requests.get(URL_ENDPOINT, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.json()
    except Exception as e:
        print(f"Error al conectar con SIPED: {e}")
        return None


def save_catalog(data: Dict[str, str]) -> None:
    """
    Genera el archivo Python del catálogo con el formato de diccionario requerido.

    Args:
        data: Diccionario con los tipos de juicio devueltos por el servidor.
    """
    with open("scraping_siped/catalogos/tipos_juicio.py", "w", encoding="utf-8") as f:
        f.write("# Archivo generado automáticamente\n")
        f.write("TIPOS_JUICIO = ")
        json_data = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
        f.write(json_data)
        f.write("\n")


if __name__ == "__main__":
    print("Iniciando recuperación de tipos de juicio...")
    catalog_data = fetch_tipos_juicio()

    if catalog_data:
        print(
            f"Catálogo descargado con éxito. Elementos encontrados: {len(catalog_data)}"
        )
        save_catalog(catalog_data)
        print("Archivo guardado en 'scraping_siped/catalogos/tipos_juicio.py'")
    else:
        print("Fallo en la recuperación del catálogo.")

