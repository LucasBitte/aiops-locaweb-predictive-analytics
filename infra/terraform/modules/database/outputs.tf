output "rds_endpoint" {
  value       = aws_db_instance.gold_db.endpoint
  description = "Endpoint de conexão do RDS PostgreSQL"
  sensitive   = true
}

output "rds_database_name" {
  value       = aws_db_instance.gold_db.db_name
  description = "Nome do banco de dados PostgreSQL"
}

output "rds_username" {
  value       = aws_db_instance.gold_db.username
  description = "Usuário padrão do RDS"
}

output "glue_catalog_database" {
  value       = aws_glue_catalog_database.aiops_catalog.name
  description = "Nome do banco de dados do AWS Glue Catalog"
}
