"""Desenho do relatorio clinico em PDF (RF-07) com ReportLab.

Recebe o dicionario montado por services/clinical_report.py (so textos e
numeros) e devolve os bytes do PDF. Nao acessa banco.
"""

from datetime import date, datetime
from io import BytesIO
from typing import Iterable, List, Optional, Sequence
from xml.sax.saxutils import escape

from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# Cores do app (tema Vitalidade) e dos graficos (paleta validada no RF-05)
INK = colors.HexColor("#102a33")
TEXT = colors.HexColor("#22343c")
MUTED = colors.HexColor("#5f7179")
BORDER = colors.HexColor("#dfe8eb")
SOFT = colors.HexColor("#f3faf7")
MINT = colors.HexColor("#12b886")
MINT_STRONG = colors.HexColor("#087f5b")
COLOR_VALUE = colors.HexColor("#0ca678")
COLOR_AVERAGE = colors.HexColor("#3b5bdb")
SEVERE_LINE = colors.HexColor("#e8590c")
LEVEL_COLORS = {
    "critico": (colors.HexColor("#c92a2a"), colors.HexColor("#fff0f0")),
    "atencao": (colors.HexColor("#c2410c"), colors.HexColor("#fff4e6")),
    "estavel": (colors.HexColor("#087f5b"), colors.HexColor("#e3f8f0")),
}
LEVEL_LABELS = {"critico": "Crítico", "atencao": "Atenção", "estavel": "Estável"}
TOLERANCE_LABELS = {"boa": "Boa", "moderada": "Moderada", "ruim": "Ruim", "sem_dados": "Sem registro"}
STATUS_LABELS = {"ativo": "Ativo", "concluido": "Concluído", "suspenso": "Suspenso"}
SYMPTOM_LABELS = {
    "vomito": "vômito", "diarreia": "diarreia", "letargia": "letargia", "inapetencia": "falta de apetite",
    "febre": "febre", "tosse": "tosse", "dispneia": "falta de ar", "lesao_pele": "lesão de pele",
}
DOC_TYPES = {"exame_sangue": "Exame de sangue", "exame_imagem": "Exame de imagem", "laudo": "Laudo", "outro": "Outro"}
WORDS = {"otimo": "ótimo", "letargico": "letárgico"}
ENERGY = {"alto": "alta", "baixo": "baixa", "letargico": "letárgica"}  # "energia" e feminino

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# As fontes padrao do PDF (Helvetica) so tem os caracteres do Windows-1252:
# troca os poucos simbolos que usamos e que ficariam como quadrado.
_REPLACE = {"−": "-", "≥": ">=", "≤": "<=", "→": "->"}


def clean(text) -> str:
    """Texto seguro para o PDF: escapa XML e troca caracteres sem glifo."""
    if text is None:
        return ""
    text = str(text)
    for old, new in _REPLACE.items():
        text = text.replace(old, new)
    text = text.encode("cp1252", errors="replace").decode("cp1252")
    # "²" nao tem glifo na Helvetica padrao: vira expoente de verdade
    return escape(text).replace("²", "<super>2</super>")


