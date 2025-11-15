import gestor_almacenamiento
import config
import os


# 'fs' es una fixture mágica de pytest-fs.
# Crea un sistema de archivos falso para esta prueba.
def test_listar_archivos_pdf(fs):
    # 1. Aseguramos que el directorio está vacío
    fs.create_dir(config.DOCUMENTOS_OUTPUT_DIR)
    assert gestor_almacenamiento.listar_archivos_pdf() == []

    # 2. Creamos archivos falsos
    fs.create_file(os.path.join(config.DOCUMENTOS_OUTPUT_DIR, "expediente_B.pdf"))
    fs.create_file(os.path.join(config.DOCUMENTOS_OUTPUT_DIR, "expediente_A.pdf"))
    fs.create_file(os.path.join(config.DOCUMENTOS_OUTPUT_DIR, "otro_archivo.txt"))
    fs.create_file(
        os.path.join(config.DOCUMENTOS_OUTPUT_DIR, "subcarpeta/doc.pdf")
    )  # No debe listarlo

    # 3. Probamos la función
    pdfs = gestor_almacenamiento.listar_archivos_pdf()

    assert len(pdfs) == 2
    # Verifica que solo lista PDFs del directorio raíz y los ordena
    assert pdfs == ["expediente_A.pdf", "expediente_B.pdf"]
