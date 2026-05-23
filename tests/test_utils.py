"""Pruebas unitarias completas y de alta cobertura para el módulo de utilidades."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
import config


class TestLimpiarNombreArchivo:
    """Batería de pruebas exhaustivas para la sanitización de nombres de archivos."""

    def test_limpiar_nombre_archivo_basico(self):
        """Valida que los nombres estándar y la sustitución de barras operen bien."""
        # La función reemplaza '/' por '-' y limpia caracteres ilegales
        assert utils.limpiar_nombre_archivo("Expediente 123/2023") == "Expediente 123-2023"

    def test_limpiar_nombre_archivo_caracteres_prohibidos(self):
        """Asegura la remoción estricta de caracteres prohibidos por el SO."""
        nombre = 'Archivo con comillas y *asteriscos* y <flechas>?'
        limpio = utils.limpiar_nombre_archivo(nombre)
        assert limpio == "Archivo con comillas y asteriscos y flechas"

    def test_limpiar_nombre_archivo_vacio(self):
        """Valida el fallback seguro ante strings vacíos o None."""
        assert utils.limpiar_nombre_archivo(None) == "SIN_NOMBRE"
        assert utils.limpiar_nombre_archivo("") == "SIN_NOMBRE"


class TestRutaUsuario:
    """Pruebas funcionales para la gestión de directorios de usuario."""

    def test_obtener_ruta_usuario(self):
        """Verifica la generación de la ruta correcta basada en la configuración."""
        username = "test_user"
        expected_path = os.path.join(config.DATA_ROOT_DIR, "test_user")

        with patch("os.makedirs") as mock_makedirs:
            ruta = utils.obtener_ruta_usuario(username)
            assert ruta == expected_path
            mock_makedirs.assert_called_with(expected_path, exist_ok=True)

    def test_obtener_ruta_usuario_none(self):
        """Verifica el fallback a 'default' ante ausencia de nombre de usuario."""
        with patch("os.makedirs"):
            ruta = utils.obtener_ruta_usuario(None)
            assert os.path.join(config.DATA_ROOT_DIR, "default") in ruta


class TestOperacionesCSV:
    """Pruebas intensivas de lectura y escritura CSV aisladas mediante tmp_path."""

    def test_guardar_y_leer_csv_completo(self, tmp_path):
        """Garantiza la persistencia e integridad de colecciones de datos en formato CSV."""
        datos = [
            {"col1": "dato1", "col2": "dato2"},
            {"col1": "dato3", "col2": "dato4"},
        ]
        nombre_archivo = "test.csv"
        directorio_temporal = str(tmp_path)

        utils.guardar_a_csv(datos, nombre_archivo, subdirectory=directorio_temporal)
        ruta_completa = os.path.join(directorio_temporal, nombre_archivo)
        assert os.path.exists(ruta_completa)

        datos_leidos = utils.leer_csv_a_diccionario(ruta_completa)
        assert len(datos_leidos) == 2
        assert datos_leidos[0]["col1"] == "dato1"
        assert datos_leidos[1]["col2"] == "dato4"

    def test_leer_csv_inexistente(self):
        """Valida la captura controlada de excepciones de archivos faltantes."""
        assert utils.leer_csv_a_diccionario("archivo_inexistente.csv") is None


class TestFusionPDFs:
    """Validación de la orquestación e integración al concatenar archivos PDF."""

    @patch("utils.PdfWriter")
    @patch("utils.PdfReader")
    @patch("os.listdir")
    def test_fusionar_pdfs_exitoso(self, mock_listdir, mock_reader, mock_writer):
        """Prueba que el ciclo recorra y escriba exclusivamente los archivos con extensión .pdf."""
        mock_listdir.return_value = ["doc1.pdf", "doc2.pdf", "imagen.jpg"]
        writer_instance = mock_writer.return_value
        reader_instance = mock_reader.return_value
        reader_instance.pages = [MagicMock()]

        with patch("builtins.open", new_callable=MagicMock):
            utils.fusionar_pdfs("/tmp/pdfs", "/tmp/salida.pdf")

        assert mock_reader.call_count == 2
        assert writer_instance.add_page.call_count == 2
        assert writer_instance.write.call_count == 1