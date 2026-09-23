#!/bin/bash
# ============================================
# Script to setup k3s + Traefik + DuckDNS + Let's Encrypt
# Run this on your GCP VM (Ubuntu 22.04 LTS)
# ============================================

set -euo pipefail

DUCKDNS_SUBDOMAIN="${DUCKDNS_SUBDOMAIN:-plant-disease-demo}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
CERT_EMAIL="${CERT_EMAIL:-team@example.com}"
CERT_MANAGER_VERSION="${CERT_MANAGER_VERSION:-v1.16.2}"

echo "============================================"
echo " K3s Setup Script"
echo "============================================"

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Step 1: Install k3s (with Traefik enabled)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" sh -

# Setup kubeconfig
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config

# Step 2: Install Helm
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Step 3: Install cert-manager for Let's Encrypt certificates
echo "Installing cert-manager..."
kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml"

# Step 4: Setup DuckDNS updater without requiring Docker
echo "Setting up DuckDNS..."
if [ -n "$DUCKDNS_TOKEN" ]; then
    sudo tee /usr/local/bin/update-duckdns.sh >/dev/null <<EOF
#!/bin/sh
curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=" >/dev/null
EOF
    sudo chmod +x /usr/local/bin/update-duckdns.sh

    sudo tee /etc/systemd/system/duckdns-update.service >/dev/null <<'EOF'
[Unit]
Description=Update DuckDNS record

[Service]
Type=oneshot
ExecStart=/usr/local/bin/update-duckdns.sh
EOF

    sudo tee /etc/systemd/system/duckdns-update.timer >/dev/null <<'EOF'
[Unit]
Description=Run DuckDNS update every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=duckdns-update.service

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable --now duckdns-update.timer
    sudo systemctl start duckdns-update.service
    echo "DuckDNS systemd updater configured for: $DUCKDNS_SUBDOMAIN.duckdns.org"
else
    echo "WARNING: DUCKDNS_TOKEN not set. Please configure DuckDNS manually."
fi

echo ""
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo ""
echo "kubectl is ready. Namespace: plant-disease"
echo ""
echo "Next steps:"
echo "1. Set GitHub Secrets (GCP_VM_HOST, GCP_VM_USER, GCP_VM_SSH_KEY)"
echo "2. Push code to main branch to trigger CI/CD"
echo "3. Helm chart will auto-deploy after CI/CD push step"
