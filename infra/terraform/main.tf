# Fullstack Template - AWS Infrastructure
# Terraform configuration for deploying the fullstack template to AWS

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = local.env
      ManagedBy   = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Local Values
# -----------------------------------------------------------------------------

locals {
  # Use workspace name, defaulting to "dev" for the "default" workspace
  env = terraform.workspace == "default" ? "dev" : terraform.workspace

  # Environment-specific configuration
  config = {
    dev = {
      db_instance_class    = "db.t4g.micro"
      db_multi_az          = false
      db_allocated_storage = 20
      ecs_desired_count    = 1
      ecs_cpu              = 256
      ecs_memory           = 512
      nat_gateway_count    = 1
    }
    staging = {
      db_instance_class    = "db.t4g.micro"
      db_multi_az          = false
      db_allocated_storage = 20
      ecs_desired_count    = 1
      ecs_cpu              = 256
      ecs_memory           = 512
      nat_gateway_count    = 1
    }
    prod = {
      db_instance_class    = "db.t4g.small"
      db_multi_az          = true
      db_allocated_storage = 50
      ecs_desired_count    = 2
      ecs_cpu              = 512
      ecs_memory           = 1024
      nat_gateway_count    = 2
    }
  }[local.env]

  # Common naming prefix
  name_prefix = "${var.project_name}-${local.env}"

  ecs_desired_count = var.ecs_desired_count_override != null ? var.ecs_desired_count_override : local.config.ecs_desired_count
}

# -----------------------------------------------------------------------------
# Modules
# -----------------------------------------------------------------------------

module "networking" {
  source = "./modules/networking"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  nat_gateway_count  = local.config.nat_gateway_count
}

module "secrets" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
  environment = local.env

  # Initial secret values (these should be updated manually or via CI)
  jwt_secret           = var.jwt_secret
  db_password          = var.db_password
  s3_access_key_id     = var.s3_access_key_id
  s3_secret_access_key = var.s3_secret_access_key
  ghcr_username        = var.ghcr_username
  ghcr_token           = var.ghcr_token
}

module "database" {
  source = "./modules/database"

  name_prefix       = local.name_prefix
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.private_subnet_ids
  security_group_id = module.networking.rds_security_group_id

  instance_class    = local.config.db_instance_class
  allocated_storage = local.config.db_allocated_storage
  multi_az          = local.config.db_multi_az

  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password

  secrets_arn = module.secrets.database_secret_arn
}

module "storage" {
  source = "./modules/storage"

  name_prefix       = local.name_prefix
  environment       = local.env
  bucket_name       = var.s3_bucket_name
  cors_origins      = var.cors_origins
  lifecycle_ia_days = 90
}

module "loadbalancer" {
  source = "./modules/loadbalancer"

  name_prefix       = local.name_prefix
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  security_group_id = module.networking.alb_security_group_id

  certificate_arn = var.certificate_arn
  enable_https    = var.enable_https
}

module "ecs" {
  source = "./modules/ecs"

  name_prefix = local.name_prefix
  environment = local.env

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.networking.ecs_security_group_id

  # Task configuration
  cpu           = local.config.ecs_cpu
  memory        = local.config.ecs_memory
  desired_count = local.ecs_desired_count
  ignore_desired_count = var.ecs_ignore_desired_count

  # Container images
  api_image = var.api_image
  web_image = var.web_image

  # Target groups from ALB
  api_target_group_arn = module.loadbalancer.api_target_group_arn
  web_target_group_arn = module.loadbalancer.web_target_group_arn

  # Secrets
  secrets_arns = module.secrets.all_secret_arns
  ghcr_credentials_arn = module.secrets.ghcr_credentials_arn

  # Environment variables
  database_url        = module.database.connection_url
  s3_bucket           = module.storage.bucket_name
  s3_region           = var.aws_region
  cors_origins        = join(",", var.cors_origins)
  jwt_issuer          = var.jwt_issuer
  jwt_audience        = var.jwt_audience
  email_from_address  = var.email_from_address
  email_from_name     = var.email_from_name
  email_web_base_url  = var.email_web_base_url
  next_public_api_url = var.next_public_api_url

  depends_on = [module.secrets, module.database, module.loadbalancer]
}
