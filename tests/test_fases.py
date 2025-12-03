import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Agregamos el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importamos las fases
from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos
from fases.fase_unico import ejecutar_fase_unico
import config

# --- Tests para FASE 1 (Lista) ---


@patch("fases.fase_1.utils")
@patch("fases.fase_1.scraper_tasks")
@patch("utils.session_manager.crear_sesion_con_cookies")
def test_fase_1_exito(mock_crear_sesion, mock_tasks, mock_utils):
    mock_sesion = MagicMock()
    mock_crear_sesion.return_value = mock_sesion

    mock_tasks.raspar_lista_expedientes.return_value = [{"exp": "1"}, {"exp": "2"}]

    cookies_dummy = {"session": "test"}
    username_dummy = "usuario_test"

    # Mock de ruta usuario
    ruta_usuario_mock = "/tmp/datos_usuarios/usuario_test"
    mock_utils.obtener_ruta_usuario.return_value = ruta_usuario_mock

    # EJECUCIÓN con username
    mensaje = ejecutar_fase_1_lista(cookies_dummy, username_dummy)

    assert "Total: 2" in mensaje

    # VERIFICACIÓN: debe usar el subdirectorio del usuario
    mock_utils.guardar_a_csv.assert_called_with(
        [{"exp": "1"}, {"exp": "2"}],
        config.LISTA_EXPEDIENTES_CSV,
        subdirectory=ruta_usuario_mock,
    )


@patch("fases.fase_1.scraper_tasks")
@patch("utils.session_manager.crear_sesion_con_cookies")
@patch("fases.fase_1.utils")
def test_fase_1_sin_resultados(mock_utils, mock_crear_sesion, mock_tasks):
    mock_crear_sesion.return_value = MagicMock()
    mock_tasks.raspar_lista_expedientes.return_value = []

    # Mock ruta
    mock_utils.obtener_ruta_usuario.return_value = "/tmp/dummy"

    mensaje = ejecutar_fase_1_lista({}, "user")

    assert "No se encontraron expedientes" in mensaje


# --- Tests para FASE 2 (Movimientos) ---


@patch("fases.fase_2.utils")
@patch("fases.fase_2.scraper_tasks")
@patch("utils.session_manager.crear_sesion_con_cookies")
def test_fase_2_flujo_normal(mock_crear_sesion, mock_tasks, mock_utils):
    mock_crear_sesion.return_value = MagicMock()

    # Configuración de mocks
    mock_utils.leer_csv_a_diccionario.return_value = [
        {"expediente": "100/23", "caratula": "TEST"}
    ]
    mock_utils.limpiar_nombre_archivo.return_value = "clean_name"

    ruta_usuario_mock = "/tmp/datos_usuarios/user"
    mock_utils.obtener_ruta_usuario.return_value = ruta_usuario_mock

    # Mockeamos os.path.exists dentro de fase_2
    with patch("fases.fase_2.os.path.exists", return_value=False):
        with patch("fases.fase_2.os.makedirs"):  # Mock makedirs
            mock_tasks.raspar_movimientos_de_expediente.return_value = [{"mov": "uno"}]

            # EJECUCIÓN
            mensaje = ejecutar_fase_2_movimientos({}, "user")

            assert "Total de movimientos descargados" in mensaje

            # Verificar que guarda en la carpeta de movimientos DENTRO del usuario
            expected_dir = os.path.join(
                ruta_usuario_mock, config.MOVIMIENTOS_OUTPUT_DIR
            )
            mock_utils.guardar_a_csv.assert_called()
            # Chequeamos args de la llamada
            args, kwargs = mock_utils.guardar_a_csv.call_args
            assert kwargs["subdirectory"] == expected_dir


@patch("fases.fase_2.utils")
@patch("utils.session_manager.crear_sesion_con_cookies")
def test_fase_2_sin_csv_maestro(mock_crear_sesion, mock_utils):
    mock_crear_sesion.return_value = MagicMock()
    mock_utils.leer_csv_a_diccionario.return_value = None
    mock_utils.obtener_ruta_usuario.return_value = "/tmp/user"

    mensaje = ejecutar_fase_2_movimientos({}, "user")

    assert "Error: No se encontró el archivo maestro" in mensaje


# --- Tests para FASE 3 (Documentos y PDF) ---


@patch("fases.fase_3.utils")
@patch("fases.fase_3.scraper_tasks")
@patch("utils.session_manager.crear_sesion_con_cookies")
@patch("fases.fase_3.os.makedirs")
@patch("fases.fase_3.os.listdir")
def test_fase_3_flujo_completo(
    mock_listdir, mock_makedirs, mock_crear_sesion, mock_tasks, mock_utils
):
    mock_crear_sesion.return_value = MagicMock()

    ruta_usuario_mock = "/tmp/user"
    mock_utils.obtener_ruta_usuario.return_value = ruta_usuario_mock

    # 1. CSVs
    mock_utils.leer_csv_a_diccionario.side_effect = [
        [{"expediente": "100/23", "caratula": "TEST"}],  # Maestro
        [{"link_escrito": "http://doc"}],  # Movimientos
    ]
    mock_utils.limpiar_nombre_archivo.return_value = "clean"

    # 2. Scraping
    mock_tasks.raspar_contenido_documento.return_value = {
        "url_pdf_principal": "http://pdf_main",
        "adjuntos": [],
    }

    # 3. SETUP LISTDIR
    mock_listdir.return_value = ["01_principal.pdf"]

    with patch("fases.fase_3.os.path.exists", return_value=False):
        # EJECUCIÓN
        mensaje = ejecutar_fase_3_documentos({}, "user")

        mock_tasks.raspar_contenido_documento.assert_called()
        mock_tasks.descargar_archivo.assert_called()
        mock_utils.fusionar_pdfs.assert_called()
        assert "completado" in mensaje


# --- Tests para FASE ÚNICA (Nuevo) ---


@patch("fases.fase_unico.utils")
@patch("fases.fase_unico.scraper_tasks")
@patch("utils.session_manager.crear_sesion_con_cookies")
@patch("fases.fase_unico.os.makedirs")
@patch("fases.fase_unico.os.path.exists")
@patch("fases.fase_unico.os.remove")
def test_fase_unico_exito(
    mock_remove,
    mock_exists,
    mock_makedirs,
    mock_crear_sesion,
    mock_tasks,
    mock_utils,
):
    mock_crear_sesion.return_value = MagicMock()

    ruta_usuario_mock = "/tmp/user"
    mock_utils.obtener_ruta_usuario.return_value = ruta_usuario_mock

    # 1. Mock de Lista Maestra
    mock_utils.leer_csv_a_diccionario.return_value = [
        {"expediente": "100/23", "caratula": "TEST_UNICO"}
    ]
    mock_utils.limpiar_nombre_archivo.return_value = "clean_unico"

    # 2. Mock de Scraping de Movimientos
    mock_tasks.raspar_movimientos_de_expediente.return_value = [
        {"link_escrito": "http://doc_unico"}
    ]

    # 3. Mock de Scraping de Documento
    mock_tasks.raspar_contenido_documento.return_value = {
        "url_pdf_principal": "http://pdf_main_unico",
        "adjuntos": [],
    }

    # 4. Mock de Existencia
    mock_exists.return_value = False
    mock_tasks.descargar_archivo.return_value = True

    # EJECUCIÓN
    mensaje = ejecutar_fase_unico({}, "100/23", "user")

    assert "Proceso completado para 100/23" in mensaje
    mock_utils.guardar_a_csv.assert_called()
    mock_tasks.descargar_archivo.assert_called()
    mock_utils.fusionar_pdfs.assert_called()
