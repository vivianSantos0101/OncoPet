"""Configuracoes centrais da aplicacao.

Valores lidos de variaveis de ambiente (ver .env.example na raiz).
Os defaults batem com o docker-compose.yml para desenvolvimento local.
"""

import os
import socket

SECRET_KEY = os.getenv("SECRET_KEY", "oncopet-dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 horas

# Cookie de sessao (o token JWT fica num cookie HttpOnly, fora do alcance do JavaScript)
AUTH_COOKIE_NAME = "oncopet_session"
# Em producao com HTTPS: COOKIE_SECURE=true (o cookie so trafega criptografado)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

# Banco relacional principal (porta 5433 para nao conflitar com instalacao local)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://oncopet:oncopet123@localhost:5433/oncopet")

# MongoDB - historico / exames (porta 27018 para nao conflitar)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27018")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "oncopet_exams")

# Nome desta copia do backend (backend1, backend2...). Com varias copias atras do
# load balancer, aparece no cabecalho X-Backend-Instance e em /api/health.
INSTANCE_NAME = os.getenv("INSTANCE_NAME") or socket.gethostname()

# Endereco do site, usado no link enviado por e-mail (ex.: https://3-228-54-7.sslip.io).
# Vem da configuracao, nunca do pedido: assim ninguem forja um link para outro site.
APP_URL = (os.getenv("APP_URL") or "http://localhost:5173").rstrip("/")

# Recuperacao de senha: o link vale RESET_TOKEN_MINUTES; um novo pedido para a
# mesma conta so gera outro e-mail depois de RESET_COOLDOWN_SECONDS
RESET_TOKEN_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
RESET_COOLDOWN_SECONDS = int(os.getenv("RESET_COOLDOWN_SECONDS", "60"))

# Servidor de e-mail (SMTP). Sem SMTP_HOST o e-mail nao sai: aparece no log do
# backend (desenvolvimento e testes). Gmail: smtp.gmail.com, porta 587, senha de app.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
