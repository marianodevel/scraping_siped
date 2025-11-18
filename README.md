\# Scraping SIPED \- Intranet PJ Santa Cruz

Herramienta automatizada para la extracción y gestión de expedientes del sistema SIPED (Intranet del Poder Judicial de Santa Cruz). La aplicación utiliza Flask para la interfaz web, Celery para el procesamiento de tareas en segundo plano y Redis como gestor de colas.

\#\# Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

1\.  \*\*Python 3.8\*\* o superior.  
2\.  \*\*Redis Server\*\*: Es indispensable para que funcionen las tareas en segundo plano (Celery).  
    \* *\*Linux (Debian/Ubuntu):\** \`sudo apt install redis-server\`  
    \* *\*Mac:\** \`brew install redis\`  
    \* *\*Windows:\** Se recomienda usar WSL2 o una imagen de Docker para Redis.

\#\# Instalación

Sigue estos pasos para configurar el entorno localmente:

1\.  \*\*Clonar el repositorio:\*\*  
    \`\`\`bash  
    git clone \<url-del-repositorio\>  
    cd scraping\_siped  
    \`\`\`

2\.  \*\*Crear y activar un entorno virtual:\*\*  
    \`\`\`bash  
    \# Crear el entorno  
    python \-m venv venv

    \# Activar en Linux/Mac  
    source venv/bin/activate

    \# Activar en Windows  
    venv\\Scripts\\activate  
    \`\`\`

3\.  \*\*Instalar dependencias:\*\*  
    \`\`\`bash  
    pip install \-r requirements.txt  
    \`\`\`

\#\# Ejecución Local

Para correr la aplicación necesitas tres terminales abiertas (o procesos en segundo plano):

\#\#\# 1\. Iniciar Redis  
Asegúrate de que el servidor de Redis esté corriendo.  
\`\`\`bash  
redis-server

### \#\#\#2. Iniciar el Worker (Celery)

En una nueva terminal (con el entorno virtual activado), ejecuta el gestor de tareas:

\`\`\`bash

celery \-A tasks.celery\_app worker \--loglevel=info

### 

### \#\#\#3. Iniciar la Aplicación Web (Flask)

En otra terminal (con el entorno virtual activado), inicia el servidor web:

\`\`\`python app.py

\#\#\#4.Uso

Una vez iniciados los servicios, abre tu navegador y ve a: https://www.google.com/search?q=http://127.0.0.1:5001

1. Se te presentará una pantalla de Inicio de Sesión.  
2. Ingresa tu Usuario (DNI/Cuit) y Contraseña de la Intranet del Poder Judicial.  
3. Una vez logueado, podrás iniciar las fases de scraping desde el panel de control.

\#\#\#5.Estructura del Proyecto

* app.py: Servidor web Flask y rutas.  
* tasks.py: Definición de tareas asíncronas para Celery.  
* scraper.py: Lógica principal de scraping.  
* templates/: Interfaz de usuario (HTML).  
* logs/: Archivos de registro de actividad.

## Disclaimer

## Licencia

