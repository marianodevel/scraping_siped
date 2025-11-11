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


# --- ¡FUNCIÓN MODIFICADA! ---
def save_to_txt(data, filename, subdirectory):
    """
    Guarda el diccionario de datos del documento en un archivo TXT formateado.
    """
    if not data or not data.get("texto_providencia"):
        print(f"  > No hay contenido de providencia para guardar en {filename}.")
        return

    try:
        # Crear el directorio si no existe
        os.makedirs(subdirectory, exist_ok=True)
        filepath = os.path.join(subdirectory, filename)

        print(f"  > Guardando documento de texto en {filepath}...")

        # Formatear el contenido del TXT
        content = []
        content.append(f"Expediente: {data.get('expediente_nro', 'N/D')}")
        content.append(f"Carátula: {data.get('caratula', 'N/D')}")
        content.append(f"Dependencia: {data.get('dependencia', 'N/D')}")
        content.append(f"Secretaría: {data.get('secretaria', 'N/D')}")
        content.append("=" * 40)
        content.append(f"Nombre Escrito: {data.get('nombre_escrito', 'N/D')}")
        content.append(f"Código Validación: {data.get('codigo_validacion', 'N/D')}")
        content.append("=" * 40)
        content.append("\nTEXTO DE LA PROVIDENCIA:\n")
        content.append(data.get("texto_providencia", "SIN TEXTO"))
        content.append("\n" + "=" * 40)
        content.append("\nFIRMANTES:\n")

        if data.get("firmantes"):
            for f in data["firmantes"]:
                content.append(
                    f"  - {f.get('nombre')} ({f.get('cargo')}) - {f.get('fecha')}"
                )
        else:
            content.append("  N/D")

        final_text = "\n".join(content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_text)

    except Exception as e:
        print(f"  > Error al guardar TXT: {e}")


# --- FIN FUNCIÓN MODIFICADA ---


# --- ¡FUNCIÓN MODIFICADA! ---
def read_csv_to_dict(filepath):
    """Lee un archivo CSV y lo devuelve como una lista de diccionarios."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        # Mensaje genérico, ya que puede ser el CSV de lista o de movimientos
        print(
            f"  > Nota: No se encontró el archivo '{filepath}'. Se creará si es necesario."
        )
        return None
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return None


# --- FIN FUNCIÓN MODIFICADA ---
