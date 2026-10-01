#!/usr/bin/env bash
# Prepara uma instancia Ubuntu (EC2) para rodar o OncoPet.
# Uso: sudo bash deploy/preparar-ubuntu.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode com sudo: sudo bash deploy/preparar-ubuntu.sh"; exit 1
fi
USUARIO="${SUDO_USER:-ubuntu}"

echo "==> 1/3 Memoria virtual (swap de 2 GB): a t2.micro/t3.micro tem so 1 GB de RAM"
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
sysctl -w vm.swappiness=10 >/dev/null
grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf

echo "==> 2/3 Docker e Docker Compose"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
usermod -aG docker "$USUARIO"
systemctl enable --now docker

echo "==> 3/3 Atualizacoes de seguranca automaticas"
apt-get install -y unattended-upgrades >/dev/null

echo
free -h
echo
echo "Pronto! Saia e entre de novo no SSH (exit) para usar o docker sem sudo."
