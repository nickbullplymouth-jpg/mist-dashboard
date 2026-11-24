#!/usr/bin/env bash
set -e

echo "=== Setting up Mist Dashboard on Amazon Linux ==="

# 1. Update system packages
sudo dnf update -y || sudo yum update -y

# 2. Install Git, Python3, and pip
sudo dnf install -y git python3 python3-pip || sudo yum install -y git python3 python3-pip

# 3. Setup App Directory
APP_DIR="/opt/mist-dashboard"
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# 4. Copy current files or clone
cp -r ./* $APP_DIR/ 2>/dev/null || true

cd $APP_DIR

# 5. Virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Create systemd service
sudo bash -c "cat << 'EOF' > /etc/systemd/system/mist-dashboard.service
[Unit]
Description=Mist Org Dashboard Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF"

# 7. Reload and start systemd service
sudo systemctl daemon-reload
sudo systemctl enable mist-dashboard
sudo systemctl restart mist-dashboard

echo "=== Deployment Complete ==="
echo "Service is running on port 8000. Check status with: sudo systemctl status mist-dashboard"
