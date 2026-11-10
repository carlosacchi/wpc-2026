"""Builds the WPC 2026 session deck on top of the official template.

Usage: python docs/session/build_deck.py [template.pptx] [output.pptx]
Content, timing and speaker notes live here; diagrams are native shapes, editable in PowerPoint.
"""
import sys
from pathlib import Path

import qrcode
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TEMPLATE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/Template_WPC2026.pptx"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "out/WPC2026-Copilot-sotto-controllo.pptx"
ASSETS = HERE / "assets"
REPO = "https://github.com/carlosacchi/wpc-2026"

RED = RGBColor(0xBD, 0x27, 0x16)
ORANGE = RGBColor(0xFB, 0xAE, 0x40)
GREY = RGBColor(0x66, 0x66, 0x66)
INK = RGBColor(0x26, 0x2B, 0x36)
NAVY = RGBColor(0x0A, 0x16, 0x40)
CODEBG = RGBColor(0x0D, 0x14, 0x2E)
BLUE = RGBColor(0x2F, 0x6B, 0xFF)
TEAL = RGBColor(0x12, 0x9E, 0x93)
VIOLET = RGBColor(0x6D, 0x5D, 0xF5)
GREEN = RGBColor(0x2E, 0x9E, 0x5B)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODE_FG = RGBColor(0xD6, 0xE2, 0xFF)
CODE_RED = RGBColor(0xFF, 0x7A, 0x6B)
CODE_GREEN = RGBColor(0x7E, 0xE0, 0x9C)
CODE_DIM = RGBColor(0x8A, 0x96, 0xB8)

prs = Presentation(TEMPLATE)
LAYOUT = {l.name: l for l in prs.slide_masters[0].slide_layouts}
NOTES: list[tuple[str, str]] = []

for sld in list(prs.slides._sldIdLst):
    prs.part.drop_rel(sld.rId)
    prs.slides._sldIdLst.remove(sld)


def new(layout, title=None, notes="", hidden=False):
    s = prs.slides.add_slide(LAYOUT[layout])
    if title is not None and s.shapes.title is not None:
        s.shapes.title.text = title
    s.notes_slide.notes_text_frame.text = notes.strip()
    NOTES.append((title or {"1_Diapositiva titolo": "Titolo", "Vuota": "Hook"}.get(layout, layout), notes.strip()))
    if hidden:
        s._element.set("show", "0")
    return s


def ph(s, idx):
    return next(p for p in s.placeholders if p.placeholder_format.idx == idx)


def drop(s, idx):
    p = ph(s, idx)
    p._element.getparent().remove(p._element)


def fill_text(tf, items, size=None, color=None):
    """items: str, (str, level) or (str, level, {'bold':..,'color':..})."""
    tf.clear()
    for i, item in enumerate(items):
        text, level, style = (item, 0, {}) if isinstance(item, str) else (item + ({},))[:3]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        for j, part in enumerate(text.split("**")):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            r.font.bold = style.get("bold", j % 2 == 1)
            if size or style.get("size"):
                r.font.size = Pt(style.get("size", size))
            if style.get("color") or color:
                r.font.color.rgb = style.get("color", color)


def box(s, x, y, w, h, text="", fill=NAVY, fg=WHITE, size=14, bold=False, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        align=PP_ALIGN.CENTER, line=None, anchor=MSO_ANCHOR.MIDDLE, font=None):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = 0.12
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.5)
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right"):
        setattr(tf, side, Inches(0.08))
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    lines = text if isinstance(text, list) else [text]
    tf.clear()
    for i, line_ in enumerate(lines):
        t, st = (line_, {}) if isinstance(line_, str) else line_
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        for j, part in enumerate(t.split("**")):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            r.font.size = Pt(st.get("size", size))
            r.font.bold = st.get("bold", bold or j % 2 == 1)
            r.font.color.rgb = st.get("color", fg)
            if font or st.get("font"):
                r.font.name = st.get("font", font)
    return sh


def label(s, x, y, w, h, text, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    return box(s, x, y, w, h, text, fill=None, fg=color, size=size, bold=bold, shape=MSO_SHAPE.RECTANGLE,
               align=align, anchor=anchor)


def arrow(s, x1, y1, x2, y2, color=GREY, width=2):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    ln.append(tail)
    return c


def code(s, x, y, w, h, lines, size=12, title=None):
    """lines: list of (text, color)."""
    panel = box(s, x, y, w, h, fill=CODEBG)
    tf = panel.text_frame
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.14)
    tf.clear()
    rows = ([(title, CODE_DIM)] if title else []) + lines
    for i, (t, col) in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = t
        r.font.name = "Consolas"
        r.font.size = Pt(size)
        r.font.color.rgb = col
    return panel


