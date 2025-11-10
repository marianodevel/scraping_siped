# Sistema de Extracción de Expedientes (scraping_siped)

Esta es una herramienta de automatización diseñada para asistir a profesionales en la consulta y descarga de expedientes y sus movimientos asociados desde la intranet del Poder Judicial de Santa Cruz (intranet.jussantacruz.gob.ar).

El sistema utiliza Python para simular la navegación, autenticación y paginación, y guarda los resultados en archivos CSV estructurados para su fácil consulta y análisis.

## ⚠️ Advertencia Legal

Esta herramienta está diseñada para automatizar el acceso a datos a los que el usuario ya tiene permiso de acceder mediante sus credenciales. El uso indebido de este software o cualquier violación de los términos de servicio de la plataforma es responsabilidad exclusiva del usuario.

## 📋 Requisitos Previos

Antes de comenzar, asegúrese de tener instalado el siguiente software en su sistema:

- Python 3.8 o superior
- Git (para clonar el repositorio)

### Verificación de Python

Abra una terminal (Terminal en macOS/Linux, Símbolo del sistema o PowerShell en Windows) y ejecute:
```bash
python3 --version
```

> En Windows, es posible que el comando sea `python --version`.

Si Python no está instalado, descárguelo desde [python.org](https://www.python.org) (para Windows/macOS) o instálelo a través del gestor de paquetes de su sistema (Linux).

## 🚀 Instalación

Siga estos pasos para configurar el entorno de trabajo.

### 1. Clonar el Repositorio

Abra su terminal, navegue al directorio donde desea instalar el proyecto y ejecute:
```bash
git clone [URL_DEL_REPOSITORIO]
cd scraping_siped
```

### 2. Crear un Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto.

**En macOS y Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**En Windows (Símbolo del sistema):**
```cmd
python -m venv venv
.\venv\Scripts\activate
```

Su terminal ahora debería mostrar `(venv)` al inicio de la línea.

### 3. Instalar Dependencias

Las librerías necesarias se listan en el archivo `requirements.txt`.

> **Nota:** Primero, asegúrese de crear un archivo llamado `requirements.txt` en la raíz de su proyecto con el siguiente contenido:
```txt
requests
beautifulsoup4
python-dotenv
```

Una vez que el archivo exista y el entorno virtual esté activado, instale las dependencias:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

El script requiere sus credenciales de acceso para autenticarse con la intranet.

1. Cree un archivo llamado `.env` en el directorio principal del proyecto (el mismo lugar donde se encuentra `config.py`)
2. Abra el archivo `.env` con un editor de texto y añada sus credenciales de la siguiente manera:
```env
USUARIO_INTRANET="su_usuario"
CONTRASENA_INTRANET="su_contraseña"
```

> Reemplace el texto con sus credenciales reales, manteniendo las comillas.

## ▶️ Ejecución

La ejecución del sistema está dividida en dos fases independientes.

### Fase 1: Descargar la Lista Maestra de Expedientes

Este script se conectará a la intranet, obtendrá la lista completa de expedientes asociados a su cuenta y la guardará en un único archivo CSV.

En su terminal (con el entorno virtual activado), ejecute:
```bash
python 1_get_expedientes.py
```

**Salida:** Este proceso creará el archivo `expedientes_completos.csv` en el directorio principal.

### Fase 2: Descargar los Movimientos de Cada Expediente

Este script leerá el archivo `expedientes_completos.csv` y procederá a visitar cada expediente, uno por uno, para descargar su lista de movimientos.

En su terminal, ejecute:
```bash
python 2_get_movimientos.py
```

**Salida:** Este proceso creará un nuevo directorio llamado `movimientos_expedientes/`. Dentro de esta carpeta, se generará un archivo CSV separado para cada expediente, nombrado con su número y carátula para fácil identificación.

> **Nota:** Si la Fase 2 se interrumpe, puede volver a ejecutarla. El script está programado para detectar los archivos CSV que ya existen y saltará los expedientes que ya han sido procesados.

## 📁 Estructura de Archivos
```
scraping_siped/
├── 1_get_expedientes.py
├── 2_get_movimientos.py
├── config.py
├── requirements.txt
├── .env (crear manualmente)
├── expedientes_completos.csv (generado)
└── movimientos_expedientes/ (directorio generado)
    ├── expediente_1.csv
    ├── expediente_2.csv
    └── ...
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abra un issue o envíe un pull request.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia que el autor determine.
