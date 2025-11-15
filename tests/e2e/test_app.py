import pytest
from flask import session
import app  #

# Usamos 'client' (de conftest.py) y 'mocker' (de pytest-mock)


def test_login_get(client):
    """Prueba que la página de login cargue."""
    response = client.get("/login")  #
    assert response.status_code == 200
    assert b"Usuario (Intranet)" in response.data


def test_login_post_fallido(client, mocker):
    """Prueba un intento de login fallido."""

    # Simulamos que la autenticación falla
    mocker.patch("app.session_manager.autenticar_en_siped", return_value=None)  #

    response = client.post(
        "/login",  #
        data={"username": "user", "password": "bad_password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Error de autenticaci" in response.data  # Mensaje flash
    assert b"Usuario (Intranet)" in response.data  # Sigue en /login


def test_login_post_exitoso_y_logout(client, mocker):
    """Prueba un login exitoso, la sesión y el logout."""

    # Simulamos que la autenticación tiene éxito
    fake_cookies = {"JSESSIONID": "abc12345"}
    mocker.patch(
        "app.session_manager.autenticar_en_siped", return_value=fake_cookies
    )  #

    # 1. Hacemos LOGIN
    response = client.post(
        "/login",  #
        data={"username": "good_user", "password": "good_password"},
        follow_redirects=True,
    )

    # Verifica que se redirige al índice
    assert response.status_code == 200
    assert b"Bienvenido, good_user!" in response.data  # Mensaje flash

    # Verifica que la sesión de Flask ahora tiene las cookies
    # (Necesitamos 'with client.session_transaction()' si no usamos follow_redirects)

    # 2. Probamos una RUTA PROTEGIDA (el índice)
    response = client.get("/")  #
    assert response.status_code == 200
    # *** CORRECCIÓN AQUÍ ***
    # El template renderiza "Fase 1", no "Estado Fase 1"
    assert b"Fase 1" in response.data
    assert b"good_user" in response.data  # Muestra el nombre de usuario

    # 3. Hacemos LOGOUT
    response = client.get("/logout", follow_redirects=True)  #
    assert response.status_code == 200
    assert b"Sesi" in response.data  # Mensaje de sesión cerrada
    assert b"Usuario (Intranet)" in response.data  # De vuelta en /login


def test_rutas_protegidas_sin_login(client):
    """Prueba que las rutas protegidas redirijan al login."""

    rutas_protegidas = [
        "/",
        "/iniciar/fase_1",
        "/resetear_estado/fase_1",
        "/fragmento/estado/fase_1",
        "/fragmento/pdfs",
        "/estado_tarea/fase_1",
        "/descargar/test.pdf",
    ]  #

    for ruta in rutas_protegidas:
        # Usamos 'client.get' o 'client.post' según la ruta
        if "iniciar" in ruta:
            response = client.post(ruta, follow_redirects=True)
        else:
            response = client.get(ruta, follow_redirects=True)

        assert response.status_code == 200
        # Todas deben redirigir al login
        assert b"Usuario (Intranet)" in response.data, f"Ruta {ruta} no protegidia"
        # Y mostrar un mensaje flash
        assert b"Por favor, inicia sesi" in response.data


def test_iniciar_fase(client, mocker):
    """Prueba el endpoint para iniciar una tarea (simulando login)."""

    # 1. Simulamos el login (la forma más fácil es "inyectar"
    #    la cookie en la sesión del cliente de prueba)
    with client.session_transaction() as sess:
        sess["siped_cookies"] = {"JSESSIONID": "abc12345"}
        sess["username"] = "test_user"

    # 2. Simulamos el gestor de tareas (para que diga que no está PENDING)
    mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "SUCCESS"},
    )  #

    # 3. Simulamos la tarea de Celery (el .delay())
    mock_tarea = mocker.Mock()
    mock_tarea.id = "celery-task-id-123"
    mock_task_delay = mocker.patch(
        "app.fase_1_lista_task.delay", return_value=mock_tarea
    )  #

    # 4. Simulamos el registro de la tarea
    mock_registrar = mocker.patch("app.gestor_tareas.registrar_tarea_iniciada")  #

    # 5. Llamamos al endpoint
    response = client.post("/iniciar/fase_1")  #

    # 6. Verificamos
    assert response.status_code == 200
    assert b"Fase 1 iniciada" in response.data

    # Verifica que se llamó a la tarea de Celery con las cookies correctas
    mock_task_delay.assert_called_once_with(cookies={"JSESSIONID": "abc12345"})

    # Verifica que se registró en el gestor
    mock_registrar.assert_called_once_with("fase_1", mock_tarea)
