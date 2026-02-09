# Staging + Production Cloud Deployments

Goal: pushes to `staging` and `main` trigger cloud deployments; PRs flow from `development` → `staging` (deploy) → `main` (prod deploy). Provide a way to pause/scale down deployments to save cost.

## Current State (from codebase)

- Deploy workflow runs only on `main` and only builds/pushes images to GHCR, runs migrations using `PRODUCTION_DATABASE_URL`, and creates a release. It does not deploy to AWS ECS. (`.github/workflows/deploy.yml`)
- GHCR push is failing with 403 during `docker buildx` push. Likely due to GHCR permissions, image naming/ownership mismatch, or repo-level workflow permissions.
- Terraform supports environments via workspaces, but only `dev`/`prod` configs are defined in `infra/terraform/main.tf`. No `staging` config.
- ECS tasks pull images directly from GHCR (no ECR). There is no GHCR credential configured for ECS, so images must be public or ECS must be given GHCR credentials via Secrets Manager.
- Migrations run in GitHub Actions using a DB URL secret. If the DB is private in AWS (RDS in private subnets), GitHub Actions cannot reach it; migrations should run inside ECS (run-task) or via a private network runner.

## Known Credential Requirements (and fixes)

- **GitHub Actions → GHCR push**: Ensure `GITHUB_TOKEN` has `packages: write` and repo Actions “Workflow permissions” set to **Read and write**. If still 403, use a PAT with `write:packages` in `GHCR_TOKEN` and update `docker/login-action` to use it.
- **Terraform (local)**: Requires AWS CLI credentials (profile, env vars, or SSO) with permissions to create VPC, ECS, RDS, ALB, S3, Secrets Manager, IAM, CloudWatch, etc.
- **GitHub Actions → AWS deploy**: Use GitHub OIDC to assume an AWS role (recommended), or store `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in GitHub Environments. Role needs ECS update, Secrets Manager read (if running migration task), and possibly `iam:PassRole`.
- **ECS pulls from GHCR (private images)**: Add an AWS Secrets Manager secret containing a GHCR PAT (`username`, `password`), and set `repositoryCredentials` in ECS task definitions so Fargate can pull private images. Do this per environment if needed.
- **Scripts that touch S3 (local)**: `scripts/create-s3-bucket` uses `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` or default AWS creds. Set env vars or configure AWS CLI profile before running.

## Plan

1. **Fix GHCR push 403 (expanded checks)**
   - **Confirm image namespace**: the workflow builds `ghcr.io/<owner>/<repo>-api` and `-web`. If the log shows a different repo slug (e.g., `fullstack-template-api` vs `fullstack-template-1-api`), the push will 403. Align `IMAGE_PREFIX` or rename the package.
   - **Workflow permissions**: repo settings → Actions → Workflow permissions = **Read and write** (required for `GITHUB_TOKEN` to publish packages).
   - **Package access**: if the package already exists, ensure the repository has access to it (GHCR package settings → Manage access). If it’s org-owned, confirm Actions is allowed to create/update packages.
   - **Private repo + GHCR**: use a PAT with `write:packages` (and `repo` if needed), store as `GHCR_TOKEN`, and update `docker/login-action` to use that secret.

2. **Add staging deployments in GitHub Actions**
   - Update `.github/workflows/deploy.yml` to trigger on `push` to `staging` and `main`.
   - Use GitHub Environments (`staging`, `production`) and per‑environment secrets (e.g., `STAGING_DATABASE_URL`, `PRODUCTION_DATABASE_URL`).
   - Ensure the workflow chooses the right environment based on branch.

3. **Wire AWS deployment after image push (Terraform in CI)**
   - Use `terraform apply` in GitHub Actions per environment; set up remote state + locking (S3 + DynamoDB) to avoid concurrency issues.
   - Workflow should pass `api_image` / `web_image` variables using the image tags produced by the build step.
   - Configure AWS credentials in Actions via OIDC (preferred) with an environment‑specific role.
   - Add GHCR pull credentials to Secrets Manager and reference them in ECS task definitions (`repositoryCredentials`).

4. **Move migrations into AWS (if RDS is private)**
   - Add a migration task definition or reuse the API task with command override.
   - Replace GitHub Actions migration step with `aws ecs run-task` in the target VPC.

5. **Add a staging workspace/config in Terraform (cheap staging)**
   - Extend `infra/terraform/main.tf` locals to include `staging` settings (smallest viable instance sizes, desired_count=1, single NAT gateway).
   - Use `terraform workspace select staging` in CI and apply environment‑specific variables (tfvars or defaults).

6. **Spin‑down strategy (cost control)**
   - Short‑term: provide runbook to scale ECS services to 0 and optionally stop RDS:
     - `aws ecs update-service --desired-count 0` (staging)
     - `aws rds stop-db-instance` (for dev/staging; note 7‑day limit)
   - Medium‑term: add Terraform variables to override `ecs_desired_count` per env and support a “paused” mode.
   - Full savings: `terraform destroy` for staging and recreate when needed.

7. **Document the flow**
   - Update `docs/deployment.md` with staging/prod branch flow, secrets list, and restart/runbook steps.

## Open Questions

- Do you want staging to mirror production sizing or be cheaper?
- Should staging images be public (simpler ECS) or private (more secure)?
- Are you OK with Terraform apply from CI, or prefer a manual apply step?
