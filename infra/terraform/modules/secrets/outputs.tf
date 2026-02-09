output "database_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.database.arn
}

output "jwt_secret_arn" {
  description = "ARN of the JWT secret"
  value       = aws_secretsmanager_secret.jwt.arn
}

output "app_secret_arn" {
  description = "ARN of the app secrets"
  value       = aws_secretsmanager_secret.app.arn
}

output "ghcr_credentials_arn" {
  description = "ARN of the GHCR credentials secret (if configured)"
  value       = var.ghcr_token != "" ? aws_secretsmanager_secret.ghcr[0].arn : ""
}

output "all_secret_arns" {
  description = "List of all secret ARNs"
  value = compact([
    aws_secretsmanager_secret.database.arn,
    aws_secretsmanager_secret.jwt.arn,
    aws_secretsmanager_secret.app.arn,
    var.ghcr_token != "" ? aws_secretsmanager_secret.ghcr[0].arn : ""
  ])
}

output "read_secrets_policy_arn" {
  description = "ARN of the IAM policy for reading secrets"
  value       = aws_iam_policy.read_secrets.arn
}
