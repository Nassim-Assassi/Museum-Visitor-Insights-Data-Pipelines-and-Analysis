#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

# Edit these values once, then run the script.
EC2_HOST=""
SSH_KEY_PATH="$SCRIPT_DIR/../c24-nassim-museum-ec2-kp.pem"
SSH_USER="ubuntu"
REPO_URL="https://github.com/nassimassassi/Coursework-Advanced-Data-Week-1.git"
BRANCH="main"
APP_DIR="/home/ubuntu/Coursework-Advanced-Data-Week-1"

if [[ -z "$EC2_HOST" ]]; then
  echo "Error: set EC2_HOST in this script before running." >&2
  exit 1
fi

if [[ ! -f "$SSH_KEY_PATH" ]]; then
  echo "Error: SSH key not found: $SSH_KEY_PATH" >&2
  exit 1
fi

chmod 600 "$SSH_KEY_PATH"

SSH_OPTS=(
  -i "$SSH_KEY_PATH"
  -o StrictHostKeyChecking=accept-new
  -o UserKnownHostsFile=/dev/null
)

echo "[1/3] Preparing EC2 packages and directory..."
ssh "${SSH_OPTS[@]}" "$SSH_USER@$EC2_HOST" "bash -s" <<EOF
set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y git python3 python3-venv python3-pip
mkdir -p "$APP_DIR"
sudo chown -R "$SSH_USER:$SSH_USER" "$APP_DIR"
EOF

echo "[2/3] Cloning or updating repository..."
ssh "${SSH_OPTS[@]}" "$SSH_USER@$EC2_HOST" "bash -s" <<EOF
set -euo pipefail
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch --all
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

if [[ -f "$APP_DIR/requirements.txt" ]]; then
  python3 -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/pip" install --upgrade pip
  "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
fi
EOF

echo "[3/3] Uploading .env to EC2..."
scp "${SSH_OPTS[@]}" "$SCRIPT_DIR/../.env" "$SSH_USER@$EC2_HOST:$APP_DIR/.env"
ssh "${SSH_OPTS[@]}" "$SSH_USER@$EC2_HOST" "chmod 600 '$APP_DIR/.env'"

echo "Done. EC2 prepared at: $APP_DIR"
