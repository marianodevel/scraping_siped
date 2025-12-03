# Scraping SIPED - Intranet PJ Santa Cruz

Herramienta automatizada para la extracción y gestión de expedientes del sistema SIPED (Intranet del Poder Judicial de Santa Cruz).

## Estructura de Datos (Namespaces)

El sistema organiza los archivos descargados por usuario para evitar conflictos.
La carpeta raíz es `datos_usuarios/`.

* `datos_usuarios/<CUIL_USUARIO>/expedientes_completos.csv`: Índice principal.
* `datos_usuarios/<CUIL_USUARIO>/movimientos_expedientes/`: CSVs con movimientos.
* `datos_usuarios/<CUIL_USUARIO>/documentos_expedientes/`: PDFs descargados y consolidados.

## Instalación y Ejecución

1.  **Instalar dependencias:** `pip install -r requirements.txt`
2.  **Redis:** Asegúrate de que `redis-server` esté corriendo.
3.  **Worker:** `celery -A tasks.celery_app worker --loglevel=info`
4.  **Web:** `python app.py`

## Ejecución Manual (CLI)

Los scripts solicitarán tu usuario (Cuil/DNI) para leer y guardar los datos en tu carpeta personal correspondiente.

* `python -m script.cli_lista_expedientes`
* `python -m script.cli_movimientos`
* `python -m script.cli_movimientos_pdf`
* `python -m script.cli_un_expediente`
