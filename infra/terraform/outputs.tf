output "bucket_id" {
  value       = aws_s3_bucket.datalake.id
  description = "O nome/ID do bucket criado"
}

output "bucket_arn" {
  value       = aws_s3_bucket.datalake.arn
  description = "O ARN (Amazon Resource Name) do bucket"
}