def number(s, x, y, n, d=0.55, fill=RED):
    return box(s, x, y, d, d, f"{n:02d}", fill=fill, size=16, bold=True, shape=MSO_SHAPE.OVAL)


def source(s, text):
    label(s, 0.5, 6.55, 9.5, 0.3, text, size=10, color=GREY)


def picture(s, name, x, y, w=None, h=None):
    return s.shapes.add_picture(str(ASSETS / name), Inches(x), Inches(y),
                                Inches(w) if w else None, Inches(h) if h else None)


def section(n, title, sub, notes):
    s = new("Intestazione sezione", f"{n}. {title}", notes)
    fill_text(ph(s, 1).text_frame, [sub])
    return s


# ---------------------------------------------------------------- 1. Title
s = new("1_Diapositiva titolo", None, """
[0:00–1:00] Presentazione.
- Chi sono, una frase. Poi subito la domanda: quanti usano Copilot o un agente per scrivere IaC? Quanti lo lasciano arrivare in produzione?
- Promessa: 45 minuti, un caso reale, una piattaforma vera su Azure, una demo live che fallisce di proposito.
""")
s.shapes.title.text_frame.clear()
tp = s.shapes.title.text_frame.paragraphs[0]
r = tp.add_run(); r.text = "Copilot sotto controllo"
tp2 = s.shapes.title.text_frame.add_paragraph()
r2 = tp2.add_run(); r2.text = "Platform Engineering multi-tenant su Azure con Terraform, Bicep e policy gates"
r2.font.size = Pt(22); r2.font.bold = False
fill_text(ph(s, 1).text_frame, ["Carlo Sacchi", "Lead DevOps | Metyis"])

# ---------------------------------------------------------------- 2. Hook
s = new("Vuota", None, """
[1:00–2:00] Il gancio.
- L'agente porta blocchi di infrastruttura in pochi secondi. Il cancello in mezzo non lo apre l'agente.
- "Oggi non parliamo di prompt migliori. Parliamo di chi ha la chiave del cancello."
- Non è sfiducia verso Copilot: è lo stesso schema che usiamo per le persone.
""")
picture(s, "cover.jpg", 0, 0, w=13.333)
label(s, 0.6, 2.2, 5.6, 2.6, [("L'agente scrive in secondi.", {"size": 36, "bold": True, "color": WHITE}),
                             ("Chi decide cosa arriva in Azure?", {"size": 30, "color": ORANGE})], color=WHITE)

# ---------------------------------------------------------------- 3. Agenda
s = new("Agenda", "Agenda", """
[2:00–2:30] Agenda in 30 secondi. La demo è al centro e dura un terzo della sessione.
""")
fill_text(ph(s, 1).text_frame, [
    "Il caso: lo scope sbagliato, eseguito correttamente",
    "Quando a scrivere è un agente",
    "Una piattaforma che decide al posto di chi scrive",
    "Demo live: Copilot, PR, gate, approvazione, canary",
    "Rollback come roll-forward, limiti, takeaway",
], size=24)

# ---------------------------------------------------------------- Act 1
section(1, "Lo scope sbagliato, eseguito correttamente", "Due post-mortem pubblici, nessun agente coinvolto", """
[2:30] Prima di parlare di AI, due incidenti senza AI. Il problema esisteva già.
""")

s = new("Due colonne", "Atlassian, aprile 2022", """
[2:30–5:00] Atlassian.
- Script di manutenzione per rimuovere un'app legacy (Insight). Riceve gli ID dei siti, non dell'app.
- Lo script fa esattamente quello che gli è stato chiesto: cancellazione permanente.
- 883 siti, 775 clienti, fino a 14 giorni per tornare online.
- Il PIR dice: nessun cross-check degli ID. Azioni: soft delete ovunque, staged rollout, rollback testato.
- Immagine: si voleva colpire il quadratino bianco, la cornice rossa ha preso l'isolato.
""")
fill_text(ph(s, 1).text_frame, [
    "Uno script doveva rimuovere un'app legacy",
    "Ha ricevuto gli ID dei **siti**, non dell'app",
    "Cancellazione permanente: **883 siti, 775 clienti**",
    "Ripristino fino a **14 giorni**",
    "Il PIR: nessun controllo che gli ID fossero quelli giusti",
    ("Azioni: soft delete, staged rollout, rollback testato", 1),
], size=20)
drop(s, 2)
picture(s, "wrong-scope.jpg", 6.75, 1.63, w=6.08)
source(s, "atlassian.com/engineering/post-incident-review-april-2022-outage")

