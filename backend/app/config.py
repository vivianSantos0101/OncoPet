"""Configuracoes centrais da aplicacao."""

SECRET_KEY = "oncovet-dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# PostgreSQL (porta 5433 para nao conflitar)
DATABASE_URL = "postgresql://oncovet:oncovet123@localhost:5433/oncovet"

# MongoDB (porta 27018 para nao conflitar)
MONGODB_URL = "mongodb://localhost:27018"
MONGODB_DB_NAME = "oncovet_exams"
