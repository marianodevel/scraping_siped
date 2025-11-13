# gestor_almacenamiento.py
import os
import config


def listar_archivos_pdf():
    """
    Escanea el directorio de salida (DOCUMENTOS_OUTPUT_DIR) y devuelve una
    lista ordenada de los nombres de los PDFs compilados.
    """
    lista_pdf = []
    directorio_salida = config.DOCUMENTOS_OUTPUT_DIR

    if os.path.exists(directorio_salida):
        for item in os.listdir(directorio_salida):
            # Solo nos interesan los archivos .pdf
            if item.endswith(".pdf"):
                lista_pdf.append(item)

    return sorted(lista_pdf)
