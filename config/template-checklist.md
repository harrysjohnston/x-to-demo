# Template checklist

Use this list after cloning the template.

## Customize

- Project name (`package.json`, Docker Compose name, docs)
- GitHub repo + GHCR image paths
- Terraform `project_name` and environment values
- JWT `JWT_ISSUER` / `JWT_AUDIENCE`
- Email sender name/address and support address
- Production domains and `NEXT_PUBLIC_API_URL`

## Do not commit

- `.env`, `.env.production`, `.env.*`
- `infra/terraform/terraform.tfvars`
- `infra/terraform/*.tfstate*`
- API keys, cloud credentials, private keys
