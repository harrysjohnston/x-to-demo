# -----------------------------------------------------------------------------
# Terraform Backend Configuration
# -----------------------------------------------------------------------------
#
# This file configures where Terraform stores its state file.
#
# LOCAL STATE (default):
# - State is stored locally in terraform.tfstate
# - Suitable for single-developer projects
# - State file should NOT be committed to git
#
# REMOTE STATE (recommended for teams):
# - Uncomment the S3 backend configuration below
# - Create the S3 bucket and DynamoDB table first (see instructions)
# - Enables state locking and team collaboration
#
# -----------------------------------------------------------------------------

# Uncomment below for remote state storage with S3 + DynamoDB locking
# This is recommended for production and team environments.
#
# Prerequisites:
# 1. Create an S3 bucket for state storage:
#    aws s3api create-bucket --bucket YOUR-STATE-BUCKET --region us-east-1
#
# 2. Enable versioning on the bucket:
#    aws s3api put-bucket-versioning --bucket YOUR-STATE-BUCKET \
#      --versioning-configuration Status=Enabled
#
# 3. Create a DynamoDB table for state locking:
#    aws dynamodb create-table --table-name terraform-locks \
#      --attribute-definitions AttributeName=LockID,AttributeType=S \
#      --key-schema AttributeName=LockID,KeyType=HASH \
#      --billing-mode PAY_PER_REQUEST
#
# 4. Update the bucket name below and uncomment the backend block

# terraform {
#   backend "s3" {
#     bucket         = "your-terraform-state-bucket"
#     key            = "fullstack-template/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "terraform-locks"
#     encrypt        = true
#   }
# }
