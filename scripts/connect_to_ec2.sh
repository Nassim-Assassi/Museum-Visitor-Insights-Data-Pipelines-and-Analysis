#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
source "$ENV_FILE"

: "${EC2_KEY_PAIR_NAME:?EC2_KEY_PAIR_NAME missing in .env}"
: "${EC2_INSTANCE_PUBLIC_IP:?EC2_INSTANCE_PUBLIC_IP missing in .env}"

PEM_FILE_NAME="$EC2_KEY_PAIR_NAME.pem"
PEM_FILE="$REPO_ROOT/$PEM_FILE_NAME"


# Edit these values once, then run the script.

SSH_USER="ec2-user"

ssh -o StrictHostKeyChecking=accept-new \
	-o ConnectTimeout=10 \
	-i "$PEM_FILE" \
	"$SSH_USER@$EC2_INSTANCE_PUBLIC_IP"