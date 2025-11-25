import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Agregamos el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importamos los módulos con sus nuevos nombres estándar
from script import cli_lista_expedientes
from script import cli_movimientos
from script import cli_movimientos_pdf

# --- Tests para Script 1 (Lista Maestra) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_lista_expedientes.session_manager")
@patch("script.cli_lista_expedientes.scraper_tasks")
@patch("script.cli_lista_expedientes.utils")
def test_cli_fase_1_flujo_exitoso(
    mock_utils, mock_tasks, mock_sm, mock_pass, mock_input
):
    """
    Simula la ejecución de: python -m script.cli_lista_expedientes
    """
    # 1. Configuración de Mocks
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}
    mock_tasks.raspar_lista_expedientes.return_value = [{"exp": "1"}]

    # 2. Ejecutar el main del script
    cli_lista_expedientes.main_lista()

    # 3. Verificaciones
    # ¿Se autenticó con lo que ingresamos en los inputs mockeados?
    mock_sm.autenticar_en_siped.assert_called_with("usuario_cli", "password_cli")

    # ¿Se intentó guardar el CSV?
    mock_utils.guardar_a_csv.assert_called()


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_lista_expedientes.session_manager")
def test_cli_fase_1_auth_fallida(mock_sm, mock_pass, mock_input):
    """Verifica que el script se detenga si falla la autenticación."""
    mock_sm.autenticar_en_siped.return_value = None  # Login fallido

    # Capturamos stdout para verificar el mensaje de error
    with patch("builtins.print") as mock_print:
        cli_lista_expedientes.main_lista()

        # Verificar que imprimió error
        args, _ = mock_print.call_args
        assert "Error de autenticación" in args[0]


# --- Tests para Script 2 (Movimientos) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_movimientos.session_manager")
@patch("script.cli_movimientos.scraper_tasks")
@patch("script.cli_movimientos.utils")
def test_cli_fase_2_flujo_exitoso(
    mock_utils, mock_tasks, mock_sm, mock_pass, mock_input
):
    """
    Simula la ejecución de: python -m script.cli_movimientos
    """
    # 1. Configuración
    mock_utils.leer_csv_a_diccionario.return_value = [
        {"expediente": "100/23", "caratula": "A"}
    ]
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}

    # Mockeamos que el archivo de salida NO existe para que intente descargarlo
    with patch("os.path.exists", return_value=False):
        mock_tasks.raspar_movimientos_de_expediente.return_value = [{"mov": "1"}]

        # 2. Ejecutar
        cli_movimientos.main_movimientos()

        # 3. Verificaciones
        mock_tasks.raspar_movimientos_de_expediente.assert_called()
        mock_utils.guardar_a_csv.assert_called()


@patch("script.cli_movimientos.utils")
def test_cli_fase_2_sin_csv_maestro(mock_utils):
    """Verifica que aborte si no hay lista maestra."""
    mock_utils.leer_csv_a_diccionario.return_value = None

    with patch("builtins.print") as mock_print:
        cli_movimientos.main_movimientos()

        # Verificar mensaje de error
        call_args = mock_print.call_args[0][0]
        assert "No se encontró" in call_args


# --- Tests para Script 3 (Documentos - Wrapper) ---


@patch("builtins.input", return_value="usuario_cli")
@patch("getpass.getpass", return_value="password_cli")
@patch("script.cli_movimientos_pdf.session_manager")
@patch(
    "script.cli_movimientos_pdf.ejecutar_fase_3_documentos"
)  # Mockeamos la fase importada
def test_cli_fase_3_delegacion(mock_fase_3, mock_sm, mock_pass, mock_input):
    """
    El script 3 es diferente: importa la lógica desde 'fases.fase_3'.
    Testeamos solo que delegue correctamente.
    """
    mock_sm.autenticar_en_siped.return_value = {"cookie": "si"}

    cli_movimientos_pdf.main()

    # Verificamos que llamó a la función de la fase pasándole las cookies
    mock_fase_3.assert_called_with(cookies={"cookie": "si"})


@patch("builtins.input", return_value="")  # Usuario vacío
@patch("getpass.getpass", return_value="")
def test_cli_fase_3_datos_vacios(mock_pass, mock_input):
    """Verifica validación de inputs vacíos."""
    with patch("builtins.print") as mock_print:
        cli_movimientos_pdf.main()
        args, _ = mock_print.call_args
        assert "Error: Usuario y contraseña son obligatorios" in args[0]
