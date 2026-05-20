# ==========================================
# OUTPUTS DOS MÓDULOS
# ==========================================

output "vpc_id" {
  value       = module.network.vpc_id
  description = "ID da VPC principal"
}

output "subnet_ids" {
  value       = module.network.subnet_ids
  description = "IDs das subnets públicas (A e B)"
}

output "bucket_id" {
  value       = module.storage.bucket_id
  description = "Nome/ID do bucket S3 Data Lake"
}

output "bucket_arn" {
  value       = module.storage.bucket_arn
  description = "ARN do bucket S3"
}

# ==========================================
# OUTPUTS DO GLUE (E5)
# ==========================================
output "glue_job_name" {
  value       = module.glue.glue_job_name
  description = "Nome do job Glue: transform_bronze_to_silver"
}

output "glue_job_arn" {
  value       = module.glue.glue_job_arn
  description = "ARN do job Glue"
}

output "glue_script_location" {
  value       = module.glue.script_s3_location
  description = "Localização do script Python no S3"
}

# ==========================================
# OUTPUTS DO DATABASE (descomente junto com o módulo)
# ==========================================
/*
output "rds_endpoint" {
  value       = module.database.rds_endpoint
  description = "Endpoint de conexão do RDS PostgreSQL"
  sensitive   = true
}

output "rds_database_name" {
  value       = module.database.rds_database_name
  description = "Nome do banco de dados PostgreSQL"
}

output "rds_username" {
  value       = module.database.rds_username
  description = "Usuário padrão do RDS"
}

output "glue_catalog_database" {
  value       = module.database.glue_catalog_database
  description = "Nome do banco de dados do AWS Glue Catalog"
}
*/