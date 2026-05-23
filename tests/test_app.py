import pytest
from flask import session
import os
import config

def test_login_get(client):
    response = client.get("/login")
    assert response.status_code == 200

def test_login_post_exitoso(client, mocker):
    mocker.patch("session_manager.autenticar_en_siped", return_value={"siped_session": "token_123"})
    response = client.post("/login", data={"username": "usuario_prueba", "password": "clave_segura"}, follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["username"] == "usuario_prueba"
        assert sess["siped_cookies"] == {"siped_session": "token_123"}

def test_login_post_fallido(client, mocker):
    mocker.patch("session_manager.autenticar_en_siped", return_value=None)
    response = client.post("/login", data={"username": "usuario_erroneo", "password": "clave_falsa"}, follow_redirects=True)
    with client.session_transaction() as sess:
        assert "username" not in sess

def test_ruta_protegida_requiere_login(client):
    assert client.get("/").status_code == 302
    assert client.get("/fragmento/pdfs").status_code == 302
    assert client.post("/iniciar/fase_1").status_code == 302

def test_logout(client):
    with client.session_transaction() as sess:
        sess["username"] = "usuario_test"
        sess["siped_cookies"] = {"siped_session": "token_test"}
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "username" not in sess

def test_iniciar_fase_desconocida(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    response = client.post("/iniciar/fase_inexistente")
    assert response.status_code == 400

def test_iniciar_fase_en_curso(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    mocker.patch("gestor_tareas.obtener_estado_tarea", return_value={"estado": "STARTED"})
    response = client.post("/iniciar/fase_1")
    assert response.status_code == 200
    assert b"curso" in response.data or b"warning" in response.data # Depende de los flashes

def test_descargar_archivo_404(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    mocker.patch("utils.obtener_ruta_usuario", return_value="/ruta/falsa")
    response = client.get("/descargar/maestro/archivo_falso.csv")
    assert response.status_code == 404

def test_descargar_por_expediente_404_sin_datos(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    mocker.patch("db_manager.obtener_expedientes", return_value=[])
    mocker.patch("utils.leer_csv_a_diccionario", return_value=[])
    response = client.get("/descargar_por_expediente/000-2026")
    assert response.status_code == 404

def test_debug_expediente_no_encontrado(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    mocker.patch("db_manager.obtener_expedientes", return_value=[])
    response = client.get("/debug/999-2026")
    assert response.status_code == 200
    assert b"no encontrado en la base de datos" in response.data

def test_debug_expediente_exitoso(client, mocker):
    with client.session_transaction() as sess:
        sess["username"] = "test"
        sess["siped_cookies"] = {}
    mocker.patch("db_manager.obtener_expedientes", return_value=[{"expediente": "123-2026", "id": 1}])
    mocker.patch("db_manager.obtener_movimientos", return_value=[{"fecha_presentacion": "01/01", "nombre_escrito": "Demanda", "estado": "Despacho"}])
    response = client.get("/debug/123-2026")
    assert response.status_code == 200
    assert b"Diagn" in response.data
    assert b"Demanda" in response.data
