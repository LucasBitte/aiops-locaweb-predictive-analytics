import os
import gc  # Gerenciamento de memória RAM para tabelas pesadas
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Carrega as variáveis de ambiente do arquivo .env localizado na raiz
load_dotenv(override=True)

RDS_HOST     = os.getenv('RDS_HOST')
RDS_PORT     = int(os.getenv('RDS_PORT', '5432'))
RDS_USER     = os.getenv('RDS_USER')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DB       = os.getenv('RDS_DB', 'analytics')
RDS_SCHEMA   = os.getenv('RDS_SCHEMA', 'dbt_dev_dbt_dev') 

# 2. Definição do Diretório de Destino Local (Camada Gold)
OUTPUT_DIR = r"D:\Projetos\AWS_Portifolio\Projeto aws\data\gold"

# 3. Pipeline de Tabelas Mapeadas para Exportação Sequencial
TABLES_TO_EXPORT = [
    # Camada Dimensional (Star Schema)
    "dim_abertura",
    "dim_grupo",
    "dim_prioridade",
    "dim_produto_categoria",
    "dim_status",
    "dim_tempo",
    "fct_incidents",
    # Camada de Machine Learning (Feature Store)
    "ml_base_features",
    "ml_cluster_dataset",
    "ml_forecast_dataset",
    "ml_sla_classification_dataset"
]


def executar_pipeline():
    print("=======================================================================")
    print("⚙️  CONFIGURAÇÃO DO AMBIENTE LOCALIZADA")
    print(f"📡 Host:   {RDS_HOST}")
    print(f"🗄️  DB:     {RDS_DB}")
    print(f"🧩 Schema: {RDS_SCHEMA}")
    print("=======================================================================\n")

    # Validação de segurança para impedir execução caso o arquivo .env falhe
    if not all([RDS_HOST, RDS_USER, RDS_PASSWORD]):
        print("❌ ERRO CRÍTICO: Credenciais do banco não foram encontradas no arquivo .env!")
        print("👉 Certifique-se de que o arquivo .env está na mesma pasta deste script.\n")
        return

    # Construção segura da URL de conexão utilizando as variáveis de ambiente
    connection_url = f"postgresql+psycopg2://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DB}"
    engine = create_engine(connection_url)

    # ---- NOVO BLOCO: VALIDAÇÃO DE CONEXÃO ----
    print("🔄 Tentando estabelecer comunicação com o AWS RDS...")
    try:
        with engine.connect() as conn:
            # Executa uma query leve apenas para testar o canal
            conn.execute(text("SELECT 1"))
        print("🔌 CONEXÃO REALIZADA COM SUCESSO! Banco de dados autenticado e pronto.\n")
        print("=======================================================================\n")
    except Exception as e:
        print("❌ ERRO AO CONECTAR: Não foi possível alcançar o banco de dados.")
        print(f"⚠️ Detalhes técnicos: {e}\n")
        return
    # ----------------------------------------

    # Garante a criação física da pasta destino no disco D:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_tables = len(TABLES_TO_EXPORT)
    print("🚀 INICIANDO PROCESSAMENTO ISOLADO E SEQUENCIAL (TABELA POR TABELA)")
    print(f"📊 Total de tabelas na fila: {total_tables}\n")

    # Loop principal ordenado
    for index, table in enumerate(TABLES_TO_EXPORT, 1):
        percentage = (index / total_tables) * 100
        
        print(f"🔄 [{index}/{total_tables}] - {percentage:.1f}% DO PIPELINE GERAL")
        print(f"📌 Processando agora: {table}")
        print("-" * 60)
        
        try:
            # ---- ETAPA 1: EXTRAÇÃO ISOLADA ----
            print("  📥 [ETAPA 1/2] Extraindo dados do RDS...")
            with engine.connect() as conn:
                query = f"SELECT * FROM {RDS_SCHEMA}.{table}"
                df = pd.read_sql(text(query), con=conn)
                
            print(f"  👉 Carga concluída com sucesso: {len(df)} linhas em memória.")
            
            # ---- ETAPA 2: GRAVAÇÃO E FECHAMENTO ----
            parquet_path = os.path.join(OUTPUT_DIR, f"{table}.parquet")
            print(f"  💾 [ETAPA 2/2] Compactando e escrevendo arquivo Parquet...")
            
            df.to_parquet(parquet_path, index=False, engine='pyarrow')
            print(f"  🎯 Arquivo físico salvo em: {parquet_path}")
            
            # Força o Python a expurgar o DataFrame da memória RAM imediatamente
            del df
            gc.collect()
            
            print(f"  ✅ Transição concluída. Tabela {table} finalizada 100%.\n")
            print("=" * 75 + "\n")
            
        except Exception as e:
            print(f"  ❌ FALHA AO PROCESSAR TABELA: {table}")
            print(f"  ⚠️ Mensagem do sistema: {e}")
            print("  ⏭️ Pulando automaticamente para manter a integridade das outras tabelas.\n")
            print("=" * 75 + "\n")

    # Encerra o pool de conexões antes de finalizar o script por completo
    engine.dispose()

    print("=======================================================================")
    print("✨  ETL EXECUTADO COMPLETAMENTE COM SUCESSO!")
    print(f"📂  Sua camada Gold local está atualizada em: {OUTPUT_DIR}")
    print("=======================================================================")


if __name__ == "__main__":
    executar_pipeline()