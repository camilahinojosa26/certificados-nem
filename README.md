#  Automatización de Cálculo de NEM desde Certificados del Mineduc

Este proyecto utiliza **Amazon Textract** para realizar OCR sobre certificados de concentración de notas de enseñanza media emitidos por el Ministerio de Educación de Chile.

##  Estructura

- `lambda_function.py`: Código que se despliega en una función AWS Lambda. Esta función se activa cada vez que se sube un archivo PDF a la carpeta `entradas/` del bucket S3.
- `procesar_certificados.py`: Script local que recorre todos los PDFs en la carpeta `entradas/` del bucket y los procesa uno por uno llamando a la Lambda.
- Archivos generados:
  - `resultados/resultado_nombreArchivo.csv`: archivo CSV con nombre, RUT, asignaturas y notas del alumno.
  - `resultados/resumen_certificados.csv`: CSV resumen con RUT, nombre y NEM de todos los certificados procesados.

##  Requisitos

- AWS CLI instalado y configurado con acceso a:
  - Amazon Textract
  - Amazon S3
  - AWS Lambda
- Python 3 y `boto3` instalado (`pip install boto3`)

##  ¿Cómo usarlo?

1. Subir archivos PDF a `entradas/` dentro del bucket S3.
2. Esperar a que la Lambda se dispare automáticamente **(o ejecutar el script local)**.
3. Revisar la carpeta `resultados/` para ver los CSVs generados.

##  Notas

- Los archivos deben ser certificados oficiales descargados desde ChileAtiende/Mineduc.
- El NEM se calcula como el promedio de las “Calificaciones Finales” de cada año escolar.
- La Lambda puede ser invocada por trigger S3 o manualmente.


