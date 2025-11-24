# Scraping SIPED - Intranet PJ Santa Cruz

Herramienta automatizada para la extracción y gestión de expedientes del sistema SIPED (Intranet del Poder Judicial de Santa Cruz). Utiliza Flask para la interfaz web, Celery para el procesamiento en segundo plano y scripts modulares para ejecución manual.

## Requisitos Previos

1.  **Python 3.8** o superior.
2.  **Redis Server**: Motor de base de datos en memoria para la cola de tareas de Celery.
    * *Linux:* `sudo apt install redis-server`
    * *Windows:* Usar WSL2 o Docker.

## Instalación

1.  **Clonar y preparar entorno:**
    ```bash
    git clone <url-del-repositorio>
    cd scraping_siped
    python -m venv .venv
    source .venv/bin/activate  # En Windows: .venv\Scripts\activate
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución de la Aplicación Web

Necesitas tres terminales abiertas:

1.  **Redis:** Asegúrate de que esté corriendo (`redis-server`).
2.  **Worker (Celery):** Procesa las tareas en segundo plano.
    ```bash
    celery -A tasks.celery_app worker --loglevel=info
    ```
3.  **Web (Flask):** Interfaz de usuario.
    ```bash
    python app.py
    ```
    Accede a: `http://127.0.0.1:5001`

## Ejecución Manual (Scripts CLI)

Si prefieres ejecutar el proceso fase por fase desde la terminal (sin interfaz web), utiliza los scripts modulares. Te pedirán tus credenciales interactivamente.

**Nota:** Ejecútalos como módulos desde la raíz del proyecto.

* **Fase 1: Obtener Lista Maestra**
    Descarga la lista de expedientes a `expedientes_completos.csv`.
    ```bash
    python -m script.1_get_lista_expedientes
    ```

* **Fase 2: Obtener Movimientos**
    Lee el CSV maestro y descarga los movimientos individuales.
    ```bash
    python -m script.2_get_movimientos
    ```

* **Fase 3: Descargar y Consolidar PDFs**
    Descarga los documentos de cada movimiento y genera un PDF unificado por expediente.
    ```bash
    python -m script.3_get_movimientos_pdf
    ```

## Estructura de Datos

* `expedientes_completos.csv`: Índice principal.
* `movimientos_expedientes/`: Archivos CSV con los movimientos de cada causa.
* `documentos_expedientes/`: Carpetas con PDFs descargados y el PDF consolidado final.
