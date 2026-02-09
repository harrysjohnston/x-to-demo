# Deployment Guide

This guide covers deployment strategies for the fullstack template, from manual Docker deployment to automated AWS infrastructure.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Manual Deployment](#manual-deployment)
- [Database Migrations](#database-migrations)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Rollback Procedures](#rollback-procedures)
- [AWS Transition Path](#aws-transition-path)
- [Troubleshooting](#troubleshooting)

## Overview

The deployment strategy uses Docker containers published to GitHub Container Registry (GHCR) and GitHub Actions to deploy to AWS ECS for staging and production. Manual Docker deployment remains available for self-hosting. This approach provides:

- **Portability**: Same images work locally, on any cloud, or on-premise
- **Consistency**: Build once, deploy anywhere
- **Traceability**: Images tagged with git commit SHA
- **AWS-ready**: Automated ECS Fargate deployments for staging and production

### Architecture

```
┌─────────────────────────────────────────────────┐
│               GitHub Actions                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Build   │→ │   Test   │→ │  Push GHCR   │ │
│  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────┘
                      ↓
              ┌──────────────┐
              │     GHCR     │
              │  (Registry)  │
              └──────────────┘
                      ↓
       ┌──────────────┴──────────────┐
       ↓                              ↓
┌─────────────┐              ┌──────────────┐
│   Manual    │              │     AWS      │
│ Deployment  │              │  ECS/Fargate │
│ (Optional)  │              │ (Stg + Prod) │
└─────────────┘              └──────────────┘
```

### Branch Flow

- `development` → `staging` → `main`
- Pushes to `staging` deploy to the staging environment
- Pushes to `main` deploy to production

## Prerequisites

### For Manual Deployment

- Docker and Docker Compose installed
- Access to GitHub Container Registry (pull permission)
- PostgreSQL database (managed or self-hosted)
- Environment variables configured

### For GitHub Actions

- GitHub repository with Actions enabled
- GitHub Environments: `staging` and `production`
- AWS OIDC role per environment (recommended) with ECS, RDS, Secrets Manager, and IAM PassRole permissions
- Required environment secrets:
  - `AWS_ROLE_ARN`
  - `DB_PASSWORD`
  - `JWT_SECRET`
- Required environment variables:
  - `S3_BUCKET_NAME`
- Optional (recommended) environment secrets/vars:
  - `GHCR_TOKEN` (for private GHCR pulls and pushes)
  - `GHCR_USERNAME` (for private GHCR pulls)
  - `CERTIFICATE_ARN` (if enabling HTTPS)
  - `CORS_ORIGINS` (JSON array string, e.g. `["https://staging.example.com"]`)
  - `ENABLE_HTTPS` (`true` or `false`)
  - `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, `EMAIL_WEB_BASE_URL`
  - `NEXT_PUBLIC_API_URL`
  - `AWS_REGION` (defaults to `us-east-1`)

## Manual Deployment

### 1. Authenticate with GHCR

```bash
# Create a GitHub Personal Access Token with read:packages scope
# Then login to GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### 2. Pull Latest Images

```bash
# Replace OWNER/REPO with your GitHub username/repo
export IMAGE_PREFIX="ghcr.io/OWNER/REPO"

docker pull ${IMAGE_PREFIX}-api:latest
docker pull ${IMAGE_PREFIX}-web:latest
```

### 3. Prepare Environment

Create a `.env.production` file. You can generate one interactively:

```bash
# Interactive prompts for key deployment variables (optional; local dev does not need this)
pnpm deploy:configure
# or: ./scripts/configure-deploy
```

Or create `.env.production` manually:

```bash
# Required settings
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Database
DATABASE_URL=postgresql+psycopg://user:password@db-host:5432/dbname

# JWT
JWT_SECRET=your-production-secret-here
JWT_ISSUER=your-app-name
JWT_AUDIENCE=your-app-name

# CORS
CORS_ORIGINS=https://your-domain.com

# Storage (S3)
STORAGE_PROVIDER=s3
S3_BUCKET=your-production-bucket
S3_REGION=us-east-1
# S3_ENDPOINT_URL not needed for real AWS S3
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key

# Email
EMAIL_ENABLED=true
EMAIL_FROM_ADDRESS=noreply@your-domain.com
EMAIL_FROM_NAME=Your App
EMAIL_WEB_BASE_URL=https://your-domain.com
EMAIL_SUPPORT_ADDRESS=support@your-domain.com

# Web
NEXT_PUBLIC_API_URL=https://api.your-domain.com/api/v1
```

### 4. Create Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
name: fullstack-template-production

services:
  api:
    image: ${IMAGE_PREFIX}-api:latest
    restart: unless-stopped
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  web:
    image: ${IMAGE_PREFIX}-web:latest
    restart: unless-stopped
    env_file:
      - .env.production
    ports:
      - "3000:3000"
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  # Optional: Include database if self-hosting
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
```

### 5. Deploy

```bash
# Set your image prefix
export IMAGE_PREFIX="ghcr.io/OWNER/REPO"

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check health
curl http://localhost:8000/health
```

## Database Migrations

### Migration Safety Script

The `apps/api/scripts/migrate.py` script provides safe migration execution with:

- **Pre-flight checks**: Connectivity, pending migrations, destructive operation detection
- **Dry-run mode**: Preview migrations without applying
- **Backup verification**: Ensures backups exist before applying
- **Post-migration validation**: Verifies schema integrity
- **Detailed logging**: All operations are logged with timestamps

### Running Migrations

#### Local Development

```bash
cd apps/api

# Check current database version
python scripts/migrate.py current

# Preview pending migrations (dry-run)
python scripts/migrate.py upgrade --dry-run

# Apply migrations
python scripts/migrate.py upgrade
```

#### GitHub Actions (ECS)

On staging and production deploys, GitHub Actions runs migrations inside the VPC using an ECS run-task. This avoids public database access and keeps migrations close to the database.

To run a migration task manually:

```bash
# Replace with your workspace outputs
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
TASK_DEF=$(terraform output -raw api_task_definition_arn)
SUBNETS=$(terraform output -json private_subnet_ids | jq -r 'join(",")')
SECURITY_GROUP=$(terraform output -raw ecs_security_group_id)

aws ecs run-task \
  --cluster "$ECS_CLUSTER" \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"api","command":["python","scripts/migrate.py","upgrade","--no-backup-check"]}]}'
```

#### Production Deployment

```bash
cd apps/api

# Always dry-run first in production
DATABASE_URL=$PRODUCTION_DB_URL python scripts/migrate.py upgrade --dry-run

# If dry-run looks good, apply migrations
# Note: Ensure database backups are enabled at the infrastructure level
DATABASE_URL=$PRODUCTION_DB_URL python scripts/migrate.py upgrade --no-backup-check

# Verify migration succeeded
DATABASE_URL=$PRODUCTION_DB_URL python scripts/migrate.py current
```

#### Migration Flags

- `--dry-run`: Preview without applying changes
- `--no-backup-check`: Skip backup verification (use when backups are automated)
- `--allow-destructive`: Allow DROP/TRUNCATE operations
- `--target <revision>`: Migrate to specific revision instead of head

### Creating New Migrations

```bash
cd apps/api

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration file in alembic/versions/
# Edit if necessary to ensure safety

# Test locally
python scripts/migrate.py upgrade --dry-run
```

### Migration Best Practices

1. **Always test migrations locally first**
2. **Review auto-generated migrations** - Alembic may not detect all changes
3. **Avoid destructive operations in production** without explicit approval
4. **Keep migrations reversible** - Write downgrade functions
5. **Coordinate with deployments** - Ensure backward-compatible schema changes
6. **Backup before major migrations** - Use your database provider's backup tools

## GitHub Actions CI/CD

### CI Workflow (Pull Requests)

On every PR, the CI workflow runs:

1. **Web checks**: Biome (linting), Vitest (unit tests), Playwright (e2e tests)
2. **API checks**: Ruff (linting), Pytest (unit tests)
3. **Docker builds**: Build both production images and test health endpoints

This ensures PRs don't break production builds.

### Deploy Workflow (Push to staging or main)

On push to `staging` or `main`, the deploy workflow:

1. **Builds images**: Creates production Docker images for API and Web
2. **Tags images**:
   - `{branch}-{sha}` - specific commit (e.g. `staging-abc1234`)
   - `{branch}` - rolling tag for the branch
   - `latest` - most recent main branch build (production only)
3. **Pushes to GHCR**: Images published to GitHub Container Registry
4. **Applies Terraform**: Updates ECS task definitions and services in the target workspace (`staging` or `prod`)
5. **Runs migrations**: Executes migrations as an ECS task inside the VPC
6. **Creates release**: GitHub release with deployment summary (production only)

### Setting Up Secrets

Configure GitHub Environments for `staging` and `production` with these secrets/variables.

**Secrets**

- `AWS_ROLE_ARN`: OIDC role to assume for the environment
- `DB_PASSWORD`: RDS master password (used by Terraform and stored in Secrets Manager)
- `JWT_SECRET`: JWT signing secret
- `GHCR_TOKEN` (optional): PAT with `write:packages` for GHCR push + ECS private pulls
- `GHCR_USERNAME` (optional): GHCR username for ECS private pulls
- `CERTIFICATE_ARN` (optional): ACM certificate ARN for HTTPS

**Variables**

- `S3_BUCKET_NAME`: S3 bucket for uploads
- `AWS_REGION` (optional): defaults to `us-east-1`
- `CORS_ORIGINS` (optional): JSON array string, e.g. `["https://staging.example.com"]`
- `ENABLE_HTTPS` (optional): `true` or `false`
- `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, `EMAIL_WEB_BASE_URL` (optional)
- `NEXT_PUBLIC_API_URL` (optional)

The `GITHUB_TOKEN` is automatically provided by Actions for GHCR authentication. If GHCR pushes return 403, set `GHCR_TOKEN` and grant `write:packages`.

### Manual Workflow Trigger

You can manually trigger deployment from GitHub Actions:

1. Go to Actions → Deploy
2. Click "Run workflow"
3. Choose the target environment (`staging` or `production`)
4. Optionally check "Skip database migration" if needed

## Rollback Procedures

### Rolling Back Code

#### Option 1: Redeploy Previous Image

```bash
# Find previous successful deployment
gh release list

# Pull the specific version
docker pull ghcr.io/OWNER/REPO-api:main-abc1234
docker pull ghcr.io/OWNER/REPO-web:main-abc1234

# Update docker-compose to use specific tags
# Then restart services
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 2: Revert Git Commit

```bash
# Revert the problematic commit
git revert <commit-hash>
git push origin main

# This triggers a new deployment with the revert
```

### Rolling Back Database Migrations

⚠️ **Caution**: Database rollbacks are risky. Always backup first.

```bash
cd apps/api

# View migration history
python scripts/migrate.py history

# Downgrade to previous revision
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade <revision>

# Verify
python scripts/migrate.py current
```

### Rollback Checklist

- [ ] Identify the last known good deployment
- [ ] Backup current database state
- [ ] Check for data migrations that may have modified data
- [ ] Coordinate with team - announce maintenance window if needed
- [ ] Rollback application code first
- [ ] Test application with current database schema
- [ ] Only rollback database if necessary
- [ ] Verify application health after rollback
- [ ] Document what went wrong and update runbooks

## AWS Deployment (Terraform + ECS)

GitHub Actions deploys staging and production by applying Terraform and updating ECS task definitions.

```
GitHub Actions → GHCR → AWS ECS Fargate
                         ↓
                    AWS RDS PostgreSQL
                    AWS S3
                    AWS Secrets Manager
                    AWS ALB
```

### Workspaces

- `default` → `dev`
- `staging` → `staging`
- `prod` → `production`

The deploy workflow automatically selects `staging` for the `staging` branch and `prod` for `main`.

### Remote State (Recommended)

CI deployments require shared state. Use the S3 backend in `infra/terraform/backend.tf` and enable DynamoDB locking before enabling GitHub Actions deploys.

### Updating Images

Terraform receives `api_image` and `web_image` variables from the workflow and updates ECS task definitions for the target workspace.

### Cost Control / Pause

Short-term (manual):

```bash
aws ecs update-service --cluster <cluster> --service <service> --desired-count 0
aws rds stop-db-instance --db-instance-identifier <identifier>
```

Terraform-managed:

- Set `ecs_desired_count_override = 0`
- Set `ecs_ignore_desired_count = false`
- Apply Terraform for the workspace

Full teardown:

```bash
terraform destroy
```

## Troubleshooting

### Images Won't Pull from GHCR

**Problem**: `Error response from daemon: unauthorized`

**Solution**:
```bash
# Ensure package is public in GitHub settings, or
# Login with proper credentials
echo $GHCR_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

For ECS private pulls, ensure `GHCR_USERNAME` and `GHCR_TOKEN` are set and Terraform creates the `/ENV/ghcr` Secrets Manager secret. The ECS execution role must have access to that secret.

### Migration Fails with "Destructive Operation Detected"

**Problem**: Migration script blocks DROP/ALTER operations

**Solution**:
```bash
# Review the migration carefully
python scripts/migrate.py upgrade --dry-run

# If safe to proceed
python scripts/migrate.py upgrade --allow-destructive
```

### Container Exits Immediately

**Problem**: Container starts but exits right away

**Solution**:
```bash
# Check logs
docker logs <container-name>

# Common issues:
# - Missing required environment variables
# - Database connection failure
# - Port already in use

# Verify environment variables
docker exec <container-name> env
```

### Health Check Failing

**Problem**: Container shows "unhealthy" status

**Solution**:
```bash
# Check health endpoint manually
docker exec <container-name> curl localhost:8000/health

# View detailed logs
docker logs <container-name>

# Adjust health check timing if startup is slow
# Increase start_period in docker-compose.yml
```

### Migration Script Can't Connect to Database

**Problem**: `OperationalError: could not connect to server`

**Solution**:
```bash
# Verify DATABASE_URL is correct
echo $DATABASE_URL

# Test connectivity manually
psql $DATABASE_URL -c "SELECT 1"

# Check if database is running (if self-hosted)
docker-compose ps db

# Check firewall rules (cloud databases)
```

### GitHub Actions Workflow Fails

**Problem**: Deploy workflow fails to push images

**Solution**:
1. Check workflow logs in GitHub Actions tab
2. Verify repository has packages write permission
3. Ensure `PRODUCTION_DATABASE_URL` secret is set
4. Check that Docker builds succeed in CI workflow first

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

For questions or issues, see the repository's issue tracker or refer to the README.
