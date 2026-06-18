#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
source "$ENV_FILE"

PEM_FILE_NAME="$EC2_KEY_PAIR_NAME.pem"
PEM_FILE="$SCRIPT_DIR/../$PEM_FILE_NAME"


# Edit these values once, then run the script.

SSH_USER="ec2-user"

ssh -o StrictHostKeyChecking=accept-new \
	-T \
	-o ConnectTimeout=10 \
	-i "$PEM_FILE" \
	"$SSH_USER@$EC2_INSTANCE_PUBLIC_IP" \
	"cd ~/Coursework-Advanced-Data-Week-1 && sudo nohup .venv/bin/python pipeline/live_pipeline.py --reset_db > pipeline/live_pipeline.log 2>&1 &"