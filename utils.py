# utils.py
import csv
import os
import re
from fpdf import FPDF
import functools
import session_manager

# Importar la librería de fusión de PDF (REQUIERE INSTALACIÓN: pip install pypdf)
try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    # Definición de placeholder para que el código funcione en ausencia de la librería
    class MockPdfWriter:
        def add_page(self, page):
            pass

        def write(self, file):
            print(f"--- MOCK PDF WRITER: ESCRIBIENDO {file.name} ---")

    class MockPdfReader:
        def __init__(self, file):
            pass

        @property
        def pages(self):
            # Retorna una página simulada para que la lógica de fusión no falle inmediatamente
            return [object()]

    PdfWriter = MockPdfWriter
    PdfReader = MockPdfReader
    print(
        "ADVERTENCIA: Librería 'pypdf' no encontrada. La función de fusión de PDF es simulada."
    )


def limpiar_nombre_archivo(name):
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


def guardar_a_csv(data, filename, subdirectory="."):
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


def guardar_a_txt(data, filename, subdirectory):
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


def leer_csv_a_diccionario(filepath):
    """
    Lee un archivo CSV y lo devuelve como una lista de diccionarios.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(
            f"  > Nota: No se encontró el archivo '{filepath}'. Se creará si es necesario."
        )
        return None
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return None


def compilar_textos_a_pdf(source_directory, output_pdf_path):
    """
    Lee todos los .txt de un directorio, los ordena y los compila en un PDF.
    """
    print(f"  > Compilando PDF en: {output_pdf_path}...")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_family = "Roboto"
    text_sanitized = False

    try:
        # Asume que los archivos Roboto-Regular.ttf y Roboto-Bold.ttf están en el directorio
        pdf.add_font(font_family, "", "Roboto-Regular.ttf")
        pdf.add_font(font_family, "B", "Roboto-Bold.ttf")

        pdf.set_font(font_family, size=10)

    except (FileNotFoundError, RuntimeError) as e:
        print(f"  > !!! ADVERTENCIA DE FUENTE: {e}")
        print(
            "  > No se pudieron encontrar 'Roboto-Regular.ttf' o 'Roboto-Bold.ttf' en el directorio."
        )
        print("  > Volviendo a 'Arial'. Caracteres especiales se reemplazarán por '?'.")

        font_family = "Arial"
        text_sanitized = True
        pdf.set_font(font_family, size=10)

    try:
        txt_files = [f for f in os.listdir(source_directory) if f.endswith(".txt")]
        txt_files.sort()

        if not txt_files:
            print("  > No se encontraron archivos .txt para compilar.")
            return

        for txt_file in txt_files:
            txt_path = os.path.join(source_directory, txt_file)

            pdf.add_page()

            pdf.set_font(font_family, "B", 14)

            title_to_write = txt_file
            if text_sanitized:
                title_to_write = txt_file.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 10, title_to_write, ln=True, align="C")

            pdf.ln(5)

            pdf.set_font(font_family, size=10)

            text_content = ""
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text_content = f.read()

                text_to_write = text_content
                if text_sanitized:
                    text_to_write = text_content.encode("latin-1", "replace").decode(
                        "latin-1"
                    )

                pdf.multi_cell(0, 5, text_to_write)

            except Exception as e:
                print(f"    > Error leyendo {txt_file}: {e}")
                error_msg = f"Error al leer el archivo: {e}"
                if text_sanitized:
                    error_msg = error_msg.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 5, error_msg)

        pdf.output(output_pdf_path)

        if text_sanitized:
            print(
                f"  > PDF guardado (modo fallback, caracteres no compatibles reemplazados por '?')."
            )
        else:
            print(f"  > PDF guardado exitosamente con fuente Unicode.")

    except Exception as e:
        print(f"  > !!! ERROR al generar PDF: {e}")
        import traceback

        traceback.print_exc()


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

    # Ordenar alfabéticamente para asegurar el orden cronológico (gracias a la nomenclatura 01, 02, etc.)
    pdf_files.sort()

    merger = PdfWriter()

    archivos_agregados = []
    try:
        for filename in pdf_files:
            filepath = os.path.join(source_directory, filename)

            # Usamos el modo binario 'rb' para leer PDFs
            with open(filepath, "rb") as f:
                reader = PdfReader(f)
                # Verifica si el objeto es un mock o si tiene páginas (si es el pypdf real)
                if hasattr(reader, "pages") and reader.pages:
                    for page in reader.pages:
                        merger.add_page(page)
                    archivos_agregados.append(filename)
                elif not hasattr(reader, "pages"):  # Es el Mock Object
                    merger.add_page(object())  # Simular adición
                    archivos_agregados.append(filename)

                else:
                    print(
                        f"    > ADVERTENCIA: '{filename}' está vacío o corrupto, saltando."
                    )

        # Escribir el PDF de salida
        if archivos_agregados:
            with open(output_pdf_path, "wb") as f:
                merger.write(f)

            print(
                f"  > PDF de expediente fusionado exitosamente. Documentos incluidos: {len(archivos_agregados)}"
            )
        else:
            print("  > No se pudo fusionar ningún archivo PDF válido.")

    except Exception as e:
        print(f"  > !!! ERROR al fusionar PDFs: {e}")
        import traceback

        traceback.print_exc()

    finally:
        pass


def manejar_fase_con_sesion(nombre_fase):
    """
    Decorador para gestionar el boilerplate de una fase de scraping.
    Ahora crea la sesión a partir de las cookies.
    """

    def decorador(funcion_nucleo):
        # El wrapper ahora espera 'cookies' como primer argumento posicional
        @functools.wraps(funcion_nucleo)
        def wrapper(cookies, *args, **kwargs):
            print(f"--- INICIANDO {nombre_fase} ---")
            try:
                # 1. Crear la Sesión a partir de las cookies
                session = session_manager.crear_sesion_con_cookies(cookies)

                # 2. Ejecutar la lógica específica de la fase
                mensaje = funcion_nucleo(session, *args, **kwargs)

                # 3. Éxito
                print(mensaje)
                return mensaje

            except Exception as e:
                # 4. Manejo de Error Fatal
                mensaje = f"Error fatal en {nombre_fase}: {e}"
                print(mensaje)
                raise Exception(mensaje)

        return wrapper

    return decorador
