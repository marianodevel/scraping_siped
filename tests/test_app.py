import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Agregamos el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    """
    Configura un cliente de prueba de Flask.
    """
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test_key"

    with app.test_client() as client:
        with app.app_context():
            yield client


# --- Tests de Autenticación ---


def test_redirect_login_si_no_hay_sesion(client):
    rv = client.get("/")
    assert rv.status_code == 302
    assert "/login" in rv.location


@patch("app.session_manager")
def test_login_exitoso(mock_sm, client):
    mock_sm.autenticar_en_siped.return_value = {"PHPSESSID": "cookie_test"}

    rv = client.post(
        "/login",
        data={"username": "usuario_prueba", "password": "password123"},
        follow_redirects=True,
    )

    assert rv.status_code == 200
    assert b"Scraper de Expedientes" in rv.data
    with client.session_transaction() as sess:
        assert sess["siped_cookies"] == {"PHPSESSID": "cookie_test"}


@patch("app.session_manager")
def test_login_fallido(mock_sm, client):
    mock_sm.autenticar_en_siped.return_value = None

    rv = client.post(
        "/login",
        data={"username": "usuario_mal", "password": "password_mal"},
        follow_redirects=True,
    )

    assert b"Error de autenticaci" in rv.data


def test_logout(client):
    with client.session_transaction() as sess:
        sess["siped_cookies"] = {"c": "v"}

    rv = client.get("/logout", follow_redirects=True)

    # CORRECCIÓN 1: Comparamos string con string (decodificado) y usamos el acento correcto
    assert "Sesión cerrada exitosamente" in rv.data.decode("utf-8")

    with client.session_transaction() as sess:
        assert "siped_cookies" not in sess


# --- Tests de Rutas Protegidas y Tareas ---


@patch("app.gestor_tareas")
@patch("app.fase_1_lista_task")
def test_iniciar_fase_1(mock_task, mock_gestor, client):
    """
    Simula el inicio de una fase. Mockeamos la tarea de Celery importada en app.py.
    """
    with client.session_transaction() as sess:
        sess["siped_cookies"] = {"c": "v"}

    # Simulamos estado IDLE para permitir ejecutar
    mock_gestor.obtener_id_tarea.return_value = None
    mock_gestor.obtener_estado_tarea.return_value = {"estado": "IDLE"}

    # Mock del objeto AsyncResult que devuelve .delay()
    mock_task_instance = MagicMock()
    mock_task_instance.id = "task_id_123"
    mock_task.delay.return_value = mock_task_instance

    rv = client.post("/iniciar/fase_1")

    assert rv.status_code == 200

    # CORRECCIÓN 2: El mensaje real es "Fase 1" (por el split), no "Fase fase_1"
    assert b"Fase 1 iniciada con ID: task_id_123" in rv.data

    mock_task.delay.assert_called_with(cookies={"c": "v"})
    mock_gestor.registrar_tarea_iniciada.assert_called_with(
        "fase_1", mock_task_instance
    )


@patch("app.gestor_tareas")
def test_ver_estado_fase(mock_gestor, client):
    with client.session_transaction() as sess:
        sess["siped_cookies"] = {"c": "v"}

    mock_gestor.obtener_estado_tarea.return_value = {
        "estado": "STARTED",
        "resultado": "Procesando...",
    }

    rv = client.get("/fragmento/estado/fase_1")

    assert rv.status_code == 200
    assert b"status-STARTED" in rv.data
    assert b"Procesando..." in rv.data
