output "vpc_id" {
  value       = aws_vpc.main.id
  description = "ID da VPC"
}

output "subnet_ids" {
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  description = "Lista de IDs das subnets"
}
