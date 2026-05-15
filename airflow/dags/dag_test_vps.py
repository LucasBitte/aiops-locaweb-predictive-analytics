from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello_vps():
    print("🚀 Airflow na VPS está rodando o código enviado pelo VS Code!")

with DAG(
    dag_id='vps_connection_test',
    start_date=datetime(2026, 5, 15),
    schedule_interval=None,
    catchup=False
) as dag:

    task_hello = PythonOperator(
        task_id='hello_task',
        python_callable=hello_vps
    )