# --- DB SUBNET GROUP (Obrigatório para RDS em VPC) ---
resource "aws_db_subnet_group" "default" {
  name       = "main"
  subnet_ids = var.subnet_ids
}

# --- AWS RDS (POSTGRESQL) ---
resource "aws_db_instance" "gold_db" {
  allocated_storage    = 20
  db_name              = "aiops_gold"
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  username             = "postgres"
  password             = var.rds_password
  db_subnet_group_name = aws_db_subnet_group.default.name
  skip_final_snapshot  = true
  publicly_accessible  = true
}

# --- AWS GLUE CATALOG (comentado - requer permissão glue:CreateDatabase) ---
# Descomente quando tiver permissão IAM para glue:CreateDatabase
# resource "aws_glue_catalog_database" "aiops_catalog" {
#   name = "aiops_catalog_db"
# }