def br(value, digits: int = 1) -> str:
    """1.0 -> '1' | 6.25 -> '6,3' (formato brasileiro, sem casas desnecessarias)."""
    if value is None:
        return "—"
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def signed(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return ("+" if value > 0 else "") + br(value, digits)


def fdate(value: Optional[date]) -> str:
    return value.strftime("%d/%m/%Y") if value else "—"


def word(value: Optional[str]) -> str:
    if not value:
        return "—"
    value = WORDS.get(value, value)
    return value[:1].upper() + value[1:]


def species_label(species: str) -> str:
    return {"cao": "Cão", "gato": "Gato"}.get(species, word(species))


def age_label(years: Optional[int], months: Optional[int]) -> str:
    parts = []
    if years:
        parts.append(f"{years} ano{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} {'mês' if months == 1 else 'meses'}")
    return " e ".join(parts) or "—"


def symptoms_text(keys: Iterable[str], other: Optional[str] = None) -> str:
    text = ", ".join(SYMPTOM_LABELS.get(k, k) for k in keys)
    if other:
        text = f"{text}; outros: {other}" if text else other
    return text or "—"


# ─── Estilos ────────────────────────────────────────

def _styles() -> dict:
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=TEXT)
    return {
        "body": ParagraphStyle("body", **base),
        "small": ParagraphStyle("small", **{**base, "fontSize": 8, "leading": 10.5, "textColor": MUTED}),
        "cell": ParagraphStyle("cell", **{**base, "fontSize": 8.3, "leading": 10.5}),
        "cell_head": ParagraphStyle("cell_head", **{**base, "fontName": "Helvetica-Bold", "fontSize": 7.6,
                                                     "leading": 10, "textColor": MUTED}),
        "label": ParagraphStyle("label", **{**base, "fontName": "Helvetica-Bold", "fontSize": 7.6,
                                            "leading": 10, "textColor": MUTED}),
        "value": ParagraphStyle("value", **{**base, "fontName": "Helvetica-Bold", "fontSize": 9.5,
                                            "leading": 12.5, "textColor": INK}),
        "title": ParagraphStyle("title", **{**base, "fontName": "Helvetica-Bold", "fontSize": 22,
                                            "leading": 26, "textColor": INK}),
        "subtitle": ParagraphStyle("subtitle", **{**base, "fontSize": 10.5, "leading": 14, "textColor": MUTED}),
        "h2": ParagraphStyle("h2", **{**base, "fontName": "Helvetica-Bold", "fontSize": 12, "leading": 15,
                                      "textColor": INK, "spaceBefore": 14, "spaceAfter": 6}),
        "big": ParagraphStyle("big", **{**base, "fontName": "Helvetica-Bold", "fontSize": 15, "leading": 18,
                                        "textColor": INK}),
        "right": ParagraphStyle("right", **{**base, "fontSize": 8, "leading": 10.5, "textColor": MUTED,
                                            "alignment": TA_RIGHT}),
    }


def _section(title: str, st: dict) -> List:
    rule = Table([[""]], colWidths=[CONTENT_W], rowHeights=[1.2])
    rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 1.2, MINT)]))
    return [Paragraph(clean(title), st["h2"]), rule, Spacer(1, 6)]


def _table(head: Sequence[str], rows: List[Sequence], widths: Sequence[float], st: dict,
           row_styles: Optional[List] = None) -> Table:
    data = [[Paragraph(clean(h), st["cell_head"]) for h in head]]
    for row in rows:
        data.append([c if not isinstance(c, str) else Paragraph(c, st["cell"]) for c in row])
    table = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    table.setStyle(TableStyle(style + (row_styles or [])))
    return table


def _tag(level: Optional[str], text: str) -> str:
    """Etiqueta colorida com o texto (o nivel nunca e so cor: impressao P&B)."""
    if not level:
        return f'<font color="#5f7179">{clean(text)}</font>'
    fg = LEVEL_COLORS[level][0].hexval().replace("0x", "#")
    return f'<font color="{fg}"><b>{clean(text)}</b></font>'


# ─── Graficos ───────────────────────────────────────

