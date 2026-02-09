# -----------------------------------------------------------------------------
# Networking Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = module.networking.ecs_security_group_id
}

# -----------------------------------------------------------------------------
# Load Balancer Outputs
# -----------------------------------------------------------------------------

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.loadbalancer.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer (for Route53 alias)"
  value       = module.loadbalancer.alb_zone_id
}

output "api_url" {
  description = "URL for the API service"
  value       = "http${var.enable_https ? "s" : ""}://${module.loadbalancer.alb_dns_name}/api/v1"
}

output "web_url" {
  description = "URL for the Web service"
  value       = "http${var.enable_https ? "s" : ""}://${module.loadbalancer.alb_dns_name}"
}

# -----------------------------------------------------------------------------
# Database Outputs
# -----------------------------------------------------------------------------

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.endpoint
}

output "database_port" {
  description = "RDS instance port"
  value       = module.database.port
}

output "database_secret_arn" {
  description = "ARN of the Secrets Manager secret containing database credentials"
  value       = module.secrets.database_secret_arn
}

# -----------------------------------------------------------------------------
# Storage Outputs
# -----------------------------------------------------------------------------

output "s3_bucket_name" {
  description = "Name of the S3 bucket for uploads"
  value       = module.storage.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for uploads"
  value       = module.storage.bucket_arn
}

output "s3_bucket_regional_domain" {
  description = "Regional domain name of the S3 bucket"
  value       = module.storage.bucket_regional_domain_name
}

# -----------------------------------------------------------------------------
# ECS Outputs
# -----------------------------------------------------------------------------

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "api_service_name" {
  description = "Name of the API ECS service"
  value       = module.ecs.api_service_name
}

output "web_service_name" {
  description = "Name of the Web ECS service"
  value       = module.ecs.web_service_name
}

output "api_task_definition_arn" {
  description = "ARN of the API task definition"
  value       = module.ecs.api_task_definition_arn
}

# -----------------------------------------------------------------------------
# Secrets Outputs
# -----------------------------------------------------------------------------

output "jwt_secret_arn" {
  description = "ARN of the JWT secret in Secrets Manager"
  value       = module.secrets.jwt_secret_arn
}

output "app_secrets_arn" {
  description = "ARN of the app secrets in Secrets Manager"
  value       = module.secrets.app_secret_arn
}

# -----------------------------------------------------------------------------
# Environment Info
# -----------------------------------------------------------------------------

output "environment" {
  description = "Current environment (workspace)"
  value       = local.env
}

output "name_prefix" {
  description = "Resource naming prefix"
  value       = local.name_prefix
}
