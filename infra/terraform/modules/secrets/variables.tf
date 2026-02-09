variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "db_password" {
  description = "Database password (stored in database secret)"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "s3_access_key_id" {
  description = "S3 access key ID (optional if using IAM roles)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "s3_secret_access_key" {
  description = "S3 secret access key (optional if using IAM roles)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ghcr_username" {
  description = "GHCR username for private image pulls"
  type        = string
  default     = ""
}

variable "ghcr_token" {
  description = "GHCR token for private image pulls"
  type        = string
  default     = ""
  sensitive   = true
}
