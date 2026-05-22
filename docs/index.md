# Documentación Técnica y Operativa del Sistema SIPED

El **Sistema Integrado de Extracción y Consolidación de Expedientes (SIPED)** es una plataforma automatizada para la interacción con portales judiciales. Su función principal consiste en la extracción estructurada de metadatos, movimientos y documentos, consolidando la información en formatos estandarizados (CSV y PDF) para su almacenamiento y gestión local.

La presente documentación se estructura en tres ejes principales, delineados según el rol y las responsabilidades del lector:

## Manual de Usuario
Destinado a los operadores del sistema. Contiene las directrices para el uso de la interfaz web, la ejecución de las fases de actualización de expedientes, la descarga de documentos consolidados y la realización de búsquedas masivas.
**[Acceder al Manual de Usuario &rarr;](usuario/flujo.md)**

## Manual de Administrador
Orientado al personal de infraestructura y operaciones. Detalla los procedimientos para la instalación del sistema, el despliegue de contenedores Docker, la configuración de variables de entorno y el mantenimiento continuo de los servicios.
**[Acceder al Manual de Administrador &rarr;](admin/despliegue.md)**

## Guía del Desarrollador
Dirigido a ingenieros de software e integrantes del equipo técnico. Proporciona la documentación de la arquitectura interna, el funcionamiento de las tareas asíncronas administradas por Celery, el uso de las herramientas de línea de comandos (CLI) y la referencia exhaustiva de la API interna de Python.
**[Acceder a la Guía del Desarrollador &rarr;](dev/arquitectura.md)**

---
*Nota: Esta documentación técnica se genera de manera automatizada a partir del código fuente para garantizar su exactitud y vigencia temporal.*
