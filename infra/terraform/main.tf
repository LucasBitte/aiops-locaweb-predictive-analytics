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
# 3. BANCO DE DADOS (RDS PostgreSQL + Glue)
# ==========================================
# Descomentar apenas quando pronto para usar
# Nota: RDS gera custos mesmo em Free Tier apos 12 meses
# Para aplicar: terraform apply -var="rds_password=SenhaForte123!"
module "database" {
  source       = "./modules/database"
  subnet_ids   = module.network.subnet_ids
  rds_password = var.rds_password
}
