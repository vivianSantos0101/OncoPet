# OncoVet 🐾

Sistema de gerenciamento de quimioterapia veterinária para oncologia animal.

## Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy / SQLite
- **Frontend:** React (Vite) / Axios
- **Autenticação:** JWT (usuário/senha)

## Estrutura do Projeto

```
OncoVet/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── tutors.py
│   │       ├── pets.py
│   │       └── sessions.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   └── Dashboard.jsx
│   │   └── components/
│   │       ├── PetForm.jsx
│   │       ├── DoseCalculator.jsx
│   │       ├── SessionForm.jsx
│   │       └── Timeline.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Como rodar

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Requisitos Funcionais (MVP)

| ID   | Descrição |
|------|-----------|
| RF01 | Cadastrar pet (nome, espécie, raça, peso) vinculado a tutor |
| RF02 | Calcular superfície corporal (peso kg → m²) e dose automática |
| RF03 | Registrar sessão (data, quimioterápico, dose, observações) |
| RF04 | Exibir histórico/linha do tempo com evolução de peso |

## Requisitos Não Funcionais (MVP)

| ID    | Descrição |
|-------|-----------|
| RNF01 | Stack enxuta: FastAPI + SQLite + React SPA |
| RNF02 | Autenticação JWT simples (sem níveis de permissão) |
| RNF03 | Interface integrada: ver pet, calcular dose e registrar sessão na mesma tela |

## Fórmula de Superfície Corporal

- **Cães:** SC (m²) = 0.101 × peso(kg)^0.734
- **Gatos:** SC (m²) = 0.101 × peso(kg)^0.667
