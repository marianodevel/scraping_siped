"""Configuraciones globales y constantes del sistema SIPED."""

import os
from typing import Dict

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

BASE_URL: str = "https://intranet.jussantacruz.gob.ar"
LOGIN_URL: str = f"{BASE_URL}/servicios/controli2.php"
LISTA_EXPEDIENTES_URL: str = (
    f"{BASE_URL}/siped/expediente/buscar/submit_buscar_abogado.php"
)
AJAX_MOVIMIENTOS_URL: str = (
    f"{BASE_URL}/siped/expediente/buscar/ver_mas_escritosAjax.php"
)

DATA_ROOT_DIR: str = os.path.join(BASE_DIR, "datos_usuarios")
LISTA_EXPEDIENTES_CSV: str = "expedientes_completos.csv"
MOVIMIENTOS_OUTPUT_DIR: str = "movimientos_expedientes"
DOCUMENTOS_OUTPUT_DIR: str = "documentos_expedientes"

BROWSER_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange=vb3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}
