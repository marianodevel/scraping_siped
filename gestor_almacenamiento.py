# gestor_almacenamiento.py
import os
import config
import utils


def listar_archivos_pdf(username):
    """
    Escanea el directorio de salida (DOCUMENTOS_OUTPUT_DIR) y devuelve una
    lista ordenada de los nombres de los PDFs compilados.
    """
    lista_pdf = []
    ruta_usuario = utils.obtener_ruta_usuario(username)
    directorio_salida = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    if os.path.exists(directorio_salida):
        for item in os.listdir(directorio_salida):
            if item.endswith(".pdf"):
                lista_pdf.append(item)

    return sorted(lista_pdf)
