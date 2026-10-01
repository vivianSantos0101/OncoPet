#!/usr/bin/env bash
# Cria o .env.prod com o endereco (IP + sslip.io) e senhas aleatorias.
# Uso (na pasta do projeto): bash deploy/gerar-env.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env.prod ]; then
  echo ".env.prod ja existe. Apague-o antes se quiser gerar de novo (as senhas dos bancos mudariam!)."
  exit 1
fi

IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
if [ -z "$IP" ]; then echo "Nao consegui descobrir o IP publico."; exit 1; fi
DOMAIN="${IP//./-}.sslip.io"

cat > .env.prod <<ENV
DOMAIN=$DOMAIN
POSTGRES_PASSWORD=$(openssl rand -hex 16)
MONGO_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENV
chmod 600 .env.prod

echo ".env.prod criado."
echo "Endereco do OncoPet: https://$DOMAIN"
