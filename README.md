# **Scraping SIPED \- Intranet PJ Santa Cruz**

Herramienta automatizada para la extracción y gestión de expedientes del sistema SIPED (Intranet del Poder Judicial de la Provincia de Santa Cruz).

## **1\. Arquitectura y Visión General**

El sistema está diseñado para operar de manera asíncrona, separando la interfaz de usuario de las tareas de extracción intensivas.

* **Aplicación Web (Flask):** Expone la interfaz gráfica y la API para iniciar las búsquedas y descargas.  
* **Gestor de Colas (Celery):** Procesa los trabajos de scraping en segundo plano para no bloquear la ejecución de la aplicación principal.  
* **Broker de Mensajes (Redis):** Actúa como intermediario para la gestión de tareas entre Flask y Celery.  
* **Almacenamiento:** Los datos extraídos se persisten en archivos locales estructurados y en disco.

## **2\. Estructura de Datos (Namespaces)**

El sistema organiza los archivos descargados por usuario de SIPED para evitar conflictos de concurrencia y sobreescritura. La carpeta raíz para persistencia es datos\_usuarios/.

* datos\_usuarios/\<CUIL\_USUARIO\>/expedientes\_completos.csv: Índice principal de expedientes.  
* datos\_usuarios/\<CUIL\_USUARIO\>/movimientos\_expedientes/: Archivos CSV con los movimientos de cada causa procesada.  
* datos\_usuarios/\<CUIL\_USUARIO\>/documentos\_expedientes/: Archivos PDF de las actuaciones, descargados y consolidados.

## **3\. Despliegue con Docker (Recomendado)**

La forma estandarizada de levantar el sistema en cualquier plataforma es mediante Docker, garantizando el correcto aislamiento de los servicios web, worker y redis.

### **Requisitos Previos**

* Docker y Docker Compose instalados en el sistema operativo.

### **Ejecución (Linux, macOS y Windows)**

1. Clonar el repositorio.  
2. Crear y configurar el archivo .env en la raíz del proyecto.  
3. Construir e iniciar los servicios en segundo plano:

docker compose up \-d \--build

La aplicación web estará operativa en http://localhost:5000.  
Para visualizar y auditar los registros del sistema:

docker compose logs \-f

## **4\. Entorno de Desarrollo Local**

Para tareas de desarrollo o ejecución sin Docker, el proyecto estandariza el uso de **uv** para la creación del entorno virtual y la sincronización de paquetes.

### **Requisitos Previos Generales**

* Python 3.10 o superior.  
* uv instalado en el sistema.  
* Servidor Redis en ejecución (puerto 6379).

### **Instrucciones para Linux y macOS**

1. **Crear el entorno virtual e instalar dependencias:**

   uv sync  
   *(Nota: Si el proyecto temporalmente carece de pyproject.toml, utilice uv venv, active el entorno y ejecute uv pip install \-r requirements.txt)*  
2. **Activar el entorno virtual:**

   source .venv/bin/activate  
3. **Iniciar los servicios (requiere terminales independientes):**  
   * Servidor Redis: redis-server  
   * Trabajador Celery: celery \-A tasks.celery\_app worker \--loglevel=info  
   * Aplicación Flask: python app.py

### **Instrucciones para Windows**

1. **Crear el entorno virtual e instalar dependencias:**

   uv sync  
2. **Activar el entorno virtual:**

   .venv\\Scripts\\activate  
3. **Iniciar los servicios (requiere terminales independientes):**  
   * Servidor Redis: Se requiere ejecutar Redis mediante WSL2 (Windows Subsystem for Linux) o mediante contenedor Docker, dado que Redis carece de soporte nativo oficial para Windows.  
   * Trabajador Celery: Por limitaciones del sistema de procesos en Windows, se debe ejecutar Celery utilizando el pool solo:

     celery \-A tasks.celery\_app worker \--loglevel=info \--pool=solo  
   * Aplicación Flask: python app.py

## **5\. Ejecución Manual (CLI)**

El sistema provee interfaces de línea de comandos para aislar la ejecución de fases específicas de extracción. Estos módulos interactivos requerirán las credenciales de acceso (Cuil/DNI) para inicializar el contenedor de datos correspondiente.  
Requieren el entorno virtual activo previamente:

* python \-m script.cli\_lista\_expedientes  
* python \-m script.cli\_movimientos  
* python \-m script.cli\_movimientos\_pdf  
* python \-m script.cli\_un\_expediente