# Scraping SIPED - Intranet PJ Santa Cruz

Herramienta automatizada para la extracción y gestión de expedientes del sistema SIPED (Intranet del Poder Judicial de Santa Cruz). La aplicación utiliza Flask para la interfaz web, Celery para el procesamiento de tareas en segundo plano y Redis como gestor de colas.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

1.  **Python 3.8** o superior.
2.  **Redis Server**: Es indispensable para que funcionen las tareas en segundo plano (Celery).
    * *Linux (Debian/Ubuntu):* `sudo apt install redis-server`
    * *Mac:* `brew install redis`
    * *Windows:* Se recomienda usar WSL2 o una imagen de Docker para Redis.

## Instalación

Sigue estos pasos para configurar el entorno localmente:

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd scraping_siped
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Crear el entorno
    python -m venv venv

    # Activar en Linux/Mac
    source venv/bin/activate

    # Activar en Windows
    venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución Local

Para correr la aplicación necesitas tres terminales abiertas (o procesos en segundo plano):

### 1. Iniciar Redis
Asegúrate de que el servidor de Redis esté corriendo.
```bash
redis-server
```

### 2. Iniciar el Worker (Celery)
En una nueva terminal (con el entorno virtual activado), ejecuta el gestor de tareas:
```bash
celery -A tasks.celery_app worker --loglevel=info
```


### 3. Iniciar la Aplicación Web (Flask)
En otra terminal (con el entorno virtual activado), inicia el servidor web:

```python app.py```


### 4. Uso
Una vez iniciados los servicios, abre tu navegador y ve a:

```127.0.0.1:5001```

Se te presentará una pantalla de Inicio de Sesión.
Ingresa tu Usuario (DNI/Cuit) y Contraseña de la Intranet del Poder Judicial.
Una vez logueado, podrás iniciar las fases de scraping desde el panel de control.

### 5. Ejecución: Modos Alternativos (Scripts CLI)
Si prefieres no utilizar la interfaz web o necesitas depurar el proceso, puedes utilizar los scripts ubicados en la carpeta script/.

#### Opción A: Script Todo-en-Uno (Legacy)
El archivo siped3.py es un script independiente que realiza todo el proceso de extracción de forma lineal. Ubicación: script/siped3.py

```
python script/siped3.py
```

#### Opción B: Ejecución Modular por Pasos
Si deseas ejecutar el proceso fase por fase manualmente, utiliza los scripts numerados. Nota importante: Dado que estos scripts dependen de archivos en la carpeta raíz (config.py, utils.py, etc.), deben ejecutarse como módulos desde la raíz del proyecto usando python -m.

##### Fase 1: Obtener Lista Maestra Genera el archivo lista_expedientes.csv.

``` 
python -m script.1_get_lista_expedientes
```

##### Fase 2: Obtener Movimientos Lee la lista maestra y descarga los movimientos en CSV individuales.

```
python -m script.2_get_movimientos
```

##### Fase 3: Descargar Textos y Generar PDF Lee los CSV de movimientos, descarga el contenido de los escritos y compila un PDF por expediente.

```
python -m script.3_get_movimientos_texto
```

### 6. Estructura del Proyecto
app.py: Servidor web Flask y rutas.

tasks.py: Definición de tareas asíncronas para Celery.

scraper.py: Lógica principal de scraping.

templates/: Interfaz de usuario (HTML).

logs/: Archivos de registro de actividad.

### 7. Licencia
