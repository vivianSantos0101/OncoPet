# Backend do OncoPet (FastAPI) para producao
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Roda sem ser root; a pasta de uploads vira um volume (fotos e laudos)
RUN useradd --create-home oncopet && mkdir -p app/uploads && chown -R oncopet app/uploads
USER oncopet

EXPOSE 8000

# --proxy-headers: confia no Caddy (HTTPS) para saber o endereco e o protocolo reais
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
