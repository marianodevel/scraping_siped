import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from requests.utils import cookiejar_from_dict  # <--- IMPORTANTE: Necesario para el fix

# Agregamos el directorio raíz al path para importar los módulos del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import config

# --- Tests de Autenticación ---


@patch("session_manager.requests.Session")
def test_autenticar_en_siped_exito(mock_session_cls):
    """
    Simula un flujo de login exitoso completo.
    El login de SIPED tiene 4 pasos (Login -> Refresh -> Menu -> Token -> Dashboard).
    Mockeamos cada respuesta HTML para que los parsers encuentren lo que buscan.
    """
    # Obtenemos la instancia del mock de sesión
    mock_session = mock_session_cls.return_value

    # Preparación de respuestas encadenadas (Mocking de la navegación)

    # 1. Respuesta del POST Login: Devuelve un Meta Refresh hacia 'inicio.php'
    r1 = MagicMock()
    r1.text = '<html><head><meta http-equiv="refresh" content="0; url=\'inicio.php\'"></head></html>'
    r1.raise_for_status.return_value = None

    # 2. Respuesta de inicio.php: Devuelve el enlace con el token de sesión
    r2 = MagicMock()
    r2.text = '<html><body><a href="/siped?token=TEST_TOKEN_123">Ingresar al Sistema</a></body></html>'
    r2.raise_for_status.return_value = None

    # 3. Respuesta del enlace token: Devuelve Meta Refresh hacia 'frame_principal.php'
    r3 = MagicMock()
    r3.text = '<html><head><meta http-equiv="refresh" content="0; url=\'frame_principal.php\'"></head></html>'
    r3.raise_for_status.return_value = None

    # 4. Respuesta final (Dashboard): Carga el dashboard
    r4 = MagicMock()
    r4.text = "<html><body>Dashboard Cargado</body></html>"
    r4.raise_for_status.return_value = None

    # Configuramos el mock:
    # .post() se llama 1 vez (login)
    mock_session.post.return_value = r1
    # .get() se llama 3 veces (inicio -> token -> dashboard) en orden
    mock_session.get.side_effect = [r2, r3, r4]

    # --- FIX DEL ERROR ---
    # Usamos cookiejar_from_dict para crear un objeto CookieJar real.
    # Así, cuando el código llame a dict_from_cookiejar(), podrá iterar sobre objetos cookie válidos.
    mock_session.cookies = cookiejar_from_dict({"PHPSESSID": "cookie_falsa_exitosa"})

    # Ejecución de la función a testear
    resultado_cookies = session_manager.autenticar_en_siped(
        "usuario_test", "password_test"
    )

    # Verificaciones
    assert resultado_cookies is not None
    assert resultado_cookies["PHPSESSID"] == "cookie_falsa_exitosa"

    # Verificamos que se enviaron las credenciales correctamente
    mock_session.post.assert_called_with(
        config.LOGIN_URL, data={"usuario": "usuario_test", "pass": "password_test"}
    )
    # Verificamos que se realizaron las 3 navegaciones GET subsiguientes
    assert mock_session.get.call_count == 3


@patch("session_manager.requests.Session")
def test_autenticar_en_siped_fallo_credenciales(mock_session_cls):
    """
    Simula un login fallido donde el servidor devuelve la página de login nuevamente
    en lugar del meta refresh esperado.
    """
    mock_session = mock_session_cls.return_value

    # Respuesta de Login incorrecto (sin meta refresh)
    r_error = MagicMock()
    r_error.text = "<html><body>Usuario o clave incorrecta</body></html>"
    r_error.raise_for_status.return_value = None

    mock_session.post.return_value = r_error

    resultado = session_manager.autenticar_en_siped("usuario_mal", "pass_mal")

    # Debe retornar None al no poder seguir el flujo
    assert resultado is None


@patch("session_manager.requests.Session")
def test_autenticar_en_siped_sin_credenciales(mock_session_cls):
    """Verifica que la función falle rápido si no se pasan usuario o clave."""
    resultado = session_manager.autenticar_en_siped("", "")

    assert resultado is None
    # No debería ni siquiera instanciar la sesión
    assert mock_session_cls.called is False


# --- Test de Creación de Sesión con Cookies ---


def test_crear_sesion_con_cookies():
    """
    Verifica que la función auxiliar restaure correctamente un objeto Session
    a partir de un diccionario de cookies guardado.
    """
    cookies_input = {"PHPSESSID": "abc_123_recuperada"}

    session = session_manager.crear_sesion_con_cookies(cookies_input)

    # Verificamos que sea un objeto Session válido
    assert session is not None
    # requests almacena las cookies en un CookieJar; verificamos que contenga nuestro valor
    assert session.cookies.get("PHPSESSID") == "abc_123_recuperada"
    # Verificamos que los headers globales (config.py) se hayan cargado
    assert session.headers["User-Agent"] == config.BROWSER_HEADERS["User-Agent"]
