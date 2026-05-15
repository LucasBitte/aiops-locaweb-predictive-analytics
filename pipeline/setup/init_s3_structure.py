import boto3
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

def initialize_s3_governance():
    bucket_name = os.getenv("S3_BUCKET")
    # Usa o perfil que configuramos
    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
    s3 = session.client('s3')

    # Estrutura de pastas do Data Lake
    folders = [
        "bronze/",
        "silver/",
        "gold/ml/",
        "gold/bi/",
        "docs/logs/"
    ]

    print(f"📂 Iniciando governança no bucket: {bucket_name}")

    for folder in folders:
        # No S3, "criar pasta" é criar um objeto vazio que termina com '/'
        s3.put_object(Bucket=bucket_name, Key=folder)
        print(f"✅ Camada criada: {folder}")

    print("\n🚀 Estrutura do Data Lake pronta para ingestão!")

if __name__ == "__main__":
    initialize_s3_governance()