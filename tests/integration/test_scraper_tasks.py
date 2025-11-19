# tests/integration/test_scraper_tasks.py
import pytest
from unittest.mock import MagicMock
import scraper_tasks
from tests.conftest import MockResponse


def test_raspar_lista_expedientes_flujo(
    html_lista_expedientes_pagina_1, html_lista_expedientes_pagina_final
):
    """
    Prueba que el scraper recorra las páginas y extraiga expedientes
    simulando las respuestas HTTP de la sesión.
    """
    # 1. Crear un Mock de Session
    mock_session = MagicMock()

    # 2. Configurar side_effect para devolver diferentes HTML según los params
    def side_effect_get(url, params=None, **kwargs):
        # Si pide la página inicial (inicio=0)
        if params and params.get("inicio") == 0:
            return MockResponse(html_lista_expedientes_pagina_1)
        # Si pide la página siguiente (inicio=10) - simulamos que es la final
        elif params and params.get("inicio") == 10:
            return MockResponse(html_lista_expedientes_pagina_final)
        return MockResponse("<html></html>", 404)

    mock_session.get.side_effect = side_effect_get

    # 3. Ejecutar la función real
    resultados = scraper_tasks.raspar_lista_expedientes(mock_session)

    # 4. Validar resultados
    # Debería encontrar 1 expediente en la pag 1 y detenerse en la pag 2
    assert len(resultados) == 1
    assert resultados[0]["expediente"] == "EXP-100/2025"

    # Verificar que se llamó 2 veces (página 0 y página 10)
    assert mock_session.get.call_count == 2


def test_raspar_contenido_documento(html_pagina_documento_pdfs):
    """Prueba la extracción de datos de un documento individual."""
    mock_session = MagicMock()
    mock_session.get.return_value = MockResponse(html_pagina_documento_pdfs)

    data = scraper_tasks.raspar_contenido_documento(mock_session, "http://url-falsa")

    assert data is not None
    assert data["expediente_nro"] == "EXP-100/2025"
    assert "pdfabogadoanterior.php" in data["url_pdf_principal"]
    assert len(data["adjuntos"]) == 1
