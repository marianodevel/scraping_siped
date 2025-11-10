# utils.py
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


def read_csv_to_dict(filepath):
    """Lee un archivo CSV y lo devuelve como una lista de diccionarios."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filepath}'.")
        print("Por favor, ejecuta '1_get_lista_expedientes.py' primero.")
        return None
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return None
