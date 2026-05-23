import pytest
import requests
import scraper_tasks
from unittest.mock import mock_open, call

def test_descargar_archivo_excepciones_red(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.HTTPError("404 Not Found")
    assert scraper_tasks.descargar_archivo(mock_session, "http://url", "dest.pdf") is False

def test_descargar_archivo_timeout(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.Timeout("Timeout")
    assert scraper_tasks.descargar_archivo(mock_session, "http://url", "dest.pdf") is False

def test_raspar_lista_excepciones_red(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.ConnectionError("Red muerta")
    assert scraper_tasks.raspar_lista_expedientes(mock_session) == []

def test_raspar_movimientos_sin_link(mocker):
    mock_session = mocker.Mock()
    # Expediente no tiene "link_detalle"
    assert scraper_tasks.raspar_movimientos_de_expediente(mock_session, {"expediente": "123"}) == []

def test_raspar_movimientos_falla_frameset(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.RequestException("Fallo en frameset")
    assert scraper_tasks.raspar_movimientos_de_expediente(mock_session, {"link_detalle": "http://x"}) == []

def test_raspar_contenido_doc_invalido(mocker):
    mock_session = mocker.Mock()
    assert scraper_tasks.raspar_contenido_documento(mock_session, "") is None
    assert scraper_tasks.raspar_contenido_documento(mock_session, "   ") is None

def test_raspar_contenido_doc_red_caida(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.RequestException("Servidor no responde")
    assert scraper_tasks.raspar_contenido_documento(mock_session, "http://url") is None

def test_raspar_busqueda_parametrizada_excepcion(mocker):
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.RequestException("Error 500")
    assert scraper_tasks.raspar_busqueda_parametrizada(mock_session, {}) == []

def test_raspar_busqueda_parametrizada_prevencion_bucle_infinito(mocker):
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.text = "html_dummy"
    mock_session.get.return_value = mock_response
    
    # Simulamos que el parser siempre devuelve el mismo expediente y el script intenta avanzar
    mocker.patch("parsers.parsear_lista_publica", return_value=[{"expediente": "EXP-BUCLE"}])
    mocker.patch("parsers.encontrar_siguiente_inicio_universal", return_value=10)
    mocker.patch("time.sleep", return_value=None)
    
    res = scraper_tasks.raspar_busqueda_parametrizada(mock_session, {"texto": "prueba"})
    
    # El sistema debe detectar la intersección (bucle) y abortar iteraciones
    # Por tanto solo debe haber 1 resultado en lugar de quedarse congelado
    assert len(res) == 1
    assert res[0]["expediente"] == "EXP-BUCLE"
