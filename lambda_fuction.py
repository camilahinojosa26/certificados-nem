import boto3
import time
import csv
import io
import re

s3 = boto3.client('s3')
textract = boto3.client('textract')

def lambda_handler(event, context):
    # Leer datos desde el evento
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    document = record['s3']['object']['key']  # Ejemplo: entradas/archivo.pdf

    print(f"Procesando archivo: {document}")

    # Iniciar análisis Textract
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=['TABLES', 'FORMS']
    )
    
    job_id = response['JobId']
    
    # Esperar resultado
    print("Esperando resultado...")
    while True:
        result = textract.get_document_analysis(JobId=job_id)
        status = result['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            break
        time.sleep(1)

    if status == 'FAILED':
        raise Exception('Textract falló en procesar el documento.')

    # Extraer texto
    blocks = result['Blocks']
    lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']

    # Extraer nombre y RUT
    nombre = ""
    rut = "NO_ENCONTRADO"
    for line in lines:
        if 'RUN' in line.upper():
            match = re.match(r'^(.*?),\s*RUN\s*(\d{1,2}\.\d{3}\.\d{3}-\d)', line, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
                rut = match.group(2)
            break

    # Extraer notas
    notas = []
    current_year = ""
    last_subject = ""
    for line in lines:
        year_match = re.search(r'Año Escolar (\d{4})', line)
        if year_match:
            current_year = year_match.group(1)

        nota_match = re.match(r'^([6-7]\.\d)$', line)
        if nota_match and last_subject and current_year:
            nota = nota_match.group(1)
            notas.append([current_year, last_subject, nota])
            last_subject = ""
        elif len(line.split()) > 1 and not re.match(r'^\d{1,2}\.\d$', line):
            last_subject = line.strip()

    # Calcular NEM
    calificaciones_finales = []
    for i, line in enumerate(lines):
        if "CALIFICACIÓN FINAL" in line.upper():
            if i+1 < len(lines):
                try:
                    nota_final = float(lines[i+1].strip())
                    if 6.0 <= nota_final <= 7.0:
                        calificaciones_finales.append(nota_final)
                except:
                    continue

    nem = round(sum(calificaciones_finales) / len(calificaciones_finales), 2) if calificaciones_finales else 0

    # Crear CSV individual
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nombre', 'RUT', 'Año', 'Asignatura', 'Nota'])
    for year, subject, grade in notas:
        writer.writerow([nombre, rut, year, subject, grade])
    writer.writerow(['NEM', '', '', '', nem])

    nombre_base = document.rsplit("/", 1)[-1].replace(".pdf", "").replace(" ", "_")
    output_filename = f'resultados/resultado_{nombre_base}.csv'

    s3.put_object(
        Bucket=bucket,
        Key=output_filename,
        Body=output.getvalue()
    )

    # ---------- CSV resumen global ----------
    resumen_key = 'resultados/resumen_certificados.csv'
    resumen_data = []

    # agrupar notas por año
    notas_por_año = {}
    for año, _, nota in notas:
        if año not in notas_por_año:
            notas_por_año[año] = []
        try:
            notas_por_año[año].append(float(nota))
        except:
            continue

    # calcular promedios por año
    años_ordenados = sorted(notas_por_año.keys())[:4]  # máx 4 años
    promedios = []
    for año in años_ordenados:
        promedio = round(sum(notas_por_año[año]) / len(notas_por_año[año]), 2)
        promedios.append(promedio)
    # completar con vacíos si no hay 4 años
    while len(promedios) < 4:
        promedios.append("")

    try:
        old = s3.get_object(Bucket=bucket, Key=resumen_key)
        reader = csv.reader(io.StringIO(old['Body'].read().decode('utf-8')))
        resumen_data = list(reader)
    except s3.exceptions.NoSuchKey:
        resumen_data.append(['RUT', 'Nombre', 'NEM', 'Año 1', 'Año 2', 'Año 3', 'Año 4'])

    # Eliminar fila existente del mismo RUT si ya estaba
    resumen_data = [r for r in resumen_data if r[0] != rut]

    # Agregar nueva fila
    resumen_data.append([rut, nombre, str(nem)] + promedios)

    resumen_output = io.StringIO()
    writer = csv.writer(resumen_output)
    for row in resumen_data:
        writer.writerow(row)

    s3.put_object(Bucket=bucket, Key=resumen_key, Body=resumen_output.getvalue())

    return {
        'statusCode': 200,
        'body': f'CSV generado: {output_filename}, NEM: {nem}, resumen actualizado.'
    }
