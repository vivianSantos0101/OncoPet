"""RF-07: relatorio clinico unificado em PDF."""

from datetime import date, datetime
from io import BytesIO

from pypdf import PdfReader

from app.reports.pdf import br, clean, render_report, symptoms_text
from app.routers.reports import report_filename
from scripts.seed_demo import seed


def pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages)


# ─── Funcoes de texto ────────────────────────────────

def test_formatacao_brasileira():
    assert br(1.0) == "1" and br(6.25, 2) == "6,25" and br(None) == "—"
    assert symptoms_text(["vomito", "dispneia"], "tremores") == "vômito, falta de ar; outros: tremores"
    assert symptoms_text([]) == "—"


def test_texto_seguro_para_o_pdf():
    assert clean("<b>Rex & Cia</b>") == "&lt;b&gt;Rex &amp; Cia&lt;/b&gt;"  # nao vira marcacao
    assert clean("−0,5 ≥ 7") == "-0,5 &gt;= 7"                               # simbolos sem glifo
    assert clean("m²") == "m<super>2</super>"
    assert clean(None) == ""


def test_nome_do_arquivo():
    assert report_filename("Luna", date(2026, 9, 30)) == "relatorio-luna-2026-09-30.pdf"
    assert report_filename("Pé de Moleque!", date(2026, 1, 2)) == "relatorio-pe-de-moleque-2026-01-02.pdf"


def test_relatorio_minimo_sem_historico():
    """Pet recem-cadastrado: o PDF sai sem quebrar e explica o que falta."""
    data = {
        "generated_at": datetime(2026, 9, 30, 10, 0), "reference_date": date(2026, 9, 30),
        "pet": {"name": "Rex", "species": "cao", "breed": "SRD", "age_years": None, "age_months": None,
                "weight": 10.0, "body_surface_area": 0.55, "cancer_type": None, "treatment_start_date": None},
        "tutor": None, "vet": None, "clinic": None,
        "level": "atencao", "alerts": [{"level": "atencao", "code": "sem_diario",
                                        "message": "O tutor ainda não fez nenhum registro no diário"}],
        "effect": None, "protocols": [], "sessions": [], "weight": None, "weight_points": [],
        "pain": None, "pain_points": [], "symptoms": [], "logs_count": 0, "diary": [], "documents": [],
    }
    pdf = render_report(data)
    assert pdf.startswith(b"%PDF")
    text = pdf_text(pdf)
    assert "Rex" in text and "Diagnóstico não informado" in text
    assert "O tutor ainda não fez registros no diário." in text


# ─── Rota /api/reports ───────────────────────────────

def test_rota_gera_pdf_com_dados_dos_dois_bancos(client, setup):
    pet_id = setup["pet"]["id"]
    client.post("/api/sessions/", headers=setup["vet"], json={
        "pet_id": pet_id, "date": "2026-09-01", "weight_at_session": 20.0,
        "drug_name": "Vincristina", "dose_mg_m2": 0.7})
    client.post("/api/records/", headers=setup["tutor"], json={
        "pet_id": pet_id, "date": "2026-09-02", "weight": 19.6, "pain_score": 8,
        "symptoms": ["vomito"], "notes": "Vomitou duas vezes"})

    res = client.get(f"/api/reports/pet/{pet_id}?reference_date=2026-09-05", headers=setup["vet"])
    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "application/pdf"
    assert res.headers["content-disposition"] == 'attachment; filename="relatorio-thor-2026-09-05.pdf"'

    text = pdf_text(res.content)
    assert "Thor" in text and "Joao" in text                   # relacional: pet e tutor
    assert "Vincristina" in text and "Ruim" in text            # sessao + tolerancia (RF-06)
    assert "Vomitou duas vezes" in text and "8/10" in text     # MongoDB: diario do tutor
    assert "CRÍTICO" in text                                   # alerta de dor intensa
    assert "dados até 05/09/2026" in text


def test_permissoes(client, setup):
    pet_id = setup["pet"]["id"]
    assert client.get(f"/api/reports/pet/{pet_id}", headers=setup["tutor"]).status_code == 200
    assert client.get(f"/api/reports/pet/{pet_id}", headers=setup["other_tutor"]).status_code == 403
    assert client.get("/api/reports/pet/999", headers=setup["vet"]).status_code == 404
    assert client.get(f"/api/reports/pet/{pet_id}").status_code == 401


def test_relatorio_dos_dados_de_demonstracao(client):
    seed(client, today=date(2026, 9, 28))
    token = client.post("/api/auth/login", data={"username": "dra_ana", "password": "oncopet123"}).json()["access_token"]
    res = client.get("/api/reports/pet/2?reference_date=2026-09-28", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    reader = PdfReader(BytesIO(res.content))
    assert len(reader.pages) >= 2
    assert reader.metadata.title == "Relatório clínico - Luna"
    text = pdf_text(res.content)
    for expected in ("Osteossarcoma apendicular", "Carboplatina adjuvante", "(atrasada)",
                     "Mariana Costa", "CRMV SP-40211", "Raio-X de tórax", "Página 1 de"):
        assert expected in text, expected
