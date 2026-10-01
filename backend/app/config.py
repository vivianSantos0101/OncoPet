"""Configuracoes centrais da aplicacao.

Valores lidos de variaveis de ambiente (ver .env.example na raiz).
Os defaults batem com o docker-compose.yml para desenvolvimento local.
"""

import os

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
