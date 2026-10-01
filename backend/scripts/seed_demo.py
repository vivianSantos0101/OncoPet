"""Popula o OncoPet com dados de demonstracao (ficticios).

Usa a propria API, entao respeita as mesmas validacoes e calculos de dose
do sistema. As datas sao geradas a partir do dia em que o script roda.

Uso (com o backend rodando):
    cd backend
    source .venv/bin/activate
    python scripts/seed_demo.py                 # API em http://localhost:8000
    python scripts/seed_demo.py --api http://localhost:8000

Para recomecar do zero:
    docker compose down -v && docker compose up -d   (na raiz do projeto)
    reinicie o backend e rode o script de novo

Todos os usuarios usam a senha: oncopet123
"""

import argparse
import random
import sys
from datetime import date, timedelta

PASSWORD = "oncopet123"

VETS = {
    "dra_ana": {"full_name": "Dra. Ana Souza", "crmv": "SP-40211", "email": "ana.souza@exemplo.com"},
    "dr_marcos": {"full_name": "Dr. Marcos Ribeiro", "crmv": "SP-38877", "email": "marcos.ribeiro@exemplo.com"},
}

TUTORS = {
    "joao": {"full_name": "João Lima", "phone": "(11) 90000-0001", "email": "joao@exemplo.com"},
    "mariana": {"full_name": "Mariana Costa", "phone": "(11) 90000-0002", "email": "mariana@exemplo.com"},
    "carla": {"full_name": "Carla Mendes", "phone": "(11) 90000-0003", "email": "carla@exemplo.com"},
    "pedro": {"full_name": "Pedro Alves", "phone": "(11) 90000-0004", "email": "pedro@exemplo.com"},
    "rafael": {"full_name": "Rafael Souza", "phone": "(11) 90000-0005", "email": "rafael@exemplo.com"},
}

CLINICS = [
    {"name": "Clínica Veterinária Vida", "address": "Rua das Acácias, 120 - São Paulo", "phone": "(11) 3000-1000"},
    {"name": "Hospital Veterinário Patinhas", "address": "Av. dos Ipês, 890 - São Paulo", "phone": "(11) 3000-2000"},
]

