import pytest
import requests
import session_manager

def test_auth_faltan_credenciales():
    assert session_manager.autenticar_en_siped("", "pass") is None
    assert session_manager.autenticar_en_siped("usr", "") is None
    assert session_manager.autenticar_en_siped("", "") is None

def test_auth_excepcion_red_post(mocker):
    mocker.patch("requests.Session.post", side_effect=requests.exceptions.ConnectionError("Caído"))
    assert session_manager.autenticar_en_siped("u", "p") is None

def test_auth_excepcion_red_get(mocker):
    mock_post = mocker.patch("requests.Session.post")
    mock_post.return_value.text = "OK"
    mocker.patch("parsers.obtener_url_meta_refresh", return_value="http://redirect")
    
    mocker.patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Timeout"))
    assert session_manager.autenticar_en_siped("u", "p") is None

def test_auth_fallo_obtener_token(mocker):
    mocker.patch("requests.Session.post")
    mocker.patch("parsers.obtener_url_meta_refresh", return_value="http://inicio")
    mocker.patch("requests.Session.get")
    mocker.patch("parsers.obtener_enlace_token_siped", return_value=None)
    assert session_manager.autenticar_en_siped("u", "p") is None

def test_auth_flujo_completo_exitoso(mocker):
    mocker.patch("requests.Session.post")
    mocker.patch("requests.Session.get")
    mocker.patch("parsers.obtener_url_meta_refresh", side_effect=["http://i", "http://f/frame_principal.php"])
    mocker.patch("parsers.obtener_enlace_token_siped", return_value="http://t")
    mocker.patch("session_manager.dict_from_cookiejar", return_value={"sesion": "activa"})
    
    assert session_manager.autenticar_en_siped("u", "p") == {"sesion": "activa"}

def test_crear_sesion_con_cookies():
    s = session_manager.crear_sesion_con_cookies({"mi_cookie": "valor"})
    assert isinstance(s, requests.Session)
    assert s.cookies.get("mi_cookie") == "valor"
    
def test_crear_sesion_sin_cookies():
    s = session_manager.crear_sesion_con_cookies(None)
    assert isinstance(s, requests.Session)
    assert len(s.cookies) == 0
