#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
source "$ENV_FILE"

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
	"$SSH_USER@$EC2_INSTANCE_PUBLIC_IP" << 'EOF'
set -euo pipefail
sudo yum update -y
sudo yum install -y git 
sudo yum install -y python3.14
sudo yum install -y python-pip

sudo rm -rf Coursework-Advanced-Data-Week-1

GIT_SSH_COMMAND="ssh -i ~/.ssh/github_deploy_key -o StrictHostKeyChecking=no" \
git clone git@github.com:Nassim-Assassi/Coursework-Advanced-Data-Week-1.git

cd Coursework-Advanced-Data-Week-1
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
  "$SSH_USER@$EC2_INSTANCE_PUBLIC_IP:~/Coursework-Advanced-Data-Week-1/.env" 