# utils.py
import csv
import os
import re
from fpdf import FPDF


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


# --- ¡FUNCIÓN MODIFICADA! ---
def compile_texts_to_pdf(source_directory, output_pdf_path):
    """
    Lee todos los .txt de un directorio, los ordena y los compila en un PDF.
    Intenta usar la fuente Roboto (que debe estar instalada en el sistema)
    y vuelve a Arial si falla.
    """
    print(f"  > Compilando PDF en: {output_pdf_path}...")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Usaremos "Roboto" como el nombre de la familia en FPDF
    font_family = "Roboto"
    text_sanitized = False  # Flag para fallback

    try:
        # --- INICIO DE LA CORRECCIÓN ---
        # Le decimos a FPDF que registre la fuente "Roboto"
        # buscando los archivos .ttf en las rutas del sistema.

        pdf.add_font(font_family, "", "Roboto-Regular.ttf")
        pdf.add_font(font_family, "B", "Roboto-Bold.ttf")

        # Ahora que la fuente está añadida, la usamos.
        pdf.set_font(font_family, size=10)
        # --- FIN DE LA CORRECCIÓN ---

    except (FileNotFoundError, RuntimeError) as e:
        # Este es el bloque de fallback si FPDF no encuentra las fuentes
        print(f"  > !!! ADVERTENCIA DE FUENTE: {e}")
        print(
            "  > No se pudieron encontrar 'Roboto-Regular.ttf' o 'Roboto-Bold.ttf' en las rutas del sistema."
        )
        print("  > Volviendo a 'Arial'. Caracteres especiales se reemplazarán por '?'.")

        font_family = "Arial"  # Fallback
        text_sanitized = True  # Marcar que necesitamos sanitizar el texto
        pdf.set_font(font_family, size=10)

    try:
        # 1. Encontrar y ordenar los archivos .txt
        txt_files = [f for f in os.listdir(source_directory) if f.endswith(".txt")]
        txt_files.sort()

        if not txt_files:
            print("  > No se encontraron archivos .txt para compilar.")
            return

        for txt_file in txt_files:
            txt_path = os.path.join(source_directory, txt_file)

            pdf.add_page()

            # Título de la página
            pdf.set_font(font_family, "B", 14)

            title_to_write = txt_file
            if text_sanitized:
                title_to_write = txt_file.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 10, title_to_write, ln=True, align="C")

            pdf.ln(5)

            # Contenido del archivo
            pdf.set_font(font_family, size=10)

            text_content = ""
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text_content = f.read()

                text_to_write = text_content
                if text_sanitized:
                    # Si estamos en modo fallback, sanitizamos
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
