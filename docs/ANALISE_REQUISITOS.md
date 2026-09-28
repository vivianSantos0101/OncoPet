# Análise: especificação × código atual

Referência: [`Requisitos_Tecnicos_OncoPet.pdf`](Requisitos_Tecnicos_OncoPet.pdf).
Legenda: ✅ atendido · 🟡 parcial · ❌ não iniciado

## Arquitetura

| Item da spec | Hoje no código | Status |
|---|---|---|
| Frontend React + **TypeScript** | React (Vite) em **JSX**, Recharts para gráficos | 🟡 falta migrar para TS |
| Backend Python + **NumPy** | FastAPI + SQLAlchemy; nenhum uso de NumPy | 🟡 |
| Banco principal **MySQL** | **PostgreSQL** (`psycopg2`, porta 5433) | 🟡 decidir: migrar ou justificar Postgres |
| Histórico no **MongoDB** (logs diários, sintomas, peso) | Mongo usado só para **exames**; peso/sintomas diários estão no Postgres (`pet_records`) | 🟡 |

## Requisitos funcionais

| RF | Descrição resumida | Onde está hoje | Status |
|---|---|---|---|
| RF-01 | Cadastro/edição de pacientes e tutores (relacional) | `models.User/Pet`, `routers/pets.py` (POST/PATCH), `routers/auth.py` (register) | ✅ (falta PATCH de tutor) |
| RF-02 | Peso diário persistido no Mongo | Peso vai para `pet_records` e `chemo_sessions` no Postgres | 🟡 mover para coleção Mongo `daily_logs` |
| RF-03 | Múltiplos sintomas (vômito, letargia) + **escala de dor** no Mongo | `PetRecord.symptoms` é texto livre; sem escala de dor | ❌ |
| RF-04 | Protocolos de quimio com sessões **planejadas × executadas** | `ChemoProtocol` + `chemo_sessions.protocol_id`; rotas `/api/protocols`; progresso em `services/protocols.py`; telas do vet e do tutor | ✅ |
| RF-05 | Estatísticas via NumPy consumidas pelos gráficos | `GET /api/pets/{id}/chart` monta série de peso em Python puro | 🟡 |
| RF-06 | Dashboard de Cuidados Paliativos (Mongo × sessões) | — | ❌ |
| RF-07 | Exportar relatório clínico em PDF | — | ❌ |

## Requisitos não funcionais

| RNF | Status | Observação |
|---|---|---|
| RNF-01 Agregação vetorizada com NumPy | ❌ | depende de RF-02/03 no Mongo |
| RNF-02 Gráficos fluidos + tema escuro | 🟡 | Recharts ok; verificar/ajustar tema escuro em `index.css` |
| RNF-03 IDs do relacional mapeando para documentos do Mongo | 🟡 | `exams.pet_id` referencia `pets.id`, mas sem validação de existência ao inserir |
| RNF-04 TS estrito no front; rotas REST separadas da camada analítica | ❌ | criar `backend/app/analytics/` e migrar front para TS |

## Outros pontos encontrados

- README descreve SQLite e uma estrutura de pastas antiga (v1); código real é v3.1 com Postgres + Mongo.
- Credenciais e `SECRET_KEY` estavam fixos no código — agora vêm de variáveis de ambiente (`.env.example`).
- `docker-compose.yml` expunha o Mongo em 27017, mas o código conecta em 27018 — alinhado.
- Testes automatizados começaram com o RF-04 (`backend/tests`). Ainda não há migrações (`Base.metadata.create_all` no startup).

## Roteiro sugerido

1. **Decidir o banco relacional** (MySQL conforme spec, ou manter Postgres e registrar a justificativa).
2. ~~**Modelo de protocolo (RF-04)**~~ — feito em `feature/protocolos-quimio`.
3. **Diário no Mongo (RF-02/03):** coleção `daily_logs` `{pet_id, date, weight, symptoms: [..], pain_score 0–10, appetite, energy}` com índice `(pet_id, date)`; migrar `pet_records`.
4. **Camada analítica (RF-05, RNF-01/04):** `backend/app/analytics/` com NumPy (tendência de peso, % de variação, médias móveis de dor/sintomas) + rota `/api/analytics/...`.
5. **Dashboard paliativo (RF-06)** consumindo a camada analítica.
6. **Relatório PDF (RF-07)** — ex.: ReportLab ou WeasyPrint no backend.
7. **Migração do frontend para TypeScript (RNF-04)** — pode ser incremental (`allowJs`), começando por `api.ts` e tipos das respostas.
8. Testes (pytest) e migrações (Alembic).
