output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "api_url" {
  value = "http://${aws_lb.main.dns_name}"
}

output "healthcheck_url" {
  value = "http://${aws_lb.main.dns_name}/health"
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.api.name
}
