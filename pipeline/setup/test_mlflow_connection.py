import mlflow
import os
import sys
from dotenv import load_dotenv

# 1. Carregar o arquivo .env que está na raiz do projeto
# Como o script está em pipeline/setup/, subimos dois níveis
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)

def test_connection():
    print("🔍 Verificando configurações no .env...")
    
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    username = os.getenv("MLFLOW_TRACKING_USERNAME")
    password = os.getenv("MLFLOW_TRACKING_PASSWORD")

    if not all([tracking_uri, username, password]):
        print("❌ Erro: MLFLOW_TRACKING_URI, USERNAME ou PASSWORD não encontrados no .env")
        sys.exit(1)

    # 2. Configurar Autenticação e URIs
    os.environ["MLFLOW_TRACKING_USERNAME"] = username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = password
    
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)

    print(f"📡 Tentando conectar em: {tracking_uri}")

    try:
        # 3. Criar ou definir um experimento de teste
        experiment_name = "Setup_Test_Local"
        mlflow.set_experiment(experiment_name)
        
        # 4. Iniciar um 'Run' de teste
        with mlflow.start_run(run_name="Conexao_VSCode_Local"):
            mlflow.log_param("ambiente", "local_vscode")
            mlflow.log_metric("status_conexao", 1.0)
            
            print(f"\n✅ SUCESSO!")
            print(f"🧪 Experimento: '{experiment_name}' atualizado.")
            print(f"📊 Acesse a UI em {tracking_uri} para ver o log.")
            
    except Exception as e:
        print(f"\n❌ FALHA NA CONEXÃO:")
        print(f"Detalhes: {e}")

if __name__ == "__main__":
    test_connection()