s = new("Solo titolo", "Azure DevOps, maggio 2023", """
[5:00–7:30] Azure DevOps, South Brazil.
- Una PR enorme di migrazione SDK. Dentro, un refuso: "cancella lo snapshot" diventa "cancella il server SQL".
- Il canary c'era! Ring 0 interno: nessuno snapshot abbastanza vecchio, quindi nessun effetto.
- Ring 1 South Brazil: condizione presente, 17 database di produzione cancellati, circa 10 ore.
- Messaggio: il canary riduce il raggio, ma non sostituisce il controllo sull'effetto. Tra le correzioni: resource lock.
- Teniamo a mente il lock: lo ritroveremo nella demo.
""")
steps = [("PR enorme\nmigrazione SDK", NAVY), ("Refuso:\ndelete DB → delete SQL Server", NAVY),
         ("Ring 0 interno\nnessuno snapshot → OK", GREEN), ("Ring 1 South Brazil\n17 DB cancellati, ~10 h", RED)]
for i, (t, c) in enumerate(steps):
    x = 0.6 + i * 3.15
    box(s, x, 2.0, 2.75, 1.5, t.split("\n"), fill=c, size=18)
    if i < 3:
        arrow(s, x + 2.78, 2.75, x + 3.12, 2.75)
label(s, 0.6, 3.9, 12, 0.5, "Correzioni pubblicate", size=18, color=RED, bold=True)
label(s, 0.6, 4.4, 12, 1.6, [
    "• Test sull'intero ciclo di vita del job di pulizia",
    "• **Resource lock** sui server SQL di produzione",
    "• Snapshot su server separati da quelli di produzione",
], size=18)
source(s, "status.dev.azure.com/_event/392143683/post-mortem")

s = new("Solo titolo", "Lo schema comune", """
[7:30–9:00] Lo schema.
- 1: lo scope reale è più grande di quello percepito.
- 2: tutto è sintatticamente valido; validate e review del diff non vedono l'effetto.
- 3: nessun livello indipendente tra il comando e l'effetto irreversibile.
- Frase chiave: il problema non è chi scrive il cambiamento, è cosa lo lascia passare.
- Ponte: e se a scriverlo è un agente che lavora dieci volte più veloce?
""")
cols = [("Scope più ampio del previsto", "Sito invece di app, server invece di database"),
        ("Sintassi valida, effetto distruttivo", "Il codice passa i test; l'effetto si vede solo nel piano"),
        ("Nessun livello indipendente", "Tra il comando e l'irreversibile non c'è nulla che dica no")]
for i, (h, b) in enumerate(cols):
    x = 0.6 + i * 4.2
    number(s, x + 1.6, 1.9, i + 1, d=0.8)
    label(s, x, 2.9, 3.8, 0.6, h, size=20, bold=True, align=PP_ALIGN.CENTER)
    label(s, x, 3.55, 3.8, 1.2, b, size=16, color=GREY, align=PP_ALIGN.CENTER)
box(s, 0.6, 5.2, 12.1, 0.9, "Il problema non è chi scrive il cambiamento. È cosa lo lascia passare.",
    fill=LIGHT, fg=RED, size=22, bold=True)

# ---------------------------------------------------------------- Act 2
section(2, "Ora il cambiamento lo scrive un agente", "Stesso schema, più velocità", """
[9:00] Stesso schema, attore diverso.
""")

s = new("Solo titolo", "Casi agentici: stesso schema", """
[9:00–11:00] Tre casi, una frase ciascuno.
- PocketOS: l'agente trova un token in un file non correlato, il token può fare tutto, una chiamata API cancella volume e backup. Le credenziali raggiungibili sono il perimetro reale.
- Replit: code freeze dichiarato in chat, l'agente cancella comunque il DB. Un'istruzione non è un controllo.
- Amazon Q: prompt distruttivo entrato via contributo esterno nell'estensione. Anche la supply chain dell'agente è superficie d'attacco.
- Non sono storie contro gli agenti: sono storie di piattaforme senza confini.
""")
rows = [("Caso", "Cosa è successo", "Lezione"),
        ("PocketOS\naprile 2026", "Un agente in staging usa un token trovato in un file non correlato: una chiamata API cancella database e backup",
         "Le credenziali raggiungibili sono il perimetro reale dell'agente"),
        ("Replit\nluglio 2025", "Durante un code freeze dichiarato, l'agente cancella il database di produzione",
         "Un'istruzione in linguaggio naturale non è un controllo"),
        ("Amazon Q\nluglio 2025", "Un prompt distruttivo entra nell'estensione tramite un contributo esterno (AWS-2025-015)",
         "La supply chain dell'agente è superficie d'attacco")]
