variable "subnet_ids" {
  description = "Lista de IDs das subnets onde o RDS será provisionado"
  type        = list(string)
}

variable "rds_password" {
  description = "Senha do banco de dados RDS"
  type        = string
  sensitive   = true
}