# start: dias atras em que o protocolo comecou | executed: sessoes ja feitas
# drugs: quando o protocolo alterna medicamentos, lista (nome, dose mg/m2) por sessao
PATIENTS = [
    {
        "name": "Thor", "pain": (1, 0), "species": "cao", "breed": "Labrador Retriever", "age": (8, 3),
        "cancer": "Linfoma multicêntrico", "tutor": "joao", "vet": "dra_ana", "clinic": 0,
        "weight": 31.2, "trend": -0.12,
        "protocols": [{
            "name": "CHOP (19 semanas)", "drug": "Vincristina / Ciclofosfamida / Doxorrubicina",
            "dose": None, "planned": 16, "interval": 7, "start": 70, "executed": 10,
            "drugs": [("Vincristina", 0.7), ("Ciclofosfamida", 250), ("Vincristina", 0.7), ("Doxorrubicina", 30)],
        }],
        "reminders": [
            ("Prednisona 1 mg/kg pela manhã", "medicacao", 0, "08:00", "diaria"),
            ("Hemograma de controle", "exame", 2, "10:00", None),
        ],
        "documents": [("Hemograma completo", "exame_sangue", -14), ("Laudo citológico - linfonodo", "laudo", -72)],
    },
    {
        "name": "Luna", "pain": (3, 0.25), "species": "cao", "breed": "Golden Retriever", "age": (10, 1),
        "cancer": "Osteossarcoma apendicular", "tutor": "mariana", "vet": "dra_ana", "clinic": 0,
        "weight": 29.5, "trend": -0.08,
        "protocols": [{
            "name": "Carboplatina adjuvante", "drug": "Carboplatina", "dose": 300,
            "planned": 6, "interval": 21, "start": 100, "executed": 4,
        }],
        "reminders": [
            ("Remarcar sessão de carboplatina", "sessao", 1, "09:30", None),
            ("Meloxicam 0,1 mg/kg", "medicacao", 0, "20:00", "diaria"),
        ],
        "documents": [("Raio-X de tórax (sem metástases)", "exame_imagem", -30)],
    },
    {
        "name": "Mia", "pain": (2, 0), "species": "gato", "breed": "Siamês", "age": (11, 6),
        "cancer": "Carcinoma de células escamosas", "tutor": "joao", "vet": "dra_ana", "clinic": 0,
        "weight": 4.3, "trend": -0.02,
        "protocols": [{
            "name": "Carboplatina felina", "drug": "Carboplatina", "dose": 200,
            "planned": 4, "interval": 21, "start": 30, "executed": 2,
        }],
        "reminders": [("Consulta de reavaliação da lesão", "consulta", 5, "14:00", None)],
        "documents": [],
    },
    {
        "name": "Bob", "pain": (1, 0), "species": "cao", "breed": "SRD (Sem Raça Definida)", "age": (12, 0),
        "cancer": "Mastocitoma grau II", "tutor": "carla", "vet": "dra_ana", "clinic": 1,
        "weight": 18.4, "trend": 0.03,
        "protocols": [
            {"name": "Vimblastina + Prednisona", "drug": "Vimblastina", "dose": 2,
             "planned": 8, "interval": 7, "start": 63, "executed": 8},
            {"name": "Lomustina resgate", "drug": "Lomustina", "dose": 70,
             "planned": 4, "interval": 21, "start": 5, "executed": 1},
        ],
        "reminders": [("Omeprazol 1 mg/kg em jejum", "medicacao", 0, "07:30", "diaria")],
        "documents": [("Bioquímico - função hepática", "exame_sangue", -6)],
    },
    {
        "name": "Nina", "pain": (2, 0.1), "species": "cao", "breed": "Poodle", "age": (9, 8),
        "cancer": "Carcinoma mamário", "tutor": "carla", "vet": "dr_marcos", "clinic": 1,
        "weight": 7.8, "trend": -0.06,
        "protocols": [{
            "name": "Doxorrubicina pós-mastectomia", "drug": "Doxorrubicina", "dose": 30,
            "planned": 5, "interval": 21, "start": 60, "executed": 3, "suspend": True,
            "notes": "Suspenso por neutropenia grau 3. Reavaliar hemograma.",
        }],
        "reminders": [("Hemograma para decidir retomada", "exame", 3, "09:00", None)],
        "documents": [("Hemograma - neutropenia", "exame_sangue", -2)],
    },
    {
        "name": "Frida", "pain": (1, 0), "species": "gato", "breed": "Persa", "age": (7, 2),
        "cancer": "Linfoma alimentar", "tutor": "pedro", "vet": "dra_ana", "clinic": 0,
        "weight": 3.9, "trend": 0.01,
        "protocols": [{
            "name": "Protocolo COP", "drug": "Ciclofosfamida", "dose": 200,
            "planned": 12, "interval": 7, "start": 35, "executed": 5,
        }],
        "reminders": [("Sessão COP", "sessao", 0, "11:00", None)],
        "documents": [],
    },
    {
        "name": "Max", "pain": (2, 0.05), "species": "cao", "breed": "Boxer", "age": (7, 5),
        "cancer": "Hemangiossarcoma esplênico", "tutor": "rafael", "vet": "dr_marcos", "clinic": 1,
        "weight": 30.1, "trend": -0.15,
        "protocols": [{
            "name": "Doxorrubicina pós-esplenectomia", "drug": "Doxorrubicina", "dose": 30,
            "planned": 5, "interval": 14, "start": 42, "executed": 3,
        }],
        "reminders": [("Ecocardiograma antes da 4ª sessão", "exame", 4, "15:00", None)],
        "documents": [("Ultrassom abdominal", "exame_imagem", -45)],
    },
    {
        "name": "Pipoca", "pain": (0, 0), "species": "cao", "breed": "Shih Tzu", "age": (6, 0),
        "cancer": "Tumor venéreo transmissível (TVT)", "tutor": "mariana", "vet": "dra_ana", "clinic": 0,
        "weight": 6.2, "trend": 0.02,
        "protocols": [{
            "name": "Vincristina semanal", "drug": "Vincristina", "dose": 0.75,
            "planned": 6, "interval": 7, "start": 28, "executed": 4,
        }],
        "reminders": [("Sessão de vincristina", "sessao", 0, "10:00", None)],
        "documents": [],
    },
    # Caso paliativo: dor alta, perda de peso, febre apos a ultima sessao e
    # tutor sem registrar ha quase 2 semanas (aparece como critico no RF-06)
    {
        "name": "Bela", "pain": (5, 0.3), "species": "cao", "breed": "Rottweiler", "age": (9, 4),
        "cancer": "Carcinoma de células de transição (bexiga)", "tutor": "pedro", "vet": "dra_ana", "clinic": 0,
        "weight": 38.0, "trend": -0.35, "diary_stop": 12,
        "side_effects": [(["febre", "letargia"], "Febre à noite, tremores", "ruim", "reduzido", "letargico", 2)],
        "protocols": [{
            "name": "Mitoxantrona + Piroxicam (paliativo)", "drug": "Mitoxantrona", "dose": 5,
            "planned": 5, "interval": 21, "start": 49, "executed": 3,
        }],
        "reminders": [("Piroxicam 0,3 mg/kg com alimento", "medicacao", 0, "19:00", "diaria")],
        "documents": [("Ultrassom de bexiga", "exame_imagem", -50)],
    },
]

