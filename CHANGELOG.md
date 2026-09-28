# Changelog

## [0.1.0] - 2026-09-28

### Adicionado
- Backend FastAPI com autenticação JWT (papéis vet e tutor), clínicas, pacientes,
  sessões de quimio com cálculo de dose por superfície corporal, registros diários,
  documentos, lembretes, exames no MongoDB e upload de arquivos.
- Frontend React/Vite com login, dashboards do veterinário e do tutor.
- docker-compose com PostgreSQL e MongoDB; configuração via variáveis de ambiente.
- Especificação técnica e análise de lacunas em `docs/`.

### Alterado
- Projeto renomeado de OncoVet para OncoPet.
