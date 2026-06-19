#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
source "$ENV_FILE"

# Check ENV variables
: "${GITHUB_REPO_URL:?GITHUB_REPO_URL missing in .env}"
: "${EC2_KEY_PAIR_NAME:?EC2_KEY_PAIR_NAME missing in .env}"
: "${EC2_INSTANCE_PUBLIC_IP:?EC2_INSTANCE_PUBLIC_IP missing in .env}"

REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"

PEM_FILE_NAME="$EC2_KEY_PAIR_NAME.pem"
PEM_FILE="$SCRIPT_DIR/../$PEM_FILE_NAME"


# Edit these values once, then run the script.

SSH_USER="ec2-user"


# send github deploy keys to the EC2 instance
scp -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=10 \
  -i "$PEM_FILE" \
  "$SCRIPT_DIR/../github_deploy_key" \
  "$SCRIPT_DIR/../github_deploy_key.pub" \
  "$SSH_USER@$EC2_INSTANCE_PUBLIC_IP:~/.ssh/"

ssh -o StrictHostKeyChecking=accept-new \
	-o ConnectTimeout=10 \
	-i "$PEM_FILE" \
  "$SSH_USER@$EC2_INSTANCE_PUBLIC_IP" "GITHUB_REPO_URL='$GITHUB_REPO_URL' bash -s" << 'EOF'
set -euo pipefail
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"
sudo yum update -y
sudo yum install -y git 
sudo yum install -y python3.14
sudo yum install -y python-pip

sudo rm -rf "$REPO_DIR"

GIT_SSH_COMMAND="ssh -i ~/.ssh/github_deploy_key -o StrictHostKeyChecking=no" \
git clone "$GITHUB_REPO_URL"

cd "$REPO_DIR"
python3.14 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# copy the .env file to the EC2 instance
scp -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=10 \
  -i "$PEM_FILE" \
  "$ENV_FILE" \
  "$SSH_USER@$EC2_INSTANCE_PUBLIC_IP:~/$REPO_DIR/.env" 