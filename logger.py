"""Configuración centralizada para la emisión de registros del sistema."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene y configura un logger con salida a la consola estándar.

    Args:
        name: Nombre del módulo que solicita el logger.

    Returns:
        Instancia configurada de logging.Logger.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

