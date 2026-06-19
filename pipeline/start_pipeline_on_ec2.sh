#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
source "$ENV_FILE"

: "${GITHUB_REPO_URL:?GITHUB_REPO_URL missing in .env}"
: "${EC2_KEY_PAIR_NAME:?EC2_KEY_PAIR_NAME missing in .env}"
: "${EC2_INSTANCE_PUBLIC_IP:?EC2_INSTANCE_PUBLIC_IP missing in .env}"
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"

PEM_FILE_NAME="$EC2_KEY_PAIR_NAME.pem"
PEM_FILE="$SCRIPT_DIR/../$PEM_FILE_NAME"


# Edit these values once, then run the script.

SSH_USER="ec2-user"

ssh -o StrictHostKeyChecking=accept-new \
	-T \
	-o ConnectTimeout=10 \
	-i "$PEM_FILE" \
	"$SSH_USER@$EC2_INSTANCE_PUBLIC_IP" \
	"cd ~/$REPO_DIR && sudo -n nohup .venv/bin/python pipeline/live_pipeline.py > pipeline/live_pipeline.log 2>&1 < /dev/null &"