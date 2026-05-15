import boto3
import os
import pandas as pd
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError

# Carrega configurações
load_dotenv()

def upload_to_bronze():
    # Configurações
    local_file = 'data/raw/LW-DATASET.xlsx'
    bucket_name = os.getenv("S3_BUCKET")
    s3_key = 'bronze/LW-DATASET.xlsx'
    
    # Validação local
    if not os.path.exists(local_file):
        print(f"❌ Erro: O arquivo {local_file} não foi encontrado!")
        print("Certifique-se de que o arquivo está na pasta 'data/raw/'.")
        return

    print(f"⏳ Iniciando upload de {local_file}...")

    try:
        # Inicia sessão AWS
        session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
        s3 = session.client('s3')

        # Upload do arquivo
        s3.upload_file(local_file, bucket_name, s3_key)
        
        print(f"✅ Sucesso! Arquivo disponível em: s3://{bucket_name}/{s3_key}")
        
        # Opcional: Validar o que acabamos de subir (contagem de linhas)
        df = pd.read_excel(local_file)
        print(f"📊 Validação inicial: {len(df)} registros detectados no arquivo local.")

    except NoCredentialsError:
        print("❌ Erro: Credenciais AWS não encontradas.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    upload_to_bronze()