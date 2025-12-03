import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from script import cli_lista_expedientes
from script import cli_movimientos
from script import cli_movimientos_pdf
from script import cli_un_expediente

# --- Tests para Script 1 (Lista Maestra) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_lista_expedientes.session_manager")
@patch("script.cli_lista_expedientes.scraper_tasks")
@patch("script.cli_lista_expedientes.utils")
def test_cli_fase_1_flujo_exitoso(
    mock_utils, mock_tasks, mock_sm, mock_pass, mock_input
):
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}
    mock_tasks.raspar_lista_expedientes.return_value = [{"exp": "1"}]
    mock_utils.obtener_ruta_usuario.return_value = "/tmp/user_path"

    cli_lista_expedientes.main_lista()

    # Verificamos que guarde en el subdirectorio del usuario
    mock_utils.guardar_a_csv.assert_called()
    args, kwargs = mock_utils.guardar_a_csv.call_args
    assert kwargs["subdirectory"] == "/tmp/user_path"


# --- Tests para Script 2 (Movimientos) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_movimientos.session_manager")
@patch("script.cli_movimientos.scraper_tasks")
@patch("script.cli_movimientos.utils")
def test_cli_fase_2_flujo_exitoso(
    mock_utils, mock_tasks, mock_sm, mock_pass, mock_input
):
    # Setup
    mock_utils.leer_csv_a_diccionario.return_value = [
        {"expediente": "100/23", "caratula": "A"}
    ]
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}
    mock_utils.obtener_ruta_usuario.return_value = "/tmp/user_path"

    with patch("os.path.exists", return_value=False):
        mock_tasks.raspar_movimientos_de_expediente.return_value = [{"mov": "1"}]

        cli_movimientos.main_movimientos()

        mock_tasks.raspar_movimientos_de_expediente.assert_called()
        # Verificar guardado en carpeta correcta
        mock_utils.guardar_a_csv.assert_called()
        args, kwargs = mock_utils.guardar_a_csv.call_args
        assert "/tmp/user_path" in kwargs["subdirectory"]


# --- Tests para Script 3 (Documentos - Wrapper) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_movimientos_pdf.session_manager")
@patch("script.cli_movimientos_pdf.ejecutar_fase_3_documentos")
def test_cli_fase_3_delegacion(mock_fase_3, mock_sm, mock_pass, mock_input):
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}

    cli_movimientos_pdf.main()

    # CRÍTICO: Verificar que se pasa el username
    mock_fase_3.assert_called_with(cookies={"cookie": "si"}, username="usuario_cli")


# --- Tests para Script 4 (Un Expediente) ---


@patch("builtins.input", side_effect=["usuario_cli", "1"])  # 1. Usuario, 2. Selección
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_un_expediente.session_manager")
@patch("script.cli_un_expediente.scraper_tasks")
@patch("script.cli_un_expediente.utils")
@patch("script.cli_un_expediente.os.makedirs")
@patch("script.cli_un_expediente.os.path.exists")
def test_cli_un_expediente_flujo_exitoso(
    mock_exists, mock_makedirs, mock_utils, mock_tasks, mock_sm, mock_pass, mock_input
):
    mock_utils.leer_csv_a_diccionario.return_value = [
        {"expediente": "100/23", "caratula": "TEST"}
    ]
    mock_utils.limpiar_nombre_archivo.return_value = "clean"
    mock_utils.obtener_ruta_usuario.return_value = "/tmp/user_path"
    mock_sm.autenticar_en_siped.return_value = {"cookie": "ok"}

    mock_tasks.raspar_movimientos_de_expediente.return_value = [
        {"link_escrito": "http://doc"}
    ]
    mock_tasks.raspar_contenido_documento.return_value = {
        "url_pdf_principal": "http://pdf",
        "adjuntos": [],
    }

    mock_exists.return_value = False
    mock_tasks.descargar_archivo.return_value = True

    cli_un_expediente.main()

    mock_utils.guardar_a_csv.assert_called()
    mock_utils.fusionar_pdfs.assert_called()