def line_chart(points: Sequence[tuple], title: str, y_label: str, width: float, height: float,
               y_range: Optional[tuple] = None, severe_line: Optional[float] = None) -> Drawing:
    """Grafico de linha (valor + media movel). points = [(data, valor, media), ...]."""
    d = Drawing(width, height)
    d.add(String(0, height - 10, title, fontName="Helvetica-Bold", fontSize=8.5, fillColor=INK))
    if len(points) < 2:
        d.add(String(0, height / 2, "Poucos registros para o gráfico", fontName="Helvetica", fontSize=8, fillColor=MUTED))
        return d

    start = points[0][0].toordinal()
    values = [(p[0].toordinal() - start, p[1]) for p in points]
    averages = [(p[0].toordinal() - start, p[2]) for p in points]

    plot = LinePlot()
    plot.x, plot.y = 26, 26
    plot.width, plot.height = width - 34, height - 50
    plot.data = [values, averages]
    plot.joinedLines = 1
    plot.lines[0].strokeColor = COLOR_VALUE
    plot.lines[0].strokeWidth = 1.6
    plot.lines[1].strokeColor = COLOR_AVERAGE
    plot.lines[1].strokeWidth = 1.4
    if len(points) <= 16:
        plot.lines[0].symbol = makeMarker("FilledCircle", size=3.2, fillColor=COLOR_VALUE, strokeColor=colors.white)

    last_day = values[-1][0]
    plot.xValueAxis.valueMin = 0
    plot.xValueAxis.valueMax = max(last_day, 1)
    steps = 4
    plot.xValueAxis.valueSteps = [round(last_day * i / steps) for i in range(steps + 1)]
    plot.xValueAxis.labelTextFormat = lambda v: date.fromordinal(int(v) + start).strftime("%d/%m")
    plot.xValueAxis.labels.fontName = "Helvetica"
    plot.xValueAxis.labels.fontSize = 6.5
    plot.xValueAxis.labels.fillColor = MUTED
    plot.xValueAxis.strokeColor = BORDER
    plot.xValueAxis.tickDown = 0

    ys = [v for _, v in values] + [v for _, v in averages]
    if y_range:
        plot.yValueAxis.valueMin, plot.yValueAxis.valueMax = y_range
        plot.yValueAxis.valueStep = 2
    else:
        pad = max((max(ys) - min(ys)) * 0.15, 0.3)
        plot.yValueAxis.valueMin = round(min(ys) - pad, 1)
        plot.yValueAxis.valueMax = round(max(ys) + pad, 1)
    plot.yValueAxis.labels.fontName = "Helvetica"
    plot.yValueAxis.labels.fontSize = 6.5
    plot.yValueAxis.labels.fillColor = MUTED
    plot.yValueAxis.labelTextFormat = lambda v: br(v, 1)
    plot.yValueAxis.strokeColor = BORDER
    plot.yValueAxis.visibleGrid = 1
    plot.yValueAxis.gridStrokeColor = colors.HexColor("#eef3f4")
    plot.yValueAxis.gridStrokeWidth = 0.5
    plot.yValueAxis.tickLeft = 0
    d.add(plot)

    if severe_line is not None and y_range:
        y = plot.y + (severe_line - y_range[0]) / (y_range[1] - y_range[0]) * plot.height
        d.add(Line(plot.x, y, plot.x + plot.width, y, strokeColor=SEVERE_LINE, strokeWidth=0.8, strokeDashArray=[3, 2]))

    # Legenda (texto na cor do texto; a cor fica so no traco)
    lx = 0
    for color, label in ((COLOR_VALUE, y_label), (COLOR_AVERAGE, "Média móvel (3 registros)")):
        d.add(Line(lx, 4, lx + 12, 4, strokeColor=color, strokeWidth=2))
        d.add(String(lx + 15, 1.5, label, fontName="Helvetica", fontSize=7, fillColor=MUTED))
        lx += 20 + len(label) * 3.6
    if severe_line is not None:
        d.add(Line(lx, 4, lx + 12, 4, strokeColor=SEVERE_LINE, strokeWidth=1, strokeDashArray=[3, 2]))
        d.add(String(lx + 15, 1.5, "Dor intensa (7+)", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return d


# ─── Pagina (cabecalho/rodape com "pagina X de Y") ──

class _NumberedCanvas(canvas.Canvas):
    """Guarda as paginas para escrever o total ("Pagina 2 de 3") no final."""

    def __init__(self, *args, footer_text: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []
        self._footer_text = footer_text

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total: int):
        self.setFillColor(MINT)
        self.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)
        self.setFont("Helvetica-Bold", 9)
        self.setFillColor(MINT_STRONG)
        self.drawString(MARGIN, PAGE_H - 22, "OncoPet")
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED)
        self.drawRightString(PAGE_W - MARGIN, PAGE_H - 22, "Relatório clínico")
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
        self.setFont("Helvetica", 7)
        self.drawString(MARGIN, 9.5 * mm, self._footer_text)
        self.drawRightString(PAGE_W - MARGIN, 9.5 * mm, f"Página {self._pageNumber} de {total}")


