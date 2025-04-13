import boto3
import json

bucket_name = 'certificados-notas-mineduc'
prefix = 'entradas/'
lambda_function_name = 'notas-mineduc'

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

if 'Contents' not in response:
    print("❌ No se encontraron archivos en 'entradas/'.")
    exit()

pdfs = [item['Key'] for item in response['Contents'] if item['Key'].endswith('.pdf')]

for pdf_key in pdfs:
    print(f"🟢 Procesando: {pdf_key}")
    event_payload = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket_name},
                    "object": {"key": pdf_key}
                }
            }
        ]
    }

    response = lambda_client.invoke(
        FunctionName=lambda_function_name,
        InvocationType='Event',
        Payload=json.dumps(event_payload)
    )

    if response['StatusCode'] == 202:
        print(f"✅ Enviado correctamente a Lambda")
    else:
        print(f"❌ Error en {pdf_key}: {response}")
