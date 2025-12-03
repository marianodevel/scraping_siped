import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
import config

# --- Tests para limpiar_nombre_archivo ---


def test_limpiar_nombre_archivo_basico():
    nombre = "Expediente: 123/2023"
    limpio = utils.limpiar_nombre_archivo(nombre)
    # Debe reemplazar / por - y eliminar : y espacios extra
    assert limpio == "Expediente 123-2023"


def test_limpiar_nombre_archivo_caracteres_prohibidos():
    nombre = 'Archivo con "comillas" y *asteriscos* y <flechas>'
    limpio = utils.limpiar_nombre_archivo(nombre)
    assert limpio == "Archivo con comillas y asteriscos y flechas"


def test_limpiar_nombre_archivo_vacio():
    assert utils.limpiar_nombre_archivo(None) == "SIN_NOMBRE"
    assert utils.limpiar_nombre_archivo("") == "SIN_NOMBRE"


# --- Tests para obtener_ruta_usuario (NUEVO) ---


def test_obtener_ruta_usuario():
    """
    Verifica que se genere la ruta correcta basada en la config y el usuario.
    """
    username = "test_user"
    expected_path = os.path.join(config.DATA_ROOT_DIR, "test_user")

    with patch("os.makedirs") as mock_makedirs:
        ruta = utils.obtener_ruta_usuario(username)

        assert ruta == expected_path
        # Verifica que intente crear la carpeta
        mock_makedirs.assert_called_with(expected_path, exist_ok=True)


def test_obtener_ruta_usuario_none():
    """Verifica el fallback a 'default' si no hay usuario."""
    with patch("os.makedirs"):
        ruta = utils.obtener_ruta_usuario(None)
        assert os.path.join(config.DATA_ROOT_DIR, "default") in ruta


# --- Tests para manejo de CSV (usando tmp_path de pytest) ---


def test_guardar_y_leer_csv(tmp_path):
    """
    Verifica que se pueda guardar una lista de dicts en un CSV y luego leerla.
    Usamos tmp_path fixture de pytest para no ensuciar el disco real.
    """
    datos = [
        {"col1": "dato1", "col2": "dato2"},
        {"col1": "dato3", "col2": "dato4"},
    ]

    nombre_archivo = "test.csv"
    # Convertimos el path de pytest a string
    directorio_temporal = str(tmp_path)

    # 1. Guardar
    utils.guardar_a_csv(datos, nombre_archivo, subdirectory=directorio_temporal)

    ruta_completa = os.path.join(directorio_temporal, nombre_archivo)
    assert os.path.exists(ruta_completa)

    # 2. Leer
    datos_leidos = utils.leer_csv_a_diccionario(ruta_completa)

    assert len(datos_leidos) == 2
    assert datos_leidos[0]["col1"] == "dato1"
    assert datos_leidos[1]["col2"] == "dato4"


def test_leer_csv_inexistente():
    """Verifica que devuelva None si el archivo no existe, sin explotar."""
    resultado = utils.leer_csv_a_diccionario("archivo_que_no_existe_12345.csv")
    assert resultado is None


# --- Tests para fusión de PDFs ---


@patch("utils.PdfWriter")
@patch("utils.PdfReader")
@patch("os.listdir")
def test_fusionar_pdfs(mock_listdir, mock_reader, mock_writer):
    """
    Testeamos la lógica de fusión mockeando las librerías de PDF
    para no necesitar archivos PDF reales.
    """
    # Configuración del escenario
    directorio_origen = "/tmp/pdfs"
    archivo_destino = "/tmp/salida.pdf"

    # Simulamos que hay 2 archivos PDF en el directorio
    mock_listdir.return_value = ["doc1.pdf", "doc2.pdf", "imagen.jpg"]

    # Simulamos el objeto PdfWriter y PdfReader
    writer_instance = mock_writer.return_value
    reader_instance = mock_reader.return_value

    # Simulamos que cada PDF tiene 1 página
    reader_instance.pages = [MagicMock()]

    with patch("builtins.open", new_callable=MagicMock):
        utils.fusionar_pdfs(directorio_origen, archivo_destino)

    # Verificaciones
    # 1. Debe haber intentado leer solo los archivos .pdf (2 veces)
    assert mock_reader.call_count == 2

    # 2. Debe haber agregado páginas al writer (2 veces, una por cada doc)
    assert writer_instance.add_page.call_count == 2

    # 3. Debe haber escrito el resultado final una vez
    assert writer_instance.write.call_count == 1