# ─── Relatorio ──────────────────────────────────────

def render_report(data: dict) -> bytes:
    st = _styles()
    pet = data["pet"]
    story: List = []

    # Titulo
    generated: datetime = data["generated_at"]
    story += [
        Paragraph(clean(pet["name"]), st["title"]),
        Paragraph(clean(pet.get("cancer_type") or "Diagnóstico não informado"), st["subtitle"]),
        Spacer(1, 3),
        Paragraph(
            f"Emitido em {generated.strftime('%d/%m/%Y às %H:%M')} · "
            f"dados até {fdate(data['reference_date'])}", st["small"]),
        Spacer(1, 10),
    ]

    # 1. Identificacao
    story += _section("1. Identificação", st)
    tutor, vet, clinic = data["tutor"] or {}, data["vet"] or {}, data["clinic"] or {}
    start = pet.get("treatment_start_date")
    treatment_days = (data["reference_date"] - start).days if start else None
    left = [
        ("Paciente", f"{pet['name']} · {species_label(pet['species'])} · {pet['breed']}"),
        ("Idade", age_label(pet.get("age_years"), pet.get("age_months"))),
        ("Peso atual / superfície corporal", f"{br(pet['weight'], 2)} kg · {br(pet['body_surface_area'], 3)} m²"),
        ("Início do tratamento",
         f"{fdate(start)}" + (f" ({treatment_days} dias)" if treatment_days is not None else "")),
    ]
    right = [
        ("Tutor", " · ".join(x for x in (tutor.get("name"), tutor.get("phone"), tutor.get("email")) if x) or "—"),
        ("Médico-veterinário",
         " · ".join(x for x in (vet.get("name"), f"CRMV {vet['crmv']}" if vet.get("crmv") else None) if x) or "—"),
        ("Clínica", " · ".join(x for x in (clinic.get("name"), clinic.get("phone")) if x) or "—"),
        ("Registros", f"{len(data['sessions'])} sessões · {data['logs_count']} registros do tutor"),
    ]

    rows = []
    for (lk, lv), (rk, rv) in zip(left, right):
        rows.append([
            [Paragraph(clean(lk), st["label"]), Paragraph(clean(lv), st["value"])],
            [Paragraph(clean(rk), st["label"]), Paragraph(clean(rv), st["value"])],
        ])
    ident = Table(rows, colWidths=[CONTENT_W / 2] * 2)
    ident.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ident)

    # 2. Situacao atual (RF-06)
    story += _section("2. Situação atual (cuidados paliativos)", st)
    level = data["level"]
    fg, bg = LEVEL_COLORS[level]
    alerts = data["alerts"]
    alert_lines = [Paragraph(f"{_tag(a['level'], LEVEL_LABELS[a['level']].upper())}&nbsp;&nbsp;{clean(a['message'])}",
                             st["body"]) for a in alerts] or [Paragraph("Nenhum alerta no momento.", st["body"])]
    box = Table(
        [[Paragraph(f'<font color="{fg.hexval().replace("0x", "#")}"><b>{LEVEL_LABELS[level]}</b></font>', st["big"]),
          alert_lines]],
        colWidths=[32 * mm, CONTENT_W - 32 * mm],
    )
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), bg),
        ("BACKGROUND", (1, 0), (1, 0), SOFT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(box)
    effect = data.get("effect")
    if effect and effect["after_session"]["pain_mean"] is not None:
        after, other = effect["after_session"], effect["other_days"]
        text = (f"Nos {effect['window_days']} dias após as sessões: dor média {br(after['pain_mean'])}/10 e "
                f"sintomas em {br(after['symptom_percent'])}% dos registros")
        if other["pain_mean"] is not None:
            text += (f"; nos demais dias: dor {br(other['pain_mean'])}/10 e "
                     f"sintomas em {br(other['symptom_percent'])}%.")
        else:
            text += " (sem registros fora desse período para comparar)."
        story += [Spacer(1, 5), Paragraph(clean(text), st["small"])]

    # 3. Protocolos (RF-04)
    if data["protocols"]:
        story += _section("3. Protocolos de quimioterapia", st)
        rows = []
        for p in data["protocols"]:
            nxt = fdate(p["next_date"]) if p["next_date"] else "—"
            if p["overdue"]:
                nxt = f'{nxt} {_tag("atencao", "(atrasada)")}'
            rows.append([
                f"<b>{clean(p['name'])}</b>",
                clean(p["drug"] or "—") + (f"<br/>{br(p['dose_mg_m2'], 2)} " + clean("mg/m²") if p["dose_mg_m2"] else ""),
                f"{p['executed']} de {p['planned']}" + (f"<br/>a cada {p['interval_days']} dias" if p["interval_days"] else ""),
                fdate(p["start_date"]),
                _tag("atencao" if p["status"] == "suspenso" else None, STATUS_LABELS.get(p["status"], p["status"])),
                nxt,
            ])
        story.append(_table(["Protocolo", "Medicamento", "Sessões", "Início", "Status", "Próxima sessão"], rows,
                            [w * CONTENT_W for w in (0.25, 0.21, 0.15, 0.12, 0.11, 0.16)], st))

    # 4. Evolucao (RF-05)
    story += _section("4. Evolução do tratamento", st)
    weight, pain = data["weight"], data["pain"]
    symptoms = data["symptoms"]
    cards = [
        ("Peso desde o início",
         f"{signed(weight['change_kg'], 2)} kg ({signed(weight['change_percent'])}%)" if weight else "—",
         (f"de {br(weight['first'], 2)} para {br(weight['last'], 2)} kg"
          + (f" · tendência {signed(weight['trend_kg_per_week'], 2)} kg/semana" if weight["trend_kg_per_week"] is not None else "")
          + (" · <b>perda relevante (5% ou mais)</b>" if weight["relevant_loss"] else "")) if weight else "sem registros de peso"),
        ("Dor nas últimas 4 semanas",
         f"{br(pain['recent_mean'])}/10" if pain and pain["recent_mean"] is not None else "—",
         (f"{signed(pain['recent_change'])} vs. 4 semanas anteriores · " if pain and pain["recent_change"] is not None else "")
         + (f"dor intensa em {br(pain['severe_percent'])}% dos registros" if pain else "dor não avaliada")),
        ("Sintoma mais frequente",
         word(SYMPTOM_LABELS.get(symptoms[0]["symptom"], symptoms[0]["symptom"])) if symptoms else "—",
         f"em {br(symptoms[0]['percent'])}% dos {data['logs_count']} registros" if symptoms else "nenhum sintoma registrado"),
    ]
    card_cells = [[Paragraph(clean(t), st["label"]), Paragraph(clean(v), st["big"]),
                   Paragraph(s if "<b>" in s else clean(s), st["small"])] for t, v, s in cards]
    card_table = Table([card_cells], colWidths=[CONTENT_W / 3] * 3)
    card_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("LINEAFTER", (0, 0), (1, 0), 3, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(card_table)

    chart_w, chart_h = CONTENT_W / 2 - 6, 54 * mm
    charts = Table([[
        line_chart(data["pain_points"], "Escala de dor (0 a 10)", "Dor", chart_w, chart_h,
                   y_range=(0, 10), severe_line=7),
        line_chart(data["weight_points"], "Peso (kg)", "Peso", chart_w, chart_h),
    ]], colWidths=[CONTENT_W / 2] * 2)
    charts.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 10)]))
    story.append(charts)

    if symptoms:
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "<b>Frequência de sintomas:</b> " + clean("; ".join(
                f"{SYMPTOM_LABELS.get(s['symptom'], s['symptom'])} {s['count']}x ({br(s['percent'])}%)" for s in symptoms)),
            st["body"]))

    # 5. Sessoes
    if data["sessions"]:
        rows = []
        for s in reversed(data["sessions"]):  # mais recente primeiro
            tol = s["tolerance"]
            tol_level = {"boa": "estavel", "moderada": "atencao", "ruim": "critico"}.get(tol)
            rows.append([
                fdate(s["date"]),
                clean(s["drug"] or "—"),
                br(s["dose_mg_m2"], 2) if s["dose_mg_m2"] else "—",
                br(s["dose_mg"], 2) if s["dose_mg"] else "—",
                br(s["weight"], 2),
                _tag(tol_level, TOLERANCE_LABELS.get(tol, "—")) if tol else "—",
            ])
        story += _section("5. Sessões realizadas", st)
        story.append(_table(["Data", "Medicamento", "Dose (mg/m²)", "Dose aplicada (mg)", "Peso (kg)", "Tolerância*"],
                            rows, [w * CONTENT_W for w in (0.14, 0.30, 0.14, 0.16, 0.11, 0.15)], st))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "* Pelo diário do tutor do 1º ao 3º dia após a sessão. Ruim: dor 7 ou mais, febre ou falta de ar; "
            "moderada: outros sintomas ou dor 2 pontos acima do habitual.", st["small"]))

    # 6. Diario do tutor (MongoDB)
    story += _section("6. Diário do tutor (últimos registros)", st)
    if data["diary"]:
        rows = []
        for log in data["diary"]:
            status = " · ".join(x for x in (
                f"estado {WORDS.get(log['general_status'], log['general_status'])}" if log["general_status"] else None,
                f"apetite {WORDS.get(log['appetite'], log['appetite'])}" if log["appetite"] else None,
                f"energia {ENERGY.get(log['energy_level'], log['energy_level'])}" if log["energy_level"] else None,
            ) if x)
            obs = " · ".join(x for x in (status, log["notes"]) if x)
            pain_txt = f"{log['pain']}/10" if log["pain"] is not None else "—"
            rows.append([
                fdate(log["date"]),
                _tag("critico", pain_txt) if log["pain"] is not None and log["pain"] >= 7 else clean(pain_txt),
                br(log["weight"], 2) if log["weight"] else "—",
                clean(symptoms_text(log["symptoms"], log["other_symptoms"])),
                clean(obs or "—"),
            ])
        story.append(_table(["Data", "Dor", "Peso (kg)", "Sintomas", "Observações"], rows,
                            [w * CONTENT_W for w in (0.13, 0.08, 0.1, 0.27, 0.42)], st))
    else:
        story.append(Paragraph("O tutor ainda não fez registros no diário.", st["body"]))

    # 7. Documentos
    if data["documents"]:
        story += _section("7. Exames e documentos", st)
        rows = [[fdate(d["date"]), clean(d["title"]), clean(DOC_TYPES.get(d["doc_type"], d["doc_type"]))]
                for d in data["documents"]]
        story.append(KeepTogether(_table(["Data", "Documento", "Tipo"], rows,
                                         [w * CONTENT_W for w in (0.14, 0.6, 0.26)], st)))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm,
        bottomMargin=20 * mm, title=f"Relatório clínico - {pet['name']}", author="OncoPet",
        subject="Relatório clínico unificado (RF-07)",
    )
    footer = (f"{pet['name']} · emitido em {generated.strftime('%d/%m/%Y')} · "
              "documento de apoio; não substitui a avaliação do médico-veterinário")
    doc.build(story, canvasmaker=lambda *a, **k: _NumberedCanvas(*a, footer_text=footer, **k))
    return buffer.getvalue()
