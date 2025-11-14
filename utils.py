# utils.py
import csv
import os
import re
from fpdf import FPDF
import functools  # <<< AÑADIR
import session_manager  # <<< AÑADIR

# ... (todas tus funciones existentes: limpiar_nombre_archivo, guardar_a_csv, etc.) ...
# ... (asegúrate de que todo el código anterior esté aquí) ...


def limpiar_nombre_archivo(name):
    """
    Limpia un string para que sea un nombre de archivo válido.
    (Original: sanitize_filename)
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
    (Original: save_to_csv)
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
    (Original: save_to_txt)
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
    (Original: read_csv_to_dict)
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
    (Original: compile_texts_to_pdf)
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


# --- V V V DECORADOR DE FASE AÑADIDO V V V ---


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