tbl = s.shapes.add_table(4, 3, Inches(0.5), Inches(1.7), Inches(12.3), Inches(4.4)).table
for c, w in enumerate((2.2, 6.0, 4.1)):
    tbl.columns[c].width = Inches(w)
for r_, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = tbl.cell(r_, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RED if r_ == 0 else (LIGHT if r_ % 2 else WHITE)
        tf = cell.text_frame
        tf.clear()
        tf.word_wrap = True
        run = tf.paragraphs[0].add_run()
        run.text = val
        run.font.size = Pt(16 if r_ == 0 else 15)
        run.font.bold = r_ == 0 or c == 0
        run.font.color.rgb = WHITE if r_ == 0 else INK
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
source(s, "The Register, 27/04/2026 · AWS Security Bulletin AWS-2025-015 · dettagli in docs/case-study.md")

s = new("Due colonne con sottotitoli", "Copilot: cosa copre e cosa no", """
[11:00–14:00] Onestà su Copilot.
- Il coding agent ha già protezioni serie: branch propri, non approva né unisce le sue PR, workflow da approvare, firewall.
- La regola "chi chiede la PR non la approva" funziona solo se la branch protection richiede almeno un'approvazione. Nel mio repo era a zero: regola inattiva.
- In VS Code agent mode i comandi chiedono conferma, ma l'auto-approvazione è un'impostazione. E il terminale dell'agente è il MIO terminale, con il MIO az login.
- Le istruzioni del repo (.github/copilot-instructions.md) le uso e le mostro: guidano, non bloccano.
- Ciò che Copilot non può sapere è il contesto della piattaforma: quale tenant, update o replace, quali credenziali. È lavoro del Platform Engineering.
""")
fill_text(ph(s, 1).text_frame, ["Cosa Copilot fa già"], size=20, color=RED)
fill_text(ph(s, 2).text_frame, [
    "Coding agent: lavora su branch propri",
    "Non approva né unisce le proprie PR",
    "I workflow sulle sue PR richiedono approvazione",
    "Agent mode in VS Code: conferma dei comandi in terminale",
    "Istruzioni di repository: guida il comportamento",
], size=17)
fill_text(ph(s, 3).text_frame, ["Cosa non può sapere"], size=20, color=RED)
fill_text(ph(s, 4).text_frame, [
    "Qual è il tenant giusto per quella risorsa",
    "Se un cambio è un update o un **replace** in Azure",
    "Quanto valgono le credenziali del **tuo** terminale",
    "Se l'approvazione è davvero obbligatoria (0 reviewer = regola spenta)",
    "**Istruzioni = guida. Gate = controllo.**",
], size=17)

# ---------------------------------------------------------------- Act 3
section(3, "La piattaforma decide, non chi scrive", "Il laboratorio: github.com/carlosacchi/wpc-2026", """
[14:00] Passiamo dal problema alla piattaforma. Tutto quello che vedete è nel repo pubblico e gira davvero in Azure.
""")

s = new("Solo titolo", "Tenant simulati, confini reali", """
[14:00–16:30] Il lab.
- Una subscription, una directory: lo dico subito. È il caso di una piattaforma interna multi-team, o di un solo team con ruoli separati.
- Ogni tenant è un resource group con: il suo Storage, il suo container di state, la sua identità di apply, il suo environment GitHub.
- La MI di apply di Sales non può toccare Operations né lo state di Operations.
- La MI di plan è Reader, con un ruolo custom solo per il what-if.
- Su ogni RG: policy Deny per lo Storage pubblico, DenyAction sul delete, lock CanNotDelete.
- La mappa tenant → RG sta nel gate, non nei file che l'agente modifica.
""")
box(s, 0.45, 1.6, 12.4, 4.85, fill=None, line=GREY)
label(s, 0.6, 1.62, 6, 0.4, "Subscription · una directory Entra", size=13, color=GREY)
cards = [("wpc-2026 · piattaforma", VIOLET, ["Storage di state (lock)", "Container tfstate-<tenant>", "MI plan: Reader + what-if",
                                            "Policy: Deny + DenyAction"]),
         ("wpc-2026-sales · ring 0", TEAL, ["Storage wpc26salesb0b966", "MI apply sales: solo questo RG", "Environment «sales»",
                                           "Lock CanNotDelete + DenyAction"]),
         ("wpc-2026-operations · ring 1", BLUE, ["Storage wpc26opsb0b966", "MI apply ops: solo questo RG",
                                                "Environment «operations»", "Lock CanNotDelete + DenyAction"])]
for i, (h, c, items) in enumerate(cards):
    x = 0.75 + i * 4.1
    box(s, x, 2.1, 3.8, 0.6, h, fill=c, size=16, bold=True)
    box(s, x, 2.7, 3.8, 2.6, ["• " + t for t in items], fill=LIGHT, fg=INK, size=17, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP)
box(s, 0.75, 5.55, 12.0, 0.7, "La mappa tenant → resource group sta nel gate della piattaforma, non nei file che l'agente modifica",
    fill=WHITE, fg=RED, size=16, bold=True, line=RED)

s = new("Solo titolo", "Il flusso di un ring", """
[16:30–19:00] Il flusso. Seguite i colori delle identità.
- PR: la CI validate gira senza credenziali Azure.
- Plan: Terraform plan salvato E Bicep what-if sullo stesso RG. Due motori, due preview.
- Due gate: devono dire ALLOW entrambi. Se uno dice DENY non esiste artefatto e l'environment non viene mai raggiunto.
- Approvazione: environment del tenant, revisore obbligatorio, chi lancia non può approvare, niente bypass admin.
- Apply: identità del tenant, e solo il piano di QUESTA run: stesso commit, stesso sha256.
- Verify: Storage privato, lock, policy, nessun drift. Solo allora parte il ring successivo.
""")
flow = [("PR", "CI validate\nsenza credenziali", GREY), ("Plan", "terraform plan\n+ Bicep what-if", VIOLET),
        ("Gate ×2", "DENY: delete, replace,\nfuori tenant, rinomina", RED), ("Approva", "environment del tenant\nno self-review", ORANGE),
        ("Apply", "MI del tenant\nstesso piano, sha256", TEAL), ("Verify", "privato, lock,\npolicy, no drift", GREEN)]
for i, (h, b, c) in enumerate(flow):
    x = 0.45 + i * 2.1
    box(s, x, 1.9, 1.9, 0.75, h, fill=c, size=17, bold=True, shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)
    label(s, x, 2.75, 1.9, 1.1, b.split("\n"), size=13, align=PP_ALIGN.CENTER)
lanes = [("Chi agisce", INK, ["Copilot + persona", "MI plan (Reader)", "MI plan", "Revisore umano", "MI apply sales", "MI plan"])]
for i, who in enumerate(lanes[0][2]):
    box(s, 0.55 + i * 2.1, 4.05, 1.7, 0.55, who, fill=LIGHT, fg=INK, size=12)
label(s, 0.45, 4.7, 12.5, 0.4, "Ring 0 sano → Ring 1 (operations), con gli stessi passi e le sue identità", size=16, color=RED, bold=True)
code(s, 0.45, 5.2, 12.4, 1.25, [
    ("gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only", CODE_FG),
    ("PASS: workload plan satisfies the selected lab rules.", CODE_GREEN),
    ("HEALTHY: wpc26salesb0b966 in wpc-2026-sales is private, locked, protected by denyAction and drift-free.", CODE_GREEN),
], size=12)

s = new("Vuota", "Cinque livelli, ognuno presuppone che il precedente fallisca", """
[19:00–21:00] Difesa a livelli. Ogni livello presuppone che il precedente possa fallire, anche se chi fallisce è una persona che modifica il codice.
- 1 gate in CI, 2 approvazione umana, 3 identità per tenant, 4 Azure Policy DenyAction, 5 lock e prevent_destroy.
- I livelli 4 e 5 vivono in Azure, fuori dalla pipeline: funzionano anche se qualcuno aggira GitHub. Come la correzione di Azure DevOps.
""")
picture(s, "defense-layers.jpg", 0, 0, w=13.333)
label(s, 8.85, 0.45, 4.3, 1.4, "Cinque livelli, ognuno presuppone che il precedente fallisca", size=24, color=WHITE, bold=True)
layers = [("Gate in CI", "plan + what-if: niente delete, replace, fuori tenant"),
          ("Approvazione umana", "environment del tenant, no self-review"),
          ("Identità per tenant", "apply limitato al proprio RG e al proprio state"),
          ("Azure Policy DenyAction", "nessun delete degli Storage del lab"),
          ("Lock + prevent_destroy", "CanNotDelete sui RG dei tenant e sullo state")]
for i, (h, b) in enumerate(layers):
    y = 2.0 + i * 0.95
    number(s, 8.85, y, i + 1, d=0.6, fill=[TEAL, BLUE, VIOLET, RED, RED][i])
    label(s, 9.55, y - 0.08, 3.7, 0.45, h, size=19, color=WHITE, bold=True)
    label(s, 9.55, y + 0.32, 3.7, 0.6, b, size=13, color=CODE_FG)

s = new("Solo titolo", "Una rinomina, due rischi", """
[21:00–23:00] La slide tecnica più importante.
- Terraform: cambiare il nome forza la sostituzione. -/+ vuol dire: cancello quello vecchio e ne creo uno nuovo. Su uno Storage con dati, è una perdita di dati.
- Bicep in modalità incrementale non cancella: crea il nuovo e lascia l'originale orfano, fuori dal template. Sembra innocuo, ma ora hai due Storage e i dati sono in quello che nessuno gestisce.
- Il gate legge entrambi i preview e dice DENY a entrambi. terraform validate e bicep build invece passano.
""")
code(s, 0.45, 1.65, 6.1, 3.9, [
    ("# module.storage.azurerm_storage_account.this", CODE_DIM),
    ("#   must be replaced", CODE_DIM),
    ("-/+ resource \"azurerm_storage_account\" \"this\" {", CODE_RED),
    ("    ~ name = \"wpc26salesb0b966\"", CODE_FG),
    ("          -> \"wpc26salesb0b966r\"", CODE_RED),
    ("          # forces replacement", CODE_RED),
    ("Plan: 1 to add, 0 to change, 1 to destroy.", CODE_FG),
    ("", CODE_FG),
    ("DENY: ...storage_account.this: delete, replacement", CODE_RED),
    ("      or unsupported action is forbidden.", CODE_RED),
], size=13, title="Terraform plan")
code(s, 6.75, 1.65, 6.1, 3.9, [
    ("+ Create  .../storageAccounts/wpc26salesb0b966r", CODE_GREEN),
    ("* Ignore  .../storageAccounts/wpc26salesb0b966", CODE_DIM),
    ("", CODE_FG),
    ("Nessun delete: l'originale resta orfano,", CODE_FG),
    ("fuori dal template, con i dati dentro.", CODE_FG),
    ("", CODE_FG),
    ("DENY: Create wpc26salesb0b966r while", CODE_RED),
    ("      wpc26salesb0b966 stays outside the template", CODE_RED),
    ("      (implicit rename).", CODE_RED),
], size=13, title="Bicep What-If (incremental, ProviderNoRbac)")
box(s, 0.45, 5.75, 12.4, 0.7, "validate e bicep build passano entrambi. La decisione si prende sul piano, non sulla sintassi.",
    fill=LIGHT, fg=RED, size=18, bold=True)

# ---------------------------------------------------------------- Act 4
section(4, "Demo", "Copilot Chat in VS Code → PR → rollout governato", """
[23:00] Demo. Runbook: docs/session/demo-runbook.md. Se qualcosa non risponde entro 60 secondi, passo alle run registrate (slide di backup nascoste).
""")

s = new("Solo titolo", "Cosa guardare durante la demo", """
[23:00–38:00] Slide di orientamento: la lascio sullo schermo nei momenti di attesa della CI.
- 1 ~3 min, 2 ~3 min, 3 ~3 min, 4 ~4 min, 5 ~1 min. Margine 1 min.
- Nei tempi di attesa: commentare le identità (chi sta agendo adesso?).
- Se Copilot segnala da solo il rischio della rinomina: bene, lo dico e procedo con la modifica esplicita. È la dimostrazione che l'istruzione guida, ma il gate decide comunque.
""")
demo = [("Copilot rinomina lo Storage di Sales", "PR verde: validate non vede il problema"),
        ("Rollout: due DENY", "plan -/+ e what-if orfano · nessun artefatto, nessuna approvazione"),
        ("Copilot corregge", "nome originale + service_label → solo un tag"),
        ("Approvazione e canary", "il revisore approva · apply · health · ring 1"),
        ("Rete di sicurezza", "delete diretto da Owner → RequestDisallowedByPolicy")]
for i, (h, b) in enumerate(demo):
    y = 1.7 + i * 0.98
    number(s, 0.6, y, i + 1, d=0.7, fill=RED if i in (1, 4) else NAVY)
    label(s, 1.5, y - 0.02, 5.4, 0.5, h, size=20, bold=True)
    label(s, 1.5, y + 0.38, 6.2, 0.5, b, size=15, color=GREY)
code(s, 8.0, 1.7, 4.85, 3.6, [
    ("$ az storage account delete \\", CODE_FG),
    ("    -g wpc-2026-sales \\", CODE_FG),
    ("    -n wpc26salesb0b966 --yes", CODE_FG),
    ("", CODE_FG),
    ("(RequestDisallowedByPolicy)", CODE_RED),
    ("Resource 'wpc26salesb0b966'", CODE_RED),
    ("was disallowed by policy.", CODE_RED),
    ("", CODE_FG),
    ("# eseguito come Owner", CODE_DIM),
    ("# della subscription", CODE_DIM),
], size=13, title="Passo 5, output reale")

# ---------------------------------------------------------------- Act 5
section(5, "Rollback, limiti, takeaway", "Tornare indietro senza cancellare", """
[38:00] Ultima parte: come rifare tutto domani, e cosa NON dimostra il lab.
""")

s = new("Solo titolo", "Rollback = roll-forward", """
[38:00–40:00] Rollback.
- Non si torna indietro cancellando: si riporta in produzione l'ultima configurazione nota e buona, con gli stessi gate e la stessa approvazione.
- demo/baseline è versionata. npm run demo:reset apre la PR di ripristino, attende la CI, fa il merge e lancia il rollout.
- Idempotente: se tutto è allineato non cambia nulla e l'apply viene saltato. Così ho preparato questa sala.
- Il teardown è break-glass: disattivo la DenyAction, tolgo il lock, cancello. Tre passi deliberati, con approvazione.
""")
rb = [("Baseline versionata", "demo/baseline/", NAVY), ("Cambi in sessione", "file team + tag", GREY),
      ("npm run demo:reset", "PR di ripristino + CI", VIOLET), ("Stesso rollout", "gate + approvazione", ORANGE),
      ("Azure riallineato", "in-place, zero delete", GREEN)]
for i, (h, b, c) in enumerate(rb):
    x = 0.45 + i * 2.52
    box(s, x, 1.9, 2.2, 1.3, [(h, {"bold": True, "size": 16}), (b, {"size": 13})], fill=c)
    if i < 4:
        arrow(s, x + 2.22, 2.55, x + 2.5, 2.55)
code(s, 0.45, 3.6, 6.6, 2.5, [
    ("$ npm run demo:status", CODE_FG),
    ("FILES: team files match demo/baseline.", CODE_GREEN),
    ("", CODE_FG),
    ("$ npm run demo:reset", CODE_FG),
    ("PR → validate → merge → rollout rings=all", CODE_FG),
    ("Apply skipped: no changes · HEALTHY", CODE_GREEN),
], size=13)
box(s, 7.35, 3.6, 5.5, 2.5, [("Teardown = break-glass", {"bold": True, "size": 20, "color": RED}),
                            ("1. DenyAction → effect=Disabled", {"size": 16}),
                            ("2. Rimuovere il lock CanNotDelete", {"size": 16}),
                            ("3. Delete, con approvazione esplicita", {"size": 16})],
    fill=LIGHT, fg=INK, align=PP_ALIGN.LEFT)

s = new("Titolo e contenuto", "Limiti dichiarati", """
[40:00–41:30] Onestà. Questi limiti li dico io prima che li chieda il pubblico.
- Il più importante: chi ha ruoli ereditati sulla subscription scavalca tutto. Nel mio lab il revisore era Contributor sulla subscription: l'ho tolto prima di questa sessione. Controllate i vostri.
""")
fill_text(ph(s, 1).text_frame, [
    "**Una directory, una subscription:** isolamento per RG, identità, state e policy. Ruoli ereditati sulla subscription lo scavalcano",
    "**Canary per tenant**, non uno split di traffico",
    "**What-if è un preview:** con ProviderNoRbac non verifica i permessi di scrittura",
    "**DenyAction copre solo delete:** il replace lo fermano gate e prevent_destroy",
    "**I gate sono regole didattiche esplicite**, non uno scanner di sicurezza completo",
    "**Chi amministra il repo** può riconfigurare branch protection ed environment",
], size=20)

s = new("Solo titolo", "Da portare a casa", """
[41:30–43:00] Tre frasi. Ripeterle lentamente.
- La decisione si prende sul piano, non sulla sintassi.
- Credenziali e approvazioni per tenant: il raggio d'azione è un'architettura, non un'istruzione.
- Una rete di sicurezza fuori dalla pipeline, perché prima o poi qualcuno la aggira.
- Chiusura: Copilot accelera. La piattaforma decide.
""")
take = [("Decide il piano", "terraform plan e what-if, letti da un gate. Non validate, non la review del diff."),
        ("Confini per tenant", "Identità, state e approvazione per tenant. Il raggio d'azione è architettura."),
        ("Rete fuori dalla pipeline", "Policy e lock in Azure: valgono anche per chi aggira GitHub.")]
for i, (h, b) in enumerate(take):
    x = 0.6 + i * 4.2
    number(s, x + 1.6, 1.9, i + 1, d=0.8)
    label(s, x, 2.9, 3.8, 0.6, h, size=22, bold=True, align=PP_ALIGN.CENTER)
    label(s, x, 3.55, 3.8, 1.4, b, size=16, color=GREY, align=PP_ALIGN.CENTER)
box(s, 0.6, 5.2, 12.1, 0.9, "Copilot accelera. La piattaforma decide.", fill=RED, size=26, bold=True)

s = new("Titolo e contenuto", "Grazie! Codice, demo e fonti", """
[43:00–45:00] Q&A. Lasciare il QR sullo schermo.
""")
fill_text(ph(s, 1).text_frame, [
    "Repository del lab: **github.com/carlosacchi/wpc-2026**",
    ("Workflow, gate, bootstrap Terraform, test", 1),
    ("docs/case-study.md: post-mortem e mappatura sui controlli", 1),
    ("docs/session/demo-runbook.md: come rifare la demo", 1),
    "Atlassian PIR, aprile 2022",
    "Azure DevOps post-mortem, maggio 2023",
    "GitHub Docs: rischi e mitigazioni del coding agent Copilot",
], size=20)
ph(s, 1).width = Inches(8.6)
qr_path = HERE / "out/qr-repo.png"
qr_path.parent.mkdir(parents=True, exist_ok=True)
qrcode.make(REPO, border=1).save(qr_path)
s.shapes.add_picture(str(qr_path), Inches(9.6), Inches(2.0), Inches(3.2), Inches(3.2))

# ---------------------------------------------------------------- Hidden backups
s = new("Solo titolo", "Backup: approvazione dell'environment", """
BACKUP (nascosta). Run reale 42823102175: il revisore azureitaliadevops approva il deployment sales. Chi ha lanciato la run (carlosacchi) non può approvare: current_user_can_approve = false.
""", hidden=True)
picture(s, "backup-approval.jpg", 1.6, 1.55, h=5.0)

s = new("Solo titolo", "Backup: canary Sales, output reali", """
BACKUP (nascosta). Run 42823102175 (canary) e 42917201757 (rings=all: Sales senza modifiche, apply saltato).
""", hidden=True)
code(s, 0.45, 1.6, 12.4, 4.8, [
    ("Plan + gates (sales)", CODE_DIM),
    ("Plan: 1 to add, 0 to change, 0 to destroy.", CODE_FG),
    ("PASS: workload plan satisfies the selected lab rules.", CODE_GREEN),
    ("IMPACT: Create .../resourceGroups/wpc-2026-sales/.../storageAccounts/wpc26salesb0b966", CODE_FG),
    ("PASS: Bicep What-If satisfies the selected lab rules.", CODE_GREEN),
    ("Apply after human approval (sales)", CODE_DIM),
    ("PASS: sales plan from this run (42823102175), commit 7e8edd1..., SHA256 283cc282...", CODE_GREEN),
    ("Apply complete! Resources: 1 added, 0 changed, 0 destroyed.", CODE_FG),
    ("Ring health check (sales)", CODE_DIM),
    ("HEALTHY: wpc26salesb0b966 in wpc-2026-sales is private, locked, protected by denyAction and drift-free.", CODE_GREEN),
], size=14)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)

md = ["# Speaker notes", "", "Generato da `build_deck.py`: modificare lì, non qui.", ""]
for i, (t, n) in enumerate(NOTES, 1):
    md += [f"## {i}. {t}", "", n or "_(nessuna nota)_", ""]
(HERE / "speaker-notes.md").write_text("\n".join(md), encoding="utf-8")
print(f"OK: {len(prs.slides)} slides -> {OUT}")
