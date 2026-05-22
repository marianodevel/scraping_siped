# Preguntas Frecuentes (FAQ) - Sistema SIPED
Este documento compila las resoluciones a las consultas y eventualidades más comunes
durante la operación del Sistema Integrado de Extracción y Consolidación de Expedientes
(SIPED).
## Operación y Tareas en Segundo Plano
¿Es necesario mantener el navegador abierto durante la extracción masiva?
No. Una vez iniciada una fase (por ejemplo, la Fase 2 o Fase 3), la petición se delega a los
procesos en segundo plano. Puede cerrar el navegador o interrumpir la conexión de su equipo;
el proceso continuará ejecutándose en el servidor hasta su finalización.
¿Qué ocurre si el sistema falla al descargar un documento específico en la Fase 3?
Si el portal judicial presenta intermitencias de red o un archivo adjunto está dañado en el
servidor de origen, el sistema registrará el error de manera interna y continuará con el siguiente
documento para no detener la cola de trabajo. Para subsanar la omisión, puede utilizar la
función "Actualización de Expediente Único" sobre el caso particular posteriormente.
## Credenciales y Seguridad
¿El sistema almacena mi contraseña de la intranet judicial?
No. El sistema utiliza sus credenciales exclusivamente en el momento de la solicitud inicial para
negociar un token de acceso (cookie de sesión) con el servidor del Poder Judicial. La
contraseña no persiste en la base de datos ni en ningún archivo físico del sistema SIPED.
## Sincronización y Consolidación
Ejecuté la Fase 1 pero no veo todos mis expedientes. ¿A qué se debe?
La Fase 1 sincroniza estrictamente los expedientes que se encuentran vinculados de manera
formal a su usuario dentro de la bandeja privada del portal judicial. Si un expediente requiere
consulta pública para ser visualizado, deberá ser localizado e indexado utilizando la
herramienta de "Búsqueda Avanzada".
¿Qué indica la etiqueta "Consolidado" en el nombre de un archivo PDF?
El archivo denominado con el sufijo "(Consolidado)" representa el producto final de la Fase 3.
Este archivo compila estructuralmente y en estricto orden cronológico tanto el documento
principal de la actuación judicial como todos sus anexos o adjuntos, integrándolos en un único
archivo físico.
Los archivos CSV generados no se tabulan correctamente al abrirlos en Microsoft Excel.
¿Cómo se soluciona?
El sistema exporta los archivos CSV utilizando coma (,) como carácter delimitador estándar y
codificación UTF-8. Si su configuración regional de Windows o Excel espera un punto y coma
(;), deberá utilizar la funcionalidad "Datos > Obtener datos desde el texto/CSV" dentro de la
hoja de cálculo para forzar la lectura delimitada por comas.
