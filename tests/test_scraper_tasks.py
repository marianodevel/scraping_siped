import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call

# Agregamos el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scraper_tasks
import config

# --- Test de Descarga de Archivos ---


def test_descargar_archivo_exito(tmp_path):
    """
    Verifica que la función escriba los chunks recibidos en el disco.
    """
    # Setup del mock de sesión
    mock_session = MagicMock()
    mock_response = MagicMock()

    # Simulamos contenido binario en chunks
    mock_response.iter_content.return_value = [b"parte1", b"parte2"]
    mock_response.status_code = 200
    mock_session.get.return_value.__enter__.return_value = mock_response

    # Archivo destino temporal
    archivo_destino = tmp_path / "test_download.pdf"

    # Ejecución
    resultado = scraper_tasks.descargar_archivo(
        mock_session, "http://fake.url/doc.pdf", str(archivo_destino)
    )

    # Verificaciones
    assert resultado is True
    assert archivo_destino.read_bytes() == b"parte1parte2"
    mock_session.get.assert_called_with(
        "http://fake.url/doc.pdf", stream=True, timeout=30
    )


def test_descargar_archivo_error(tmp_path):
    """Verifica que retorne False si hay una excepción de red."""
    mock_session = MagicMock()
    # Simulamos que requests lanza una excepción
    mock_session.get.side_effect = Exception("Error de conexión")

    archivo_destino = tmp_path / "fallido.pdf"
    resultado = scraper_tasks.descargar_archivo(
        mock_session, "http://url", str(archivo_destino)
    )

    assert resultado is False
    assert not archivo_destino.exists()


# --- Test de Lógica de Paginación (Lista Expedientes) ---


@patch("scraper_tasks.parsers")  # Mockeamos el módulo parsers entero
def test_raspar_lista_expedientes_paginacion(mock_parsers):
    """
    Simula un escenario con 2 páginas de resultados.
    Página 1 -> Encuentra expedientes y detecta botón 'siguiente' (inicio=10).
    Página 2 -> Encuentra expedientes y NO detecta botón 'siguiente'.
    """
    mock_session = MagicMock()

    # Configuración de los mocks de los parsers para simular el comportamiento
    # Llamada 1: Devuelve 2 expedientes. Llamada 2: Devuelve 1 expediente.
    mock_parsers.parsear_lista_expedientes.side_effect = [
        [{"exp": "1"}],
        [{"exp": "2"}],
    ]

    # Llamada 1: Encuentra siguiente página (10). Llamada 2: No encuentra (None).
    mock_parsers.encontrar_siguiente_pagina_inicio.side_effect = [10, None]

    # Ejecución
    lista_final = scraper_tasks.raspar_lista_expedientes(mock_session)

    # Verificaciones
    assert len(lista_final) == 2  # 1 de la pág 1 + 1 de la pág 2
    assert lista_final[0]["exp"] == "1"
    assert lista_final[1]["exp"] == "2"

    # Verificar que el bucle llamó a la URL correcta con los parámetros cambiantes
    expected_calls = [
        call(config.LISTA_EXPEDIENTES_URL, params={"inicio": 0}),
        call(config.LISTA_EXPEDIENTES_URL, params={"inicio": 10}),
    ]

    # CORRECCIÓN 1: Usamos any_order=True
    mock_session.get.assert_has_calls(expected_calls, any_order=True)


# --- Test de Flujo Completo de Movimientos ---


@patch("scraper_tasks.parsers")
def test_raspar_movimientos_de_expediente_flujo(mock_parsers):
    """
    Verifica la compleja danza de obtener movimientos.
    """
    mock_session = MagicMock()

    # Datos de entrada
    expediente_input = {"expediente": "100/23", "link_detalle": "http://url/frameset"}

    # --- Configuración de respuestas de Sesión (HTMLs simulados) ---
    # R1: Frameset
    r_frameset = MagicMock()
    r_frameset.text = '<html><frame name="sup" src="detalle_real.php"></html>'

    # R2: Detalle Real (HTML)
    r_detalle = MagicMock()
    r_detalle.text = "<html>Input ID...</html>"

    # R3: AJAX Movimientos (Página 1) - Contenido
    r_ajax_1 = MagicMock()
    # --- FIX CRÍTICO: Relleno > 200 caracteres para pasar el check de longitud ---
    r_ajax_1.text = "<table>tabla llena</table>" + (" " * 200)

    # R4: AJAX Movimientos (Página 2) - Vacío (Fin del bucle)
    r_ajax_2 = MagicMock()
    r_ajax_2.text = ""  # Texto corto rompe el bucle (< 200 chars)

    mock_session.get.side_effect = [r_frameset, r_detalle, r_ajax_1, r_ajax_2]

    # --- Configuración de Parsers ---

    # 1. Extraer params AJAX
    # CORRECCIÓN 2: Clave "exp_id" correcta
    mock_parsers.parsear_detalle_para_ajax_params.return_value = {"exp_id": 999}

    # 2. Parsear movimientos del HTML AJAX
    mock_parsers.parsear_movimientos_de_ajax_html.side_effect = [[{"mov": "uno"}]]

    # Ejecución
    movimientos = scraper_tasks.raspar_movimientos_de_expediente(
        mock_session, expediente_input
    )

    # Verificaciones
    assert len(movimientos) == 1
    assert movimientos[0]["mov"] == "uno"

    mock_session.get.assert_any_call("http://url/detalle_real.php")
    assert mock_session.get.call_count == 4


# --- Test de Scraping de Documento (PDFs) ---


@patch("scraper_tasks.parsers")
def test_raspar_contenido_documento(mock_parsers):
    """Verifica que delegue correctamente al parser de documentos."""
    mock_session = MagicMock()

    # Mock parser return
    data_esperada = {"url_pdf_principal": "http://pdf", "adjuntos": []}
    mock_parsers.parsear_pagina_documento.return_value = data_esperada

    resultado = scraper_tasks.raspar_contenido_documento(mock_session, "http://url/doc")

    assert resultado == data_esperada
    mock_session.get.assert_called_with("http://url/doc")