# Dias apos a sessao: (sintomas marcados, outros sintomas, estado, apetite, energia, dor extra)
SIDE_EFFECTS = [
    (["vomito"], None, "regular", "reduzido", "baixo", 1),
    (["letargia", "inapetencia"], None, "regular", "reduzido", "letargico", 1),
    (["diarreia"], None, "regular", "normal", "normal", 0),
    (["inapetencia"], "Recusou a ração pela manhã", "regular", "reduzido", "normal", 0),
]
GOOD_DAYS = [
    ([], "bom", "normal", "normal", "Brincou normalmente."),
    ([], "otimo", "normal", "alto", "Muito disposto, passeio completo."),
    ([], "bom", "normal", "normal", None),
]


class SeedError(Exception):
    pass


def ok(res, what):
    if res.status_code >= 400:
        raise SeedError(f"{what}: HTTP {res.status_code} - {res.text[:200]}")
    return res.json()


def mini_pdf(title: str, lines: list) -> bytes:
    """Gera um PDF de uma pagina com texto simples (sem dependencias)."""
    def esc(t):
        t = t.encode("latin-1", "replace").decode("latin-1")
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    text = ["BT", "/F1 18 Tf", "56 780 Td", f"({esc(title)}) Tj", "/F1 11 Tf"]
    for line in lines:
        text += ["0 -22 Td", f"({esc(line)}) Tj"]
    text.append("ET")
    stream = "\n".join(text).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def seed(client, today: date = None, rng: random.Random = None) -> dict:
    """Cria todos os dados usando um cliente HTTP (httpx.Client ou TestClient)."""
    today = today or date.today()
    rng = rng or random.Random(42)
    auth = {}

    def register(username, role, info):
        res = client.post("/api/auth/register", json={
            "username": username, "password": PASSWORD, "role": role, **info,
        })
        if res.status_code == 400 and "existe" in res.text.lower():
            raise SeedError(
                f"O usuario '{username}' ja existe: o banco ja foi populado.\n"
                "Para recomecar do zero: docker compose down -v && docker compose up -d, "
                "reinicie o backend e rode o script de novo."
            )
        body = ok(res, f"cadastro de {username}")
        auth[username] = {"Authorization": f"Bearer {body['access_token']}"}
        return body["user"]

    users = {}
    for username, info in VETS.items():
        users[username] = register(username, "vet", info)
    for username, info in TUTORS.items():
        users[username] = register(username, "tutor", info)

    clinic_ids = [ok(client.post("/api/clinics/", headers=auth["dra_ana"], json=c), "clinica")["id"] for c in CLINICS]

    totals = {"pets": 0, "protocols": 0, "sessions": 0, "records": 0, "reminders": 0, "documents": 0}

    for pt in PATIENTS:
        vet_h, tutor_h = auth[pt["vet"]], auth[pt["tutor"]]
        first_day = today - timedelta(days=max(p["start"] for p in pt["protocols"]))
        weight_on = lambda d: round(pt["weight"] + pt["trend"] * ((d - first_day).days / 7) + rng.uniform(-0.15, 0.15) * (pt["weight"] / 20), 1)

        pet = ok(client.post("/api/pets/", headers=vet_h, json={
            "name": pt["name"], "species": pt["species"], "breed": pt["breed"],
            "weight": pt["weight"], "age_years": pt["age"][0], "age_months": pt["age"][1],
            "cancer_type": pt["cancer"], "treatment_start_date": first_day.isoformat(),
            "tutor_id": users[pt["tutor"]]["id"], "vet_id": users[pt["vet"]]["id"],
            "clinic_id": clinic_ids[pt["clinic"]],
        }), f"pet {pt['name']}")
        totals["pets"] += 1

        # Eventos em ordem cronologica: o peso atual do pet fica o do ultimo registro
        events = []
        session_days = set()
        for proto in pt["protocols"]:
            start = today - timedelta(days=proto["start"])
            created = ok(client.post("/api/protocols/", headers=vet_h, json={
                "pet_id": pet["id"], "name": proto["name"], "drug_name": proto["drug"],
                "dose_mg_m2": proto["dose"], "planned_sessions": proto["planned"],
                "interval_days": proto["interval"], "start_date": start.isoformat(),
                "notes": proto.get("notes"),
            }), f"protocolo {proto['name']}")
            proto["id"] = created["id"]
            totals["protocols"] += 1
            for i in range(proto["executed"]):
                day = start + timedelta(days=i * proto["interval"])
                session_days.add(day)
                drug, dose = proto["drugs"][i % len(proto["drugs"])] if proto.get("drugs") else (None, None)
                events.append((day, "session", {
                    "pet_id": pet["id"], "protocol_id": proto["id"], "date": day.isoformat(),
                    "session_type": "quimioterapia", "drug_name": drug, "dose_mg_m2": dose,
                    "notes": rng.choice(["Sem intercorrências.", "Boa tolerância.", "Pré-medicação com ondansetrona.", None]),
                }))

        day = first_day + timedelta(days=3)
        while day <= today - timedelta(days=pt.get("diary_stop", 1)):
            after_session = any(0 < (day - s).days <= 3 for s in session_days)
            base_pain, pain_trend = pt["pain"]
            pain = base_pain + pain_trend * ((day - first_day).days / 7) + rng.choice([-1, 0, 0, 1])
            other, notes = None, None
            if after_session and rng.random() < 0.6:
                symptoms, other, status, appetite, energy, extra_pain = rng.choice(pt.get("side_effects", SIDE_EFFECTS))
                pain += extra_pain
            else:
                symptoms, status, appetite, energy, notes = rng.choice(GOOD_DAYS)
            events.append((day, "record", {
                "pet_id": pet["id"], "date": day.isoformat(), "symptoms": symptoms,
                "other_symptoms": other, "pain_score": max(0, min(10, round(pain))),
                "general_status": status, "appetite": appetite, "energy_level": energy, "notes": notes,
            }))
            day += timedelta(days=7)

        for day, kind, payload in sorted(events, key=lambda e: (e[0], e[1])):
            if kind == "session":
                payload["weight_at_session"] = weight_on(day)
                ok(client.post("/api/sessions/", headers=vet_h, json=payload), f"sessao de {pt['name']}")
                totals["sessions"] += 1
            else:
                payload["weight"] = weight_on(day)
                ok(client.post("/api/records/", headers=tutor_h, json=payload), f"registro de {pt['name']}")
                totals["records"] += 1

        for proto in pt["protocols"]:
            if proto.get("suspend"):
                ok(client.patch(f"/api/protocols/{proto['id']}", headers=vet_h, json={"status": "suspenso"}), "suspender protocolo")

        for title, kind, offset, time, recurrence in pt["reminders"]:
            ok(client.post("/api/reminders/", headers=vet_h, json={
                "pet_id": pet["id"], "title": title, "reminder_type": kind,
                "date": (today + timedelta(days=offset)).isoformat(), "time": time,
                "recurrence": recurrence,
            }), f"lembrete de {pt['name']}")
            totals["reminders"] += 1

        for title, doc_type, offset in pt["documents"]:
            doc_day = today + timedelta(days=offset)
            pdf = mini_pdf(f"{title} - {pt['name']}", [
                f"Paciente: {pt['name']} ({pt['breed']})",
                f"Data: {doc_day.strftime('%d/%m/%Y')}",
                "Documento de demonstracao gerado pelo seed do OncoPet.",
                "Dados ficticios.",
            ])
            upload = ok(client.post("/api/uploads/", headers=vet_h, files={
                "file": (f"{title}.pdf", pdf, "application/pdf"),
            }), "upload de documento")
            ok(client.post("/api/documents/", headers=vet_h, json={
                "pet_id": pet["id"], "title": title, "doc_type": doc_type,
                "file_url": upload["url"], "date": doc_day.isoformat(),
            }), f"documento de {pt['name']}")
            totals["documents"] += 1

    return totals


def main():
    parser = argparse.ArgumentParser(description="Popula o OncoPet com dados de demonstracao.")
    parser.add_argument("--api", default="http://localhost:8000", help="URL do backend")
    args = parser.parse_args()

    import httpx
    with httpx.Client(base_url=args.api, timeout=30) as client:
        try:
            client.get("/")
        except httpx.HTTPError:
            sys.exit(f"Nao consegui acessar {args.api}. Suba o backend antes (uvicorn app.main:app --reload).")
        try:
            totals = seed(client)
        except SeedError as err:
            sys.exit(str(err))

    print("Banco populado com dados de demonstracao:")
    for key, label in [("pets", "pacientes"), ("protocols", "protocolos"), ("sessions", "sessoes"),
                       ("records", "registros do tutor"), ("reminders", "lembretes"), ("documents", "documentos")]:
        print(f"  {totals[key]:>4}  {label}")
    print(f"\nLogins (senha para todos: {PASSWORD}):")
    print("  Veterinarios: dra_ana, dr_marcos")
    print("  Tutores:      joao, mariana, carla, pedro, rafael")


if __name__ == "__main__":
    main()
