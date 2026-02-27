#!/usr/bin/env bash
set -euo pipefail

echo "=== DeutschLerner Deploy ==="

DEPLOY_DIR="${DEPLOY_DIR:-/opt/deutsch-lerner}"
SERVICE_NAME="deutsch-lerner"
USE_DOCKER="${USE_DOCKER:-false}"

if [ "$USE_DOCKER" = "true" ]; then
    echo "Deploying with Docker..."
    docker-compose down || true
    docker-compose build
    docker-compose up -d
    echo "✅ Docker deployment complete!"
    echo "Check status: docker-compose ps"
else
    echo "Deploying with systemd..."

    # Copy files
    sudo mkdir -p "$DEPLOY_DIR"
    sudo rsync -av --exclude='.venv' --exclude='data/*.db' --exclude='.git' \
        . "$DEPLOY_DIR/"

    # Setup venv
    cd "$DEPLOY_DIR"
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    .venv/bin/pip install -r requirements.txt

    # Run migrations
    .venv/bin/python main.py migrate

    # Install systemd service
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=DeutschLerner German Learning Assistant
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${DEPLOY_DIR}
EnvironmentFile=${DEPLOY_DIR}/.env
ExecStart=${DEPLOY_DIR}/.venv/bin/python -m uvicorn src.api.server:create_app --factory --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl restart ${SERVICE_NAME}

    echo "✅ Systemd deployment complete!"
    echo "Check status: sudo systemctl status ${SERVICE_NAME}"
fi
