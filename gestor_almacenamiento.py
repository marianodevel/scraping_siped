"""Módulo para la consulta y administración de archivos locales generados."""

import os
from typing import List

import config
import utils


def listar_archivos_pdf(username: str) -> List[str]:
    """
    Escanea el directorio de salida y devuelve los nombres de los PDFs compilados.

    Args:
        username: Identificador del usuario actual.

    Returns:
        Lista ordenada alfabéticamente con los nombres de los archivos PDF.
    """
    lista_pdf = []
    ruta_usuario = utils.obtener_ruta_usuario(username)
    directorio_salida = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    if os.path.exists(directorio_salida):
        for item in os.listdir(directorio_salida):
            if item.endswith(".pdf"):
                lista_pdf.append(item)

    return sorted(lista_pdf)


def verificar_csv_maestro(username: str) -> bool:
    """
    Verifica la existencia física del archivo CSV maestro de la Fase 1.

    Args:
        username: Identificador del usuario actual.

    Returns:
        Verdadero si el archivo existe, Falso en caso contrario.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    ruta_csv = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)
    return os.path.exists(ruta_csv)


def listar_archivos_movimientos(username: str) -> List[str]:
    """
    Devuelve una lista de los archivos CSV de movimientos extraídos.

    Args:
        username: Identificador del usuario actual.

    Returns:
        Lista ordenada de nombres de archivos CSV correspondientes a movimientos.
    """
    lista_movs = []
    ruta_usuario = utils.obtener_ruta_usuario(username)
    directorio_salida = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)

    if os.path.exists(directorio_salida):
        for item in os.listdir(directorio_salida):
            if item.endswith(".csv"):
                lista_movs.append(item)

    return sorted(lista_movs)


def listar_archivos_busqueda(username: str) -> List[str]:
    """
    Devuelve una lista con todos los archivos de búsquedas avanzadas.

    Args:
        username: Identificador del usuario actual.

    Returns:
        Lista de nombres de archivos CSV ordenados del más reciente al más antiguo.
    """
    lista_busquedas = []
    ruta_usuario = utils.obtener_ruta_usuario(username)

    if os.path.exists(ruta_usuario):
        for item in os.listdir(ruta_usuario):
            if item.startswith("busqueda_") and item.endswith(".csv"):
                lista_busquedas.append(item)

    lista_busquedas.sort(reverse=True)
    return lista_busquedas

