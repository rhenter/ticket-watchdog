output "ecs_service_name" {
  value = aws_ecs_service.api.name
}

output "rds_endpoint" {
  value = aws_rds_cluster.this.endpoint
}
