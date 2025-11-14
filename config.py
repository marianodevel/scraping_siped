# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Credenciales ELIMINADAS ---
# Las credenciales ya no se leen de aquí.
# USUARIO = os.getenv("USUARIO_INTRANET")
# CLAVE = os.getenv("CLAVE_INTRANET")

# --- Constantes del Sitio ---
BASE_URL = "https://intranet.jussantacruz.gob.ar"
LOGIN_URL = f"{BASE_URL}/servicios/controli2.php"
LISTA_EXPEDIENTES_URL = f"{BASE_URL}/siped/expediente/buscar/submit_buscar_abogado.php"
AJAX_MOVIMIENTOS_URL = f"{BASE_URL}/siped/expediente/buscar/ver_mas_escritosAjax.php"

# --- Archivos de Salida ---
LISTA_EXPEDIENTES_CSV = "expedientes_completos.csv"
MOVIMIENTOS_OUTPUT_DIR = "movimientos_expedientes"
DOCUMENTOS_OUTPUT_DIR = "documentos_expedientes"

# --- Headers ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange=vb3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}
