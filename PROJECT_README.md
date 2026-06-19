# EC2 Startup Runbook (Exact Order)

## Overview

This repository deploys and runs a live museum kiosk data pipeline on AWS.

- Infrastructure: Terraform provisions RDS PostgreSQL + EC2
- Runtime: EC2 runs the live Kafka consumer pipeline
- Deployment scripts: shell scripts in `pipeline/` automate setup and startup

## Repository Structure

- `pipeline/terraform/`: infrastructure definitions and variables
- `pipeline/populate_ec2.sh`: bootstraps EC2 and deploys project dependencies
- `pipeline/start_pipeline_on_ec2.sh`: starts live pipeline process on EC2
- `pipeline/live_pipeline.py`: long-running Kafka-to-Postgres consumer

## 0) Required Installs (Local Machine)

Install these first:

1. Terraform CLI
2. AWS CLI
3. Git
4. OpenSSH client (`ssh` and `scp`)
5. Bash shell

Also required:

- Valid AWS credentials configured for Terraform/AWS CLI access

## 1) Provide Required Inputs

You must provide these before running anything:

1. `pipeline/terraform/terraform.tfvars` with all variables required by `pipeline/terraform/variables.tf`
2. AWS credentials available to Terraform
3. `github_deploy_key` and `github_deploy_key.pub` in repo root

Do not create `.env` manually; Terraform generates it.

## 2) Create Infrastructure

From repo root:

```bash
cd pipeline/terraform
terraform init
terraform apply
cd ../..
```

Outputs used by later steps:

- `.env` in repo root
- `<EC2_KEY_PAIR_NAME>.pem` in repo root

## 3) Prepare EC2

From repo root:

```bash
chmod +x pipeline/*.sh
bash pipeline/populate_ec2.sh
```

This step:

- Copies deploy keys to EC2
- Clones `GITHUB_REPO_URL`
- Installs Python and project dependencies on EC2
- Copies `.env` to EC2

## 4) Start Live Pipeline

From repo root:

```bash
bash pipeline/initial_start_pipeline_on_ec2.sh
```

Starts `pipeline/live_pipeline.py --reset_db` on EC2 with `nohup`.

## 5) Verify Deployment

Connect to EC2:

```bash
bash pipeline/connect_to_ec2.sh
```

Check pipeline log output:

```bash
source .env
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"
tail -f ~/$REPO_DIR/pipeline/live_pipeline.log
```

Expected:

- Live pipeline process is running
- Log shows successful DB/Kafka initialization and batch inserts

## Files You Actually Run

- `pipeline/terraform/main.tf` (via Terraform in `pipeline/terraform/`)
- `pipeline/populate_ec2.sh`
- `pipeline/start_pipeline_on_ec2.sh`

## Important Constraint

EC2 scripts derive the clone directory from `GITHUB_REPO_URL`:

```bash
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"
```

This supports any repository name when cloning with default Git behavior (no custom target directory in `git clone`).

## Common Issues

- `terraform apply` fails:
	- Verify AWS credentials are configured and `terraform.tfvars` is complete.
- `populate_ec2.sh` fails on clone:
	- Verify `GITHUB_REPO_URL` is in `.env` and deploy keys are valid.
- `start_pipeline_on_ec2.sh` runs but no data appears:
	- Check `live_pipeline.log` and confirm Kafka/DB credentials in `.env`.
