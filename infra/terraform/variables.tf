# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "fullstack-template"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "app"
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
  default     = "app"
}

variable "db_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Container Images
# -----------------------------------------------------------------------------

variable "api_image" {
  description = "Docker image for the API service"
  type        = string
  default     = "ghcr.io/OWNER/fullstack-template-api:latest"
}

variable "web_image" {
  description = "Docker image for the Web service"
  type        = string
  default     = "ghcr.io/OWNER/fullstack-template-web:latest"
}

# -----------------------------------------------------------------------------
# Registry Credentials (optional)
# -----------------------------------------------------------------------------

variable "ghcr_username" {
  description = "GitHub Container Registry username (for private image pulls)"
  type        = string
  default     = ""
}

variable "ghcr_token" {
  description = "GitHub Container Registry token (for private image pulls)"
  type        = string
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------------------------
# ECS Scaling Overrides
# -----------------------------------------------------------------------------

variable "ecs_desired_count_override" {
  description = "Optional override for ECS desired task count (set to 0 to pause)"
  type        = number
  default     = null
}

variable "ecs_ignore_desired_count" {
  description = "Ignore desired_count changes so manual scaling isn't reverted"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Storage
# -----------------------------------------------------------------------------

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for uploads (must be globally unique)"
  type        = string
}

variable "s3_access_key_id" {
  description = "S3 access key ID (optional, uses IAM role if not provided)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "s3_secret_access_key" {
  description = "S3 secret access key (optional, uses IAM role if not provided)"
  type        = string
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Security / Secrets
# -----------------------------------------------------------------------------

variable "jwt_secret" {
  description = "Secret key for JWT signing"
  type        = string
  sensitive   = true
}

variable "jwt_issuer" {
  description = "JWT issuer claim"
  type        = string
  default     = "fullstack-template"
}

variable "jwt_audience" {
  description = "JWT audience claim"
  type        = string
  default     = "fullstack-template"
}

# -----------------------------------------------------------------------------
# CORS / Domain
# -----------------------------------------------------------------------------

variable "cors_origins" {
  description = "List of allowed CORS origins"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS (optional)"
  type        = string
  default     = ""
}

variable "enable_https" {
  description = "Enable HTTPS on the load balancer (requires certificate_arn)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Email
# -----------------------------------------------------------------------------

variable "email_from_address" {
  description = "Default from address for emails"
  type        = string
  default     = "no-reply@example.com"
}

variable "email_from_name" {
  description = "Default from name for emails"
  type        = string
  default     = "Fullstack Template"
}

variable "email_web_base_url" {
  description = "Base URL for frontend links in emails"
  type        = string
  default     = "http://localhost:3000"
}

# -----------------------------------------------------------------------------
# Web App
# -----------------------------------------------------------------------------

variable "next_public_api_url" {
  description = "Public API URL for the Next.js frontend"
  type        = string
  default     = "http://localhost:8000/api/v1"
}
