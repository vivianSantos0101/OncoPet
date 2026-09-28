# OncoPet 🐾

Sistema de acompanhamento de quimioterapia veterinária (oncologia animal), com visão do veterinário e do tutor.

## Stack atual

- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy · PostgreSQL · MongoDB (Motor)
- **Frontend:** React 18 (Vite) · Axios · Recharts
- **Auth:** JWT com papéis `vet` e `tutor`

> A especificação técnica alvo (MySQL, TypeScript, NumPy, dashboard paliativo, PDF) está em
> [`docs/Requisitos_Tecnicos_OncoPet.pdf`](docs/Requisitos_Tecnicos_OncoPet.pdf).
> O que falta está em [`docs/ANALISE_REQUISITOS.md`](docs/ANALISE_REQUISITOS.md).

## Estrutura

```
OncoPet/
├── backend/
│   ├── app/
│   │   ├── main.py          # app FastAPI + registro de rotas
│   │   ├── config.py        # configurações via variáveis de ambiente
│   │   ├── database.py      # SQLAlchemy (PostgreSQL)
│   │   ├── mongodb.py       # Motor (MongoDB)
│   │   ├── models.py        # User, Clinic, Pet, ChemoProtocol, ChemoSession, PetRecord, Document, Reminder
│   │   ├── schemas.py
│   │   ├── services/        # regras de negócio (ex.: progresso de protocolos)
│   │   ├── auth.py          # JWT + dependências require_vet / get_current_user
│   │   ├── breeds.py
│   │   └── routers/         # auth, clinics, tutors, vets, pets, protocols, sessions,
│   │                        # records, documents, reminders, exams (Mongo), uploads
│   ├── scripts/             # seed_demo.py (dados de demonstração)
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx · api.js · main.jsx · index.css
│       ├── pages/           # Login, VetDashboard, TutorDashboard
│       └── components/      # PetDetail, ProtocolPanel, PetAgenda, Notifications, FileUpload
├── docs/
├── docker-compose.yml       # Postgres :5433 + Mongo :27018
└── .env.example
```

## Como rodar

```bash
# 1. Bancos
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://localhost:8000/docs

# 3. Frontend (outro terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

### Dados de demonstração

Com o backend rodando, popule o banco com pacientes, protocolos, sessões,
diário do tutor, lembretes e laudos fictícios:

```bash
cd backend
source .venv/bin/activate
python scripts/seed_demo.py
```

Logins criados (senha `oncopet123` para todos):

| Perfil | Usuários |
|---|---|
| Veterinário | `dra_ana`, `dr_marcos` |
| Tutor | `joao`, `mariana`, `carla`, `pedro`, `rafael` |

As datas são geradas a partir do dia em que o script roda. Para recomeçar do
zero: `docker compose down -v && docker compose up -d`, reinicie o backend e
rode o script de novo.

### Testes (backend)

Rodam com SQLite, sem precisar do Docker:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

As configurações têm defaults compatíveis com o `docker-compose.yml`. Para mudar, copie `.env.example` para `.env` e exporte as variáveis antes de subir o backend.

## Fórmula de superfície corporal

- **Cães:** SC (m²) = 0.101 × peso(kg)^0.734
- **Gatos:** SC (m²) = 0.101 × peso(kg)^0.667
