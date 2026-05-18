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
