# Manual de Administración del Sistema SIPED

Este documento contiene las especificaciones técnicas, directrices de infraestructura y procedimientos operativos necesarios para el despliegue, configuración y mantenimiento del Sistema Integrado de Extracción y Consolidación de Expedientes (SIPED).

## 1. Requisitos del Entorno

Para garantizar la correcta ejecución del sistema y la paridad de entornos, el host de destino debe cumplir con los siguientes requisitos mínimos:

* **Sistema Operativo:** Linux (distribuciones basadas en Arch Linux o complementarias con soporte Docker).
* **Motor de Contenedores:** Docker Engine versión 20.10 o superior.
* **Orquestación:** Docker Compose versión 2.0 o superior.
* **Gestión de Dependencias (Desarrollo):** uv versión 0.1.0 o superior.
* **Almacenamiento:** Espacio disponible en disco para el volumen persistente de datos de usuarios (`datos_usuarios/`), con permisos de lectura y escritura para el UID ejecutor del contenedor.

## 2. Arquitectura de Infraestructura

El sistema se compone de tres servicios principales aislados y conectados mediante una red virtual interna:

1.  **Servicio Web (Flask):** Actúa como el controlador de la interfaz de usuario. Expone el puerto `5000` y se encarga del manejo de sesiones de usuario, auditoría ligera y el despacho de tareas de scraping hacia la cola.
2.  **Broker de Mensajería (Redis):** Instancia en memoria encargada de administrar la cola de tareas asíncronas y almacenar los estados temporales de Celery. Opera internamente en el puerto `6379`.
3.  **Proceso de Ejecución (Celery Worker):** Consumidor asíncrono que ejecuta las tareas intensivas de red contra la intranet judicial, procesa el almacenamiento local de archivos CSV y fusiona los documentos binarios en PDFs consolidados.

## 3. Configuración de Variables de Entorno

La configuración operacional del sistema se administra mediante un archivo `.env` localizado en la raíz del proyecto. Este archivo debe ser creado antes de iniciar los contenedores.

| Variable | Descripción | Valor de Referencia / Sugerido |
| :--- | :--- | :--- |
| `FLASK_SECRET_KEY` | Clave criptográfica para la firma segura de cookies de sesión web. | Cadena alfanumérica compleja generada de forma aleatoria. |
| `REDIS_URL` | Dirección de red para la conexión con el broker de Celery. | `redis://redis:6379/0` |
| `SQLALCHEMY_DATABASE_URI` | Ruta de conexión para el motor de base de datos relacional. | `sqlite:////app/datos_usuarios/siped.db` |

*Nota de seguridad: Nunca incluya credenciales de producción ni claves secretas directamente en el archivo `config.py` o dentro del control de versiones.*

## 4. Procedimientos de Despliegue

### 4.1. Construcción e Inicialización
Para compilar las imágenes locales e iniciar la pila completa de servicios en modo desasistido (detached mode), ejecute el siguiente comando desde la raíz del proyecto:

```bash
docker-compose up -d --build
```

### 4.2. Detención de los Servicios
Para pausar la ejecución de los contenedores manteniendo intactos los datos almacenados en los volúmenes persistentes y el estado de la base de datos local:

```bash
docker-compose stop
```

Para remover por completo los contenedores, redes virtuales y liberar los recursos del sistema:

```bash
docker-compose down
```

### 4.3. Auditoría y Monitoreo de Registros (Logs)
El sistema centraliza los flujos de logs para facilitar el diagnóstico de errores de red o excepciones en el parsing:

* **Logs generales de la infraestructura:** `docker-compose logs -f`
* **Logs específicos del motor de scraping (Worker):** `docker-compose logs -f worker`
* **Logs del servidor de aplicaciones web (Flask):** `docker-compose logs -f web`

## 5. Mantenimiento y Solución de Problemas

### 5.1. Persistencia de Datos
Toda la información extraída (listas maestras en CSV, historiales de movimientos y PDFs consolidados) se almacena bajo una estructura jerárquica segregada por usuario dentro del directorio `datos_usuarios/` en el host. Asegure la ejecución de copias de seguridad (backups) periódicas sobre este directorio.

### 5.2. Bloqueos de Red o Timeouts
En caso de detectar fallas consecutivas en las tareas de extracción, verifique que las cabeceras definidas en `config.py` (`BROWSER_HEADERS`) no hayan sido filtradas por el firewall perimetral de la intranet judicial y que la resolución DNS interna del contenedor permita el acceso a los dominios del Poder Judicial.

