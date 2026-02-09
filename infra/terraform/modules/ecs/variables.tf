variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "cpu" {
  description = "CPU units for the task (256, 512, 1024, etc.)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory in MB for the task (512, 1024, 2048, etc.)"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "ignore_desired_count" {
  description = "Ignore desired_count changes to allow manual scaling"
  type        = bool
  default     = true
}

variable "api_image" {
  description = "Docker image for the API service"
  type        = string
}

variable "web_image" {
  description = "Docker image for the Web service"
  type        = string
}

variable "ghcr_credentials_arn" {
  description = "Secrets Manager ARN with GHCR credentials for private pulls"
  type        = string
  default     = ""
}

variable "api_target_group_arn" {
  description = "ARN of the API target group"
  type        = string
}

variable "web_target_group_arn" {
  description = "ARN of the Web target group"
  type        = string
}

variable "secrets_arns" {
  description = "List of Secrets Manager ARNs the tasks can access"
  type        = list(string)
}

# Environment variables
variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "s3_bucket" {
  description = "S3 bucket name for uploads"
  type        = string
}

variable "s3_region" {
  description = "AWS region for S3"
  type        = string
}

variable "cors_origins" {
  description = "CORS origins (comma-separated)"
  type        = string
}

variable "jwt_issuer" {
  description = "JWT issuer claim"
  type        = string
}

variable "jwt_audience" {
  description = "JWT audience claim"
  type        = string
}

variable "email_from_address" {
  description = "Email from address"
  type        = string
}

variable "email_from_name" {
  description = "Email from name"
  type        = string
}

variable "email_web_base_url" {
  description = "Base URL for email links"
  type        = string
}

variable "next_public_api_url" {
  description = "Public API URL for Next.js frontend"
  type        = string
}
