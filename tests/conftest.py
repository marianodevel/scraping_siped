import pytest
import os
import sys

# ==========================================================
# ===== INICIO DE LA CORRECCIÓN =====
# ==========================================================

# Añadir el directorio raíz al path
# (Esto es buena práctica por si acaso, pero la clave es la variable de entorno)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ESTA ES LA CORRECCIÓN CRÍTICA:
# Establecer la variable de entorno A NIVEL GLOBAL,
# ANTES de que se importe la app por primera vez.
os.environ["FLASK_ENV"] = "testing"

# ========================================================
# ===== FIN DE LA CORRECCIÓN =====
# ========================================================


@pytest.fixture(scope="session")
def app():
    """
    Fixture de sesión para crear la instancia de la app de Flask.
    Ahora que FLASK_ENV está puesto, 'from app import app'
    importará la app ya configurada con los mocks.
    """

    # Esta variable ahora es redundante aquí, pero no hace daño dejarla
    # por si 'test_app.py' (que usa 'client') la necesita.
    os.environ["FLASK_ENV"] = "testing"

    # Esta importación AHORA cargará el app.py en modo "testing"
    # porque la variable de entorno se estableció globalmente.
    from app import app as flask_app

    # Establecer configuraciones de prueba
    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Deshabilitar CSRF para tests E2E
            "DEBUG": False,
            "SERVER_NAME": "localhost",  # Necesario para url_for en live_server
        }
    )

    yield flask_app


# Fixture 'client' (para tests de API/integración como test_app.py)
@pytest.fixture
def client(app):
    """Un cliente de prueba para la app."""
    return app.test_client()


# Fixture 'runner' (para comandos de CLI si los tuvieras)
@pytest.fixture
def runner(app):
    """Un runner para los comandos CLI de Flask."""
    return app.test_cli_runner()
