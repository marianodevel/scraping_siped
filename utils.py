# marianodevel/scraping_siped/marianodevel-scraping_siped-c1d54d11d3b59f2e8f0a682b7ed49cc9c0bba71f/utils.py
import csv
import os
import re


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


def save_to_csv(data, filename, subdirectory="."):
    """
    Guarda una lista de diccionarios en un archivo CSV dentro de un subdirectorio.
    """
    if not data:
        print(f"  > No hay datos para guardar en {filename}.")
        return

    try:
        # Crear el directorio si no existe
        os.makedirs(subdirectory, exist_ok=True)
        filepath = os.path.join(subdirectory, filename)

        print(f"  > Guardando {len(data)} filas en {filepath}...")

        headers = data[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

    except Exception as e:
        print(f"  > Error al guardar CSV: {e}")


def save_to_txt(content, filename, subdirectory):
    """
    Guarda el contenido de texto en un archivo TXT dentro de un subdirectorio.
    """
    if not content:
        print(f"  > No hay contenido para guardar en {filename}.")
        return

    try:
        # Crear el directorio si no existe
        os.makedirs(subdirectory, exist_ok=True)
        filepath = os.path.join(subdirectory, filename)

        print(f"  > Guardando documento de texto en {filepath}...")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    except Exception as e:
        print(f"  > Error al guardar TXT: {e}")


def read_csv_to_dict(filepath):
    """Lee un archivo CSV y lo devuelve como una lista de diccionarios."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        # Esto no es un error fatal, solo significa que el CSV no existe
        # (por ejemplo, si 2_get_movimientos no se ha ejecutado)
        return None
    except Exception as e:
        print(f"Error al leer el CSV '{filepath}': {e}")
        return None
