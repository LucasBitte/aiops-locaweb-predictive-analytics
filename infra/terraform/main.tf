# ==========================================
# 1. REDE (VPC e Conectividade)
# ==========================================
module "network" {
  source = "./modules/network"
}

# ==========================================
# 2. DATA LAKE (S3)
# ==========================================
module "storage" {
  source      = "./modules/storage"
  bucket_name = "aiops-locaweb-datalake-2026"
}

# ==========================================
# 3. BANCO DE DADOS (RDS PostgreSQL)
# ==========================================
# Descomentar apenas quando pronto para usar
# Nota: RDS gera custos mesmo em Free Tier apos 12 meses
# Para aplicar: terraform apply -var="rds_password=SenhaForte123!"
module "database" {
  source       = "./modules/database"
  subnet_ids   = module.network.subnet_ids
  rds_password = var.rds_password
}

# ==========================================
# 4. GLUE JOB (Bronze → Silver E5)
# ==========================================
module "glue" {
  source      = "./modules/glue"
  bucket_name = module.storage.bucket_id

  # Configurações Free Tier (G.1X × 3 = 180 DPU-min/exec)
  glue_job_name    = "transform_bronze_to_silver"
  glue_version     = "4.0"
  worker_type      = "G.1X"
  num_workers      = 3
  timeout_minutes  = 60
}
