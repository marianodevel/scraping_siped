import csv
import os
import re
import functools
import session_manager

# Importamos pypdf directamente, ya que está en requirements.txt
try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print(
        "ERROR CRÍTICO: 'pypdf' no está instalado. Ejecute 'pip install -r requirements.txt'"
    )
    raise


def limpiar_nombre_archivo(name):
    """
    Limpia un string para que sea un nombre de archivo válido.
    """
    if not name:
        name = "SIN_NOMBRE"
    name = name.replace("/", "-")
    name = re.sub(r'[\\*?:"<>|]', "", name)
    return name[:150].strip()


def guardar_a_csv(data, filename, subdirectory="."):
    """
    Guarda una lista de diccionarios en un archivo CSV.
    """
    if not data:
        print(f"  > No hay datos para guardar en {filename}.")
        return

    try:
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


def leer_csv_a_diccionario(filepath):
    """
    Lee un archivo CSV y lo devuelve como una lista de diccionarios.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"  > Nota: No se encontró el archivo '{filepath}'.")
        return None
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return None


def fusionar_pdfs(source_directory, output_pdf_path):
    """
    Busca todos los archivos PDF en source_directory, los ordena
    alfabéticamente y los fusiona en un solo PDF.
    """
    print(f"  > Fusionando PDFs en: {output_pdf_path}...")
    pdf_files = [f for f in os.listdir(source_directory) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("  > No se encontraron archivos .pdf para fusionar.")
        return

    # Ordenar alfabéticamente para asegurar el orden cronológico
    pdf_files.sort()

    merger = PdfWriter()
    archivos_agregados = []

    try:
        for filename in pdf_files:
            filepath = os.path.join(source_directory, filename)

            with open(filepath, "rb") as f:
                reader = PdfReader(f)
                if len(reader.pages) > 0:
                    for page in reader.pages:
                        merger.add_page(page)
                    archivos_agregados.append(filename)
                else:
                    print(f"    > ADVERTENCIA: '{filename}' está vacío, saltando.")

        if archivos_agregados:
            with open(output_pdf_path, "wb") as f:
                merger.write(f)
            print(
                f"  > PDF fusionado exitosamente. Documentos incluidos: {len(archivos_agregados)}"
            )
        else:
            print("  > No se pudo fusionar ningún archivo PDF válido.")

    except Exception as e:
        print(f"  > !!! ERROR al fusionar PDFs: {e}")
        import traceback

        traceback.print_exc()


def manejar_fase_con_sesion(nombre_fase):
    """
    Decorador para gestionar el boilerplate de una fase de scraping.
    Crea la sesión a partir de las cookies.
    """

    def decorador(funcion_nucleo):
        @functools.wraps(funcion_nucleo)
        def wrapper(cookies, *args, **kwargs):
            print(f"--- INICIANDO {nombre_fase} ---")
            try:
                session = session_manager.crear_sesion_con_cookies(cookies)
                mensaje = funcion_nucleo(session, *args, **kwargs)
                print(mensaje)
                return mensaje

            except Exception as e:
                mensaje = f"Error fatal en {nombre_fase}: {e}"
                print(mensaje)
                raise Exception(mensaje)

        return wrapper

    return decorador
