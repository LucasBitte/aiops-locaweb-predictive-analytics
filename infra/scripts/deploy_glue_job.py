"""
Deploy Glue Jobs via boto3
Epico: E5

Responsabilidade:
- Upload scripts Python para S3
- Criar dois Glue jobs (xlsx_to_parquet + transform_bronze_to_silver)
- Job 1: Converter XLSX para Parquet (Python Shell)
- Job 2: Transformar Bronze para Silver (Glue ETL)
"""

import boto3
import os
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import urllib3
import warnings

urllib3.disable_warnings()
warnings.filterwarnings('ignore')

load_dotenv()

AWS_PROFILE = os.getenv("AWS_PROFILE", "aiops-deployer")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "aiops-locaweb-datalake-2026")
GLUE_ROLE_ARN = os.getenv("GLUE_ROLE_ARN", "")

SCRIPTS_TO_UPLOAD = [
    ("pipeline/bronze/xlsx_to_parquet.py", "scripts/xlsx_to_parquet.py"),
    ("pipeline/silver/transform_bronze_to_silver.py", "scripts/transform_bronze_to_silver.py"),
]


def log_info(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [OK] {msg}")


def log_error(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [ERROR] {msg}")


def log_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def init_aws_clients():
    try:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        s3_client = session.client("s3", verify=False)
        glue_client = session.client("glue", verify=False)
        iam_client = session.client("iam", verify=False)

        sts = session.client("sts", verify=False)
        identity = sts.get_caller_identity()
        log_info(f"Conectado como: {identity['Arn']}")

        return s3_client, glue_client, iam_client

    except Exception as e:
        log_error(f"Erro ao conectar AWS: {e}")
        raise


def upload_scripts_to_s3(s3_client):
    log_section("FAZENDO UPLOAD DOS SCRIPTS")

    for local_path, s3_key in SCRIPTS_TO_UPLOAD:
        try:
            if not os.path.exists(local_path):
                log_error(f"Arquivo nao encontrado: {local_path}")
                continue

            log_info(f"Uploadando {local_path} -> s3://{S3_BUCKET}/{s3_key}")
            s3_client.upload_file(local_path, S3_BUCKET, s3_key)

        except Exception as e:
            log_error(f"Erro ao fazer upload {local_path}: {e}")
            raise

    log_info(f"[SUCCESS] {len(SCRIPTS_TO_UPLOAD)} scripts uploadados para S3")


def get_glue_role():
    if not GLUE_ROLE_ARN:
        log_error("GLUE_ROLE_ARN eh obrigatoria")
        print("\n" + "="*70)
        print("ERROR: Voce precisa fornecer uma role IAM existente")
        print("="*70)
        print("\nDefina a variavel de ambiente:")
        print('  $env:GLUE_ROLE_ARN = "arn:aws:iam::206226812451:role/NOME_ROLE"')
        print("\nOu no arquivo .env:")
        print('  GLUE_ROLE_ARN=arn:aws:iam::206226812451:role/NOME_ROLE')
        print("\nExemplo de roles existentes no seu projeto:")
        print('  - arn:aws:iam::206226812451:role/aiops-glue-bronze-silver-role')
        print("="*70 + "\n")
        raise ValueError("GLUE_ROLE_ARN nao definida")

    log_info(f"Usando role existente: {GLUE_ROLE_ARN}")
    return GLUE_ROLE_ARN


def create_xlsx_to_parquet_job(role_arn):
    log_section("CRIANDO JOB: xlsx_to_parquet")
    job_name = "xlsx_to_parquet"

    try:
        log_info(f"Criando job: {job_name}")

        cmd = (
            f'aws glue create-job '
            f'--name {job_name} '
            f'--role {role_arn} '
            f'--command Name=pythonshell,ScriptLocation=s3://{S3_BUCKET}/scripts/xlsx_to_parquet.py,PythonVersion=3 '
            f'--timeout 60 '
            f'--max-retries 0 '
            f'--profile {AWS_PROFILE} '
            f'--region {AWS_REGION}'
        )

        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            log_info(f"[SUCCESS] Job criado: {job_name}")
            return job_name
        elif "AlreadyExistsException" in result.stderr or "already exists" in result.stderr:
            log_info(f"[INFO] Job ja existe, atualizando: {job_name}")

            update_cmd = (
                f'aws glue update-job '
                f'--name {job_name} '
                f'--role {role_arn} '
                f'--command Name=pythonshell,ScriptLocation=s3://{S3_BUCKET}/scripts/xlsx_to_parquet.py,PythonVersion=3 '
                f'--profile {AWS_PROFILE} '
                f'--region {AWS_REGION}'
            )

            update_result = subprocess.run(update_cmd, capture_output=True, text=True, shell=True)

            if update_result.returncode == 0:
                log_info(f"[SUCCESS] Job atualizado: {job_name}")
                return job_name
            else:
                log_error(f"[FAILED] Erro ao atualizar job: {update_result.stderr}")
                raise Exception(update_result.stderr)
        else:
            log_error(f"[FAILED] Erro ao criar job: {result.stderr}")
            raise Exception(result.stderr)

    except Exception as e:
        log_error(f"[FAILED] Erro ao criar xlsx_to_parquet job: {e}")
        raise


def create_transform_bronze_to_silver_job(role_arn):
    log_section("CRIANDO JOB: transform_bronze_to_silver")
    job_name = "transform_bronze_to_silver"

    try:
        log_info(f"Criando job: {job_name}")

        cmd = (
            f'aws glue create-job '
            f'--name {job_name} '
            f'--role {role_arn} '
            f'--command Name=glueetl,ScriptLocation=s3://{S3_BUCKET}/scripts/transform_bronze_to_silver.py,PythonVersion=3 '
            f'--glue-version 4.0 '
            f'--worker-type G.1X '
            f'--number-of-workers 3 '
            f'--timeout 60 '
            f'--max-retries 0 '
            f'--profile {AWS_PROFILE} '
            f'--region {AWS_REGION}'
        )

        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            log_info(f"[SUCCESS] Job criado: {job_name}")
            return job_name
        elif "AlreadyExistsException" in result.stderr or "already exists" in result.stderr:
            log_info(f"[INFO] Job ja existe, atualizando: {job_name}")

            update_cmd = (
                f'aws glue update-job '
                f'--name {job_name} '
                f'--role {role_arn} '
                f'--command Name=glueetl,ScriptLocation=s3://{S3_BUCKET}/scripts/transform_bronze_to_silver.py,PythonVersion=3 '
                f'--profile {AWS_PROFILE} '
                f'--region {AWS_REGION}'
            )

            update_result = subprocess.run(update_cmd, capture_output=True, text=True, shell=True)

            if update_result.returncode == 0:
                log_info(f"[SUCCESS] Job atualizado: {job_name}")
                return job_name
            else:
                log_error(f"[FAILED] Erro ao atualizar job: {update_result.stderr}")
                raise Exception(update_result.stderr)
        else:
            log_error(f"[FAILED] Erro ao criar job: {result.stderr}")
            raise Exception(result.stderr)

    except Exception as e:
        log_error(f"[FAILED] Erro ao criar transform_bronze_to_silver job: {e}")
        raise


def main():
    print("\n" + "="*70)
    print("  DEPLOY GLUE JOBS (E5) - BRONZE to SILVER PIPELINE")
    print("="*70 + "\n")

    try:
        s3_client, glue_client, iam_client = init_aws_clients()

        upload_scripts_to_s3(s3_client)

        role_arn = get_glue_role()

        job1_name = create_xlsx_to_parquet_job(role_arn)
        job2_name = create_transform_bronze_to_silver_job(role_arn)

        print("="*70)
        print("[SUCCESS] GLUE JOBS CRIADOS COM SUCESSO")
        print("="*70)
        print(f"\nArquivos em S3:")
        print(f"  - s3://{S3_BUCKET}/scripts/xlsx_to_parquet.py")
        print(f"  - s3://{S3_BUCKET}/scripts/transform_bronze_to_silver.py")
        print(f"\nGlue Jobs criados:")
        print(f"  1. {job1_name} (Python Shell - XLSX to Parquet)")
        print(f"  2. {job2_name} (Glue ETL - Parquet to Silver)")
        print(f"  Role: {role_arn}")
        print(f"\nPipeline E4->E5:")
        print(f"\n[STEP 1] Executar job 1 (XLSX to Parquet):")
        print(f"  aws glue start-job-run --job-name {job1_name} --profile {AWS_PROFILE}")
        print(f"\n[STEP 2] Aguardar conclusao (5-10 min), depois executar job 2:")
        print(f"  aws glue start-job-run --job-name {job2_name} --profile {AWS_PROFILE}")
        print(f"\n[STEP 3] Monitorar execucao:")
        print(f"  aws logs tail /aws-glue/jobs/output --follow --profile {AWS_PROFILE}")
        print(f"\n[STEP 4] Validar Silver em S3:")
        print(f"  aws s3 ls s3://{S3_BUCKET}/silver/ --recursive --profile {AWS_PROFILE}")
        print()

        return 0

    except Exception as e:
        log_error(f"Pipeline falhou: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
