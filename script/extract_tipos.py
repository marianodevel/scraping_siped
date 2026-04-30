import requests
import json
import time

# Endpoint identificado en la ingeniería inversa
URL_ENDPOINT = "https://siped.jussantacruz.gov.ar/busqueda/get_tipos_juicio"

def fetch_tipos_juicio():
    """
    Realiza una petición al sistema para obtener el catálogo completo.
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(URL_ENDPOINT, headers=headers, timeout=15)
        response.raise_for_status()
        # Aseguramos la codificación correcta para evitar los "ACCI N"
        response.encoding = 'utf-8' 
        return response.json()
    except Exception as e:
        print(f"Error al conectar con SIPED: {e}")
        return None

def save_catalog(data):
    """
    Genera el archivo tipos_juicio.py con el formato requerido.
    """
    with open("scraping_siped/catalogos/tipos_juicio.py", "w", encoding="utf-8") as f:
        f.write("# Archivo generado automáticamente\n")
        f.write("TIPOS_JUICIO = ")
        # Usamos indent para que sea legible y ensure_ascii=False para las tildes
        json_data = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
        f.write(json_data)
        f.write("\n")

if __name__ == "__main__":
    print("Iniciando recuperación de tipos de juicio...")
    catalog_data = fetch_tipos_juicio()
    
    if catalog_data:
        save_catalog(catalog_data)
        print(f"Catálogo actualizado con {len(catalog_data)} entradas.")
    else:
        print("No se pudo actualizar el catálogo.")