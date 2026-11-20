"""Builds the WPC 2026 session deck on top of the official template.

Usage: python docs/session/build_deck.py [template.pptx] [output.pptx]
Content, timing and speaker notes live here; diagrams are native shapes, editable in PowerPoint.
"""
import re
import sys
from pathlib import Path

import qrcode
from PIL import Image
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


TALK_SECONDS = 45 * 60
CLOCK = [0]  # running time in seconds; notes get their [start–end] from here
TIME_RE = re.compile(r"^\[(\d+):(\d\d)(?:–(\d+):(\d\d))?\]\s*")

RECITATIONS = {
    "Titolo": """Buongiorno. Chi di voi usa già Copilot, o un altro agente, per scrivere Terraform o Bicep? [pausa]

E prima di applicare quel codice in produzione, chi controlla il piano? [pausa]

Non è un test: oggi vediamo come verificare l'effetto di una modifica prima che arrivi in Azure. Nella demo il gate fermerà una rinomina rischiosa: quello sarà il risultato giusto.""",
    "Chi sono": """Sono Carlo Sacchi, lavoro come Lead DevOps in Metyis e mi occupo di Azure e Infrastructure as Code. Sono anche Microsoft MVP per Azure e co-conduco Azure Italia Podcast, un podcast in italiano dedicato ad Azure.

Vivo ad Amsterdam, quindi la pizza che vedete è metà italiana e metà olandese. Ma oggi siamo qui soprattutto per parlare di una domanda concreta: quando un agente può scrivere infrastruttura, chi decide se quella modifica è davvero sicura da applicare?""",
    "Hook": """Oggi chiedere a un agente di scrivere Terraform costa meno che chiedere un caffè. Il codice arriva in pochi secondi e spesso è scritto molto bene. Ma la qualità del codice non basta a dirci se l'effetto che produrrà è quello giusto.

Per questo non parleremo di prompt migliori. Parleremo di chi ha la chiave del cancello. Non è sfiducia verso Copilot: sono le stesse regole che chiediamo alle persone da anni — review, piano e approvazione. L'agente può entrare in quel processo; non deve sostituirlo.""",
    "Agenda": """Partiamo da due incidenti reali, per vedere che il problema dello scope sbagliato esisteva già prima degli agenti. Poi vedremo cosa cambia quando a scrivere è un agente e come una piattaforma può decidere cosa arriva in Azure.

Al centro c'è una demo live. Chiuderemo con il rollback e con i limiti del laboratorio: li esplicito perché è importante distinguere ciò che dimostriamo da ciò che non dimostriamo.""",
    "Le parole di questa sessione (1/2)": """Prima di entrare nei casi, allineiamo alcune parole. Non leggerò tutte le definizioni: mi interessa che ci capiamo quando le userò.

Un ring, o canary, è il primo gruppo che riceve un cambiamento; nel nostro laboratorio il gruppo è un team intero. Un Environment di GitHub è la destinazione del deploy e può richiedere l'approvazione di una persona. Il gate è il controllo automatico che legge il piano e decide se la pipeline può proseguire.

Infine, una Managed Identity è un'identità Azure senza password salvate: nel laboratorio ne useremo una per il plan e identità di apply separate per i team.""",
    "Le parole di questa sessione (2/2)": """Due parole avranno qui un significato preciso. Quando dico tenant intendo un team, non una directory Entra ID: in questo laboratorio Sales e Operations sono due tenant simulati, isolati con resource group e identità diverse.

Quando dico replace intendo che una risorsa viene cancellata e ricreata. Per uno Storage che contiene dati non è una semplice rinomina: può significare perdere quei dati.

Plan e What-If sono entrambi anteprime, ma arrivano da strumenti diversi. Terraform confronta codice, state e Azure; ARM confronta il template con ciò che esiste. Useremo entrambi per confrontare due modi diversi in cui una rinomina può andare male.""",
    "1. Lo scope sbagliato, eseguito correttamente": """Prima di parlare di intelligenza artificiale, guardiamo due incidenti in cui l'intelligenza artificiale non c'entra. In entrambi, il codice ha fatto esattamente ciò che gli era stato chiesto. Il problema era l'ampiezza dello scope e l'assenza di un controllo indipendente prima dell'effetto.""",
    "Atlassian, aprile 2022": """Nell'aprile 2022 Atlassian stava dismettendo un'applicazione legacy chiamata Insight. Lo script di manutenzione era corretto: riceveva una lista di ID e cancellava gli oggetti corrispondenti. Il problema è che la lista conteneva gli ID dei siti dei clienti, non quelli dell'applicazione.

In ventitré minuti furono cancellati 883 siti, che coinvolgevano 775 clienti. Per alcuni, il ripristino richiese fino a quattordici giorni. Il codice non aveva un bug di sintassi: nessuno aveva verificato che gli ID appartenessero allo scope giusto.

Le correzioni furono di piattaforma: soft delete, rollout graduale e rollback testato. La lezione non è “scriviamo script migliori”. È che il sistema deve limitare e verificare l'effetto di uno script corretto prima che colpisca lo scope sbagliato.""",
    "Azure DevOps, maggio 2023": """Il secondo caso riguarda Microsoft: Azure DevOps è il servizio, non il nome dell'azienda. Nel maggio 2023, durante una migrazione molto ampia del SDK di Azure, un refuso trasformò il job che doveva eliminare uno snapshot di database in un job che eliminava il server SQL che lo ospitava.

Il ring interno passò senza problemi, ma non conteneva snapshot abbastanza vecchi da attivare quel job. Quando il cambiamento arrivò in South Brazil, la condizione si verificò: furono cancellati diciassette database di produzione e il disservizio durò circa dieci ore.

Il canary aveva ridotto il raggio d'azione, ma non aveva verificato l'effetto pericoloso. Tra le correzioni ci fu anche un resource lock sui server SQL di produzione. Tenetelo a mente: nella nostra demo vedremo un lock fermare una cancellazione persino fuori dalla pipeline.""",
    "Lo schema comune": """I due casi hanno lo stesso schema. La sintassi era valida; il codice era stato revisionato e testato. I test verificavano che il codice facesse ciò che diceva, ma non che ciò che diceva fosse la cosa giusta.

Chi approvava immaginava uno scope più piccolo: l'applicazione invece dei siti, il database invece del server. E tra il comando e l'effetto irreversibile non c'era un livello indipendente che potesse dire di no.

Quindi il problema non è chi scrive il cambiamento. È cosa lo lascia passare. Ora mettiamo al posto della persona un agente, capace di preparare cambiamenti molto più velocemente.""",
    "2. Ora il cambiamento lo scrive un agente": """Lo schema resta lo stesso; cambia l'attore e aumenta la velocità. Preciso subito una cosa: questa non è una sessione contro gli agenti. Li uso ogni giorno e li ho usati anche per costruire questo laboratorio.

La domanda è come dare loro un perimetro adeguato: quali credenziali possono raggiungere, quali azioni possono eseguire e quali decisioni devono restare alla piattaforma e alle persone.""",
    "Casi agentici: stesso schema": """Tre casi mostrano tre modi diversi in cui il perimetro di un agente può fallire.

Nel caso PocketOS, un agente che lavorava in staging trovò un token in un file non correlato. Quel token aveva permessi eccessivi e bastò una chiamata per cancellare il volume con il database di produzione e i backup. L'agente non aveva forzato alcun limite: aveva usato una credenziale che poteva raggiungere. Le credenziali accessibili definiscono il suo perimetro reale.

Nel caso Replit, l'agente cancellò il database di produzione nonostante un code freeze dichiarato in chat. Un'istruzione in linguaggio naturale è una richiesta, non un controllo tecnico.

Nel caso Amazon Q, un token GitHub troppo ampio permise di inserire codice malevolo nella build dell'estensione. La release non fece danni solo perché il codice conteneva un errore di sintassi. Siamo stati fortunati, non protetti.

Non sono storie contro gli agenti: sono storie di piattaforme senza confini sufficienti.""",
    "Copilot: cosa sa e cosa non decide": """Partiamo dalla pull request. Copilot non può approvare la propria PR. Ma questo, da solo, non ferma un merge: se il repository non richiede una review, la PR può essere unita senza approvazione.

In VS Code c'è un controllo diverso: l'agent mode può chiedermi conferma prima di eseguire un comando, ma posso anche attivare l'auto-approvazione. Inoltre l'agente usa il mio terminale: se lì sono già autenticato ad Azure, i suoi comandi possono usare le mie credenziali. Nella demo ho isolato la configurazione Azure come precauzione, ma non è un confine d'identità.

Copilot può conoscere l'effetto di una modifica. Per esempio, può leggere che rinominare uno Storage richiede un replace, o consultare le regole del repository. Ma sapere cosa succederà non significa avere il permesso di decidere se farlo.

Nel laboratorio ci sono due approvazioni distinte. Per applicare una modifica ai file di un team, il rollout si ferma sull'Environment GitHub del team e approva una persona diversa da chi l'ha avviato. Se invece una PR modifica i controlli della piattaforma, come gate o workflow, deve approvarla un Code Owner prima del merge.""",
    "Azure MCP Server: contesto, non giudizio": """MCP aiuta la governance o la complica? La risposta è: può fare entrambe le cose. MCP è un protocollo con cui un modello usa strumenti esterni. Azure MCP Server porta contesto sullo stato di Azure e conoscenza utile, ma la decisione resta al modello e le credenziali restano quelle con cui il server viene avviato.

Nella configurazione locale, quindi, attenzione al vostro accesso ad Azure. Per il cloud agent si può configurare una managed identity dedicata e con privilegi limitati. Alcuni strumenti sono in sola lettura, ma ogni scrittura effettuata direttamente tramite un tool può saltare il percorso di plan, gate e approvazione.

La regola pratica è fissare la versione, abilitare la modalità read-only quando basta e caricare solo i namespace necessari. MCP può migliorare la proposta e dare contesto; non sostituisce il gate.""",
    "3. La piattaforma decide, non chi scrive": """Da qui in avanti vedrete codice vero, in un repository pubblico, collegato a un laboratorio che gira davvero su Azure. Le run sono consultabili e il QR per il repository è alla fine.

Prima di guardare la demo, chiarisco come sono costruiti i confini del laboratorio e quali identità agiscono in ogni fase.""",
    "Tenant simulati, confini reali": """Questo laboratorio usa una sola subscription e una sola directory Entra. I “tenant” sono resource group che rappresentano due team, Sales e Operations. È un modello utile per ragionare su una piattaforma interna multi-team, ma non va confuso con l'isolamento tra directory Entra separate.

Ogni team ha il proprio resource group, il proprio state, la propria identità di apply e il proprio Environment GitHub. Se l'identità di Sales prova a modificare Operations, Azure la ferma con RBAC. Se un file di team cambia il resource group, il gate lo confronta con una mappa che vive nel codice della piattaforma e lo rifiuta.

C'è anche una semplificazione dichiarata: l'identità di plan può scrivere lo state di entrambi i team. In produzione la separerei per tenant. Anche i nomi dei resource group sono vincolati per non coinvolgere carichi reali presenti nella subscription.""",
    "Il flusso di un ring": """Seguiamo il flusso da sinistra a destra, chiedendoci ogni volta chi sta agendo. La pull request esegue la CI senza credenziali Azure. Il plan produce un piano Terraform salvato e un Bicep What-If sullo stesso resource group.

Due gate leggono le anteprime. Devono passare entrambi: se uno rileva un delete, un replace o una modifica fuori tenant, la pipeline si ferma prima di raggiungere l'Environment. Non c'è quindi un'approvazione da concedere per un piano che è già stato rifiutato.

Se il piano passa, una persona diversa da chi ha avviato il rollout approva l'Environment. L'apply usa l'identità limitata al tenant e verifica che il piano approvato sia quello prodotto da questa run e da questo commit. Alla fine un controllo verifica lo stato atteso.

Il gate è codice semplice e leggibile, non un'intelligenza artificiale: è intenzionale, perché la regola che decide dovrebbe essere più semplice del sistema che controlla.""",
    "Cinque livelli, ognuno presuppone che il precedente fallisca": """La difesa ha cinque livelli. I primi due sono in GitHub: il gate sul piano e l'approvazione umana. Il terzo è l'identità di apply, limitata al resource group del proprio team. Gli ultimi due sono in Azure: una policy che blocca l'azione e un resource lock.

Questi ultimi livelli funzionano anche se qualcuno passa dal portale o usa direttamente la riga di comando, fuori dalla pipeline. Per questo il resource lock richiamato nel caso Azure DevOps ricompare nella demo.

Ogni livello può avere un buco: un errore nel gate, una persona distratta, una regola di policy configurata male. L'obiettivo è che per produrre l'effetto indesiderato debbano fallire più livelli indipendenti.""",
    "Una rinomina, due rischi": """Questa è la slide tecnica che spiega la demo. In Azure il nome di uno Storage account non si cambia sul posto. Terraform pianifica un replace: elimina la risorsa vecchia e ne crea una nuova. Se la vecchia contiene dati, il rischio è perderli. Eppure la validazione della sintassi può essere verde.

Bicep in modalità incrementale si comporta diversamente: crea il nuovo Storage e lascia quello vecchio in Azure, anche se non è più nel template. A prima vista sembra più prudente, ma il vecchio Storage resta orfano e conserva i dati senza essere più gestito dal codice.

La stessa riga modificata produce quindi due rischi diversi: perdita dei dati o risorsa orfana. Per questo il gate confronta entrambe le anteprime. La regola specifica del laboratorio sfrutta il fatto che ogni team ha un solo Storage; non è una regola universale.""",
    "4. Demo": """Ora passiamo alla demo. È live; se un passaggio non risponde entro un minuto, userò la registrazione e proseguiremo senza perdere il filo.

Il revisore è collegato da un secondo dispositivo. Chi avvia il rollout non può approvarlo: questa separazione è parte della dimostrazione, non un dettaglio organizzativo. Mentre guardiamo i passaggi, teniamo d'occhio chi agisce e quali controlli intervengono.""",
    "Cosa guardare durante la demo": """Cominciamo chiedendo a Copilot di rinominare lo Storage di Sales. La pull request può risultare verde perché la validazione controlla la forma del codice, non l'effetto della modifica. Se Copilot segnala il replace, bene: le istruzioni del repository lo aiutano a riconoscerlo. Ma proseguiamo lo stesso, così vediamo che la protezione non dipende dal fatto che l'agente obbedisca.

Quando avviamo il rollout, guardiamo il piano Terraform: compare il replace. Poi guardiamo Bicep: il nuovo Storage verrebbe creato e quello vecchio resterebbe fuori dal template. I due gate rispondono DENY. Non nasce un deploy approvabile, quindi il revisore non riceve una richiesta.

Copilot corregge la modifica usando il nome originale e cambiando solo un tag. Questa volta le anteprime passano. Io non posso approvare il rollout; lo fa il revisore. L'apply cambia il tag senza aggiungere o distruggere risorse e il controllo finale conferma lo stato atteso. In produzione si potrebbe poi passare al ring Operations con la sua approvazione.

Infine, fuori dalla pipeline, provo a cancellare lo Storage direttamente da Azure come Owner. La policy o il lock rifiuta la richiesta. Questa protezione non dipende dal fatto che GitHub o il gate siano stati consultati.""",
    "5. Rollback, limiti, takeaway": """Chiudiamo con come ripristinare il laboratorio e con ciò che questa dimostrazione non prova. Tornare indietro non significa cancellare e ricreare: significa applicare una configurazione nota attraverso gli stessi controlli.""",
    "Rollback = roll-forward": """Dopo una demo, la tentazione può essere cancellare tutto e ripartire. Qui il reset è un roll-forward: confronta i file dei team con una baseline versionata, apre una pull request di ripristino, passa dalla CI e dallo stesso rollout approvato.

Il reset è idempotente: se i file sono già allineati non serve una pull request e l'apply viene saltato. Ma ripristina la configurazione, non i dati. Se un replace avesse cancellato i blob, il roll-forward non li riporterebbe indietro: servono backup e procedure di ripristino provate.

Il teardown finale è una procedura break-glass deliberata, con passaggi approvati e tracciati.""",
    "Limiti dichiarati": """Prima che me lo chiediate, ecco i limiti principali. Il più importante riguarda i ruoli ereditati: un Contributor a livello di subscription può agire anche nei resource group dei team. La policy e il lock restano, ma la separazione tra i team non è più garantita. Per questo bisogna controllare i ruoli assegnati agli scope superiori.

Il canary qui è un team, non una percentuale di traffico. La policy protegge l'azione di delete sugli Storage con il tag previsto, non i blob al loro interno; il laboratorio protegge il control plane, non i dati.

Infine, chi amministra il repository può cambiare le protezioni di GitHub. Policy e lock sono in Azure proprio per aggiungere controlli che non dipendono solo dalla configurazione del repository.""",
    "Protezioni spesso spente": """Il laboratorio protegge il control plane, non i dati. Quindi, prima di tornare in ufficio, ecco cosa controllare. Non c'è niente di esotico: sono impostazioni che esistono già, ma spesso sono spente di default, oppure qualcuno può spegnerle.

In Terraform, prevent_destroy sulle risorse che custodiscono dati e sullo state, e un gate che legga il piano. E attenzione al provider azurerm: di default, un destroy purga il Key Vault anche dal soft delete.

In Azure, soft delete e versioning sui blob, purge protection sul Key Vault, soft delete del server SQL, backup immutabili. E poi lock e policy, che valgono anche fuori dalla pipeline.

Non dovete ricordarla adesso: la trovate nel deck, sul repository.""",
    "Da portare a casa": """Tre idee da portare a casa. La prima: si decide sul piano, non sulla sintassi. Una validazione verde non ci dice quale sarà l'effetto.

La seconda: il raggio d'azione di un agente, come quello di una persona, dipende dall'architettura delle identità, non da una frase nel prompt.

La terza: serve una rete di sicurezza fuori dalla pipeline, perché prima o poi qualcuno la pipeline la aggirerà. Se ricordate una sola frase, ricordate questa: Copilot accelera. La piattaforma decide.""",
    "Grazie! Codice, demo e fonti": """Grazie. Lascio il QR sullo schermo per le domande e per chi vuole esplorare o ripetere la demo: nel repository trovate il codice, le fonti e il runbook.

Una domanda che spesso arriva è se il gate possa essere modificato dall'agente. I file della piattaforma richiedono la review di un code owner; i file dei team sono invece quelli su cui l'agente può lavorare. E anche se qualcuno cambiasse le regole di GitHub, le identità, le policy e i lock in Azure resterebbero controlli separati.

Grazie, e sono felice di rispondere alle vostre domande.""",
}


def mmss(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def new(layout, title=None, notes="", hidden=False, mins=None, name=None):
    """mins: slide duration. If omitted, it is derived from a leading [m:ss–m:ss] (or [m:ss] = 0) in the notes.
    The stamp is then recomputed from the running clock, so adding or cutting slides keeps the timing consistent."""
    notes = notes.strip()
    m = TIME_RE.match(notes)
    body = notes[m.end():].strip() if m else notes
    if m and not hidden:
        if mins is None:
            start = int(m[1]) * 60 + int(m[2])
            mins = ((int(m[3]) * 60 + int(m[4])) - start) / 60 if m[3] else 0
    note_name = name or title or {"1_Diapositiva titolo": "Titolo", "Vuota": "Hook"}.get(layout, layout)
    if note_name in RECITATIONS:
        notes = f"DA RECITARE\n{RECITATIONS[note_name]}"
        if body:
            notes += f"\n\nSPUNTI FACOLTATIVI\n{body}"
    else:
        notes = body
    if mins is not None and not hidden:
        start = CLOCK[0]
        CLOCK[0] += round(mins * 60)
        notes = (f"[{mmss(start)}] " if not mins else f"[{mmss(start)}–{mmss(CLOCK[0])}] ") + notes
    s = prs.slides.add_slide(LAYOUT[layout])
    if title is not None and s.shapes.title is not None:
        s.shapes.title.text = title
    s.notes_slide.notes_text_frame.text = notes
    NOTES.append((note_name, notes))
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


def table(s, rows, widths, x=0.5, y=1.7, row_h=0.45, size=15, head_size=16, first_col_bold=True):
    """rows[0] is the header. Rows grow with their text when rendered."""
    tbl = s.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)),
                             Inches(row_h * len(rows))).table
    for c, w in enumerate(widths):
        tbl.columns[c].width = Inches(w)
    for r_, row in enumerate(rows):
        tbl.rows[r_].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = tbl.cell(r_, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RED if r_ == 0 else (LIGHT if r_ % 2 else WHITE)
            tf = cell.text_frame
            tf.clear()
            tf.word_wrap = True
            run = tf.paragraphs[0].add_run()
            run.text = val
            run.font.size = Pt(head_size if r_ == 0 else size)
            run.font.bold = r_ == 0 or (c == 0 and first_col_bold)
            run.font.color.rgb = WHITE if r_ == 0 else INK
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tbl


def columns(s, cols, y=1.65, h=3.75, size=15, gap=0.2, x0=0.45, width=12.4):
    """cols: list of (header, color, [bullets]). Header band + light body, same height for all columns."""
    w = (width - gap * (len(cols) - 1)) / len(cols)
    for i, (head, color, items) in enumerate(cols):
        x = x0 + i * (w + gap)
        box(s, x, y, w, 0.6, head, fill=color, size=17, bold=True)
        body = box(s, x, y + 0.6, w, h - 0.6, ["• " + t for t in items], fill=LIGHT, fg=INK, size=size,
                   align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
        body.text_frame.margin_left = body.text_frame.margin_right = Inches(0.15)
        body.text_frame.margin_top = Inches(0.12)
        for p in body.text_frame.paragraphs:
            p.space_after = Pt(6)


def section(n, title, sub, notes):
    s = new("Intestazione sezione", f"{n}. {title}", notes)
    fill_text(ph(s, 1).text_frame, [sub])
    return s


# ---------------------------------------------------------------- 1. Title
s = new("1_Diapositiva titolo", None, """
[0:00–0:30]
- Fai una breve pausa dopo ciascuna domanda.
- Se nessuno risponde, vai avanti senza commentare la sala.
- Il gate blocca la rinomina: quello è il risultato atteso della demo.
""")
s.shapes.title.text_frame.clear()
tp = s.shapes.title.text_frame.paragraphs[0]
r = tp.add_run(); r.text = "Copilot sotto controllo"
tp2 = s.shapes.title.text_frame.add_paragraph()
r2 = tp2.add_run(); r2.text = "Platform Engineering multi-tenant su Azure con Terraform, Bicep e policy gates"
r2.font.size = Pt(22); r2.font.bold = False
fill_text(ph(s, 1).text_frame, ["Carlo Sacchi", "Lead DevOps | Metyis"])

# ---------------------------------------------------------------- Chi sono
s = new("Solo titolo", "Chi sono", """
Quarantacinque secondi, non di più: il pubblico è qui per la demo.
- Se c'è spazio per una frase sola, quella che lega il mio lavoro al tema: da dove nasce la domanda di questa sessione.
- Azure Italia Podcast: un invito a chi ascolta in italiano, senza pubblicità lunga.
- La pizza mezza italiana e mezza olandese di solito strappa un sorriso: lo lascio e vado avanti.
""", mins=0.5)
photo = ROOT / "docs/CarloSacchiBio.png"
if photo.exists():
    pic = s.shapes.add_picture(str(photo), Inches(0.8), Inches(1.9), Inches(3.4), Inches(3.4))
    pic.auto_shape_type = MSO_SHAPE.OVAL
else:
    print("WARN: docs/CarloSacchiBio.png non trovato, nella slide 'Chi sono' uso le iniziali")
    box(s, 0.8, 1.9, 3.4, 3.4, "CS", fill=NAVY, size=72, bold=True, shape=MSO_SHAPE.OVAL)
label(s, 4.8, 1.8, 8.0, 0.8, "Carlo Sacchi", size=36, bold=True)
label(s, 4.8, 2.6, 8.0, 0.5, "Lead DevOps · Metyis", size=22, color=RED)
facts = [("Microsoft MVP", "Azure - Infrastructure as Code", ROOT / "docs/mvp2627.webp"),
         ("Azure Italia Podcast", "il podcast in italiano su Microsoft Azure · azureitalia.cloud",
          ROOT / "docs/2024 AZURE ITALIA SQUARE NUOVO WHITE 1200.png"),
         ("Italiano, vivo ad Amsterdam", "carlosacchi.cloud", ASSETS / "pizza-it-nl.png")]
LOGO = 1.05
for i, (h, b, logo) in enumerate(facts):
    y = 3.15 + i * (LOGO + 0.05)
    if logo.exists():
        if logo.suffix.lower() == ".webp":  # python-pptx does not embed WebP: convert once into out/
            png = OUT.parent / (logo.stem + ".png")
            png.parent.mkdir(parents=True, exist_ok=True)
            Image.open(logo).save(png)
            logo = png
        s.shapes.add_picture(str(logo), Inches(4.8), Inches(y), Inches(LOGO), Inches(LOGO))
    else:
        print(f"WARN: {logo.relative_to(ROOT)} non trovato, nella slide 'Chi sono' uso il numero")
        number(s, 4.8 + (LOGO - 0.55) / 2, y + (LOGO - 0.55) / 2, i + 1, d=0.55)
    label(s, 6.1, y + 0.12, 6.8, 0.45, h, size=20, bold=True)
    label(s, 6.1, y + 0.53, 6.8, 0.35, b, size=14, color=GREY)
label(s, 0.8, 6.55, 12.0, 0.35, "linkedin.com/in/carlo-sacchi · github.com/carlosacchi", size=14, color=GREY)

# ---------------------------------------------------------------- 2. Hook
s = new("Vuota", None, """
[1:00–2:00] Lascio l'immagine parlare per due secondi, poi:
- «Oggi chiedere a un agente di scrivere Terraform costa meno che chiedere un caffè. Il codice arriva in pochi secondi, ed è anche scritto bene. Il problema non è la qualità del codice.»
- «Non parliamo di prompt migliori. Parliamo di chi ha la chiave del cancello.»
- Anticipo l'obiezione: non è sfiducia verso Copilot. Sono le stesse regole che chiediamo alle persone da anni: review, piano, approvazione. L'agente entra in uno schema che esiste già, o che dovrebbe esistere.
""")
picture(s, "cover.jpg", 0, 0, w=13.333)
label(s, 0.6, 2.2, 5.6, 2.6, [("L'agente scrive in secondi.", {"size": 36, "bold": True, "color": WHITE}),
                             ("Chi decide cosa arriva in Azure?", {"size": 30, "color": ORANGE})], color=WHITE)

# ---------------------------------------------------------------- 3. Agenda
s = new("Agenda", "Agenda", """
[2:00–2:30] Trenta secondi. Faccio notare una sola cosa: la demo sta al centro e prende un terzo del tempo.
- Ci arriviamo con due incidenti veri; dopo la demo parliamo di come si torna indietro e di cosa il lab NON dimostra.
- Annunciare subito che c'è una slide di limiti dichiarati crea fiducia: chi è scettico si rilassa.
""")
fill_text(ph(s, 1).text_frame, [
    "Il caso: lo scope sbagliato, eseguito correttamente",
    "Quando a scrivere è un agente",
    "Una piattaforma che decide al posto di chi scrive",
    "Demo live: Copilot, PR, gate, approvazione, canary",
    "Rollback come roll-forward, limiti, takeaway",
], size=24)

# ---------------------------------------------------------------- Glossary (short, on stage)
# (term, general definition, meaning in this session) — kept in alphabetical order
WORDS = sorted([
    ("Canary / ring", "Rilascio graduale: il cambiamento va prima a un gruppo ristretto e si allarga solo se resta sano.",
     "Ring 0 è Sales, ring 1 è Operations: Operations parte solo se Sales è sano."),
    ("DenyAction e lock", "Protezioni dentro Azure: una Azure Policy che rifiuta un'azione e un blocco contro la cancellazione.",
     "Rifiutano il delete degli Storage anche a chi passa fuori dalla pipeline."),
    ("Environment GitHub", "In GitHub Actions, una destinazione di deploy con regole proprie: revisori, branch ammessi, variabili.",
     "Il rollout si ferma finché un revisore, diverso da chi l'ha lanciato, non approva."),
    ("Gate", "Controllo automatico in pipeline che fa proseguire o blocca un rilascio in base a regole esplicite.",
     "Legge terraform plan e Bicep What-If e risponde PASS o DENY."),
    ("IaC", "Infrastructure as Code: infrastruttura descritta in file versionati e applicata da strumenti, non a mano.",
     "Terraform per i deploy, Bicep solo per l'anteprima What-If."),
    ("Managed Identity (MI)", "Identità Azure senza password, gestita da Entra ID, con cui un servizio o una pipeline accede alle risorse.",
     "Una per il plan; una di apply per ogni tenant, limitata al suo resource group."),
    ("MCP", "Model Context Protocol: protocollo aperto con cui un agente AI usa strumenti e dati esterni.",
     "Azure MCP Server dà a Copilot accesso ad Azure, con le credenziali di chi lo avvia."),
    ("OIDC", "OpenID Connect: standard per dimostrare un'identità con token firmati e a scadenza.",
     "GitHub Actions ottiene un token Azure senza secret salvati (federazione delle identità)."),
    ("Plan / What-If", "L'anteprima di un cambiamento: cosa verrà creato, modificato o cancellato, prima di farlo.",
     "terraform plan e ARM What-If sullo stesso resource group, letti dai gate."),
    ("Platform Engineering", "Disciplina che costruisce piattaforme interne self-service, con le regole già incluse, per chi sviluppa.",
     "La piattaforma decide cosa arriva in Azure, non chi scrive il codice."),
    ("Replace  -/+", "Un cambiamento che non si applica sul posto: la risorsa viene cancellata e ricreata.",
     "Rinominare lo Storage di Sales: con dei dati dentro, vuol dire perderli."),
    ("Tenant", "Un cliente o un gruppo isolato che condivide la stessa piattaforma. In Azure è anche la directory Entra ID.",
     "Un team (Sales, Operations) con il suo resource group, state, identità ed environment."),
], key=lambda w: w[0].lower())
WORD_NOTES = [
    """Le parole, prima metà. Non le leggo: sono qui perché in sala ci sono profili diversi, e chi fa sviluppo applicativo non deve perdersi al minuto 15. Il deck completo ha un glossario più lungo in fondo.
- Canary: il nome viene dal canarino nelle miniere, che segnalava il gas prima che arrivasse ai minatori. Qui il canarino è un intero team.
- Su Environment GitHub mi fermo un secondo: è la parte meno conosciuta di GitHub Actions ed è il cuore dell'approvazione umana nella demo.
- MI: da qui in avanti uso la sigla. Managed Identity vuol dire niente password da ruotare e niente secret nel repository.""",
    """Seconda metà. Due parole hanno un significato diverso da quello che vi aspettate, e le dico ad alta voce.
- Tenant: per chi lavora su Azure "tenant" è la directory Entra ID. Qui no: è un team. È una scelta di linguaggio da piattaforma interna, e la dichiaro subito per non sembrare di barare più avanti.
- Replace: è la parola chiave della demo. Su una VM è fastidioso, su uno Storage con dei dati è una perdita di dati.
- Plan e What-If sono la stessa idea in due mondi: Terraform confronta codice, state e Azure; ARM confronta il template con quello che esiste in Azure. Due motori diversi, e lo sfrutteremo.""",
]
for n, half in enumerate((WORDS[:6], WORDS[6:])):
    s = new("Solo titolo", f"Le parole di questa sessione ({n + 1}/2)", WORD_NOTES[n], mins=0.5)
    for i, (term, general, here) in enumerate(half):
        r_, c = divmod(i, 2)
        x, y = 0.45 + c * 6.3, 1.6 + r_ * 1.62
        b = box(s, x, y, 6.1, 1.5, [(term, {"size": 17, "bold": True, "color": RED}),
                                    (general, {"size": 14}),
                                    ("**Qui:** " + here, {"size": 14, "color": GREY})],
                fill=LIGHT, fg=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
        b.text_frame.margin_left = b.text_frame.margin_right = Inches(0.15)

# ---------------------------------------------------------------- Act 1
section(1, "Lo scope sbagliato, eseguito correttamente", "Due post-mortem pubblici, nessun agente coinvolto", """
[2:30] «Prima di parlare di AI, due incidenti in cui l'AI non c'entra niente.» Il problema esisteva già: l'agente lo accelera, non lo inventa.
""")

s = new("Due colonne", "Atlassian, aprile 2022", """
[2:30–4:45] Atlassian, raccontato come una storia e non come un elenco.
- Aprile 2022: un team deve dismettere un'app legacy, Insight. Lo script di manutenzione è corretto e fa esattamente il suo lavoro: cancella in modo permanente gli oggetti di cui riceve gli ID.
- Il problema è l'input. Invece degli ID dell'app riceve gli ID dei siti dei clienti. Tutto il resto funziona perfettamente.
- Il dettaglio che colpisce: la cancellazione avviene tra le 07:38 e le 08:01 UTC. Ventitré minuti per cancellare 883 siti; per alcuni clienti, fino a 14 giorni per tornare online.
- Il PIR non dice «lo script aveva un bug». Dice che nessuno ha verificato se quegli ID fossero dell'app o del sito. Mancava un controllo sullo scope, non sulla sintassi.
- Le azioni correttive sono tutte di piattaforma: soft delete ovunque, staged rollout, rollback testato. Nessuna è «scrivere script migliori».
- L'immagine: si voleva colpire il quadratino bianco, la cornice rossa ha preso l'isolato.
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
[4:45–7:00] Azure DevOps è il servizio Microsoft. Il rollout graduale c'era già, ma il ring interno non conteneva il caso critico.
- Una PR molto grande: migrazione dei pacchetti da Microsoft.Azure.Management a Azure.ResourceManager. Il tipo di PR che si approva con fiducia, perché «è solo una migrazione di SDK».
- Dentro c'è un refuso: il job che doveva cancellare un database snapshot adesso cancella l'Azure SQL Server che lo ospita.
- Ring 0, interno: non c'erano snapshot abbastanza vecchi da far scattare il job. Il canary è passato verde senza mai incontrare la condizione pericolosa.
- Ring 1, South Brazil: la condizione c'è. Diciassette database di produzione, circa dieci ore di disservizio.
- Lo dico ad alta voce: il canary riduce il raggio d'azione, non verifica l'effetto. Se il ring 0 non contiene il caso critico, non ti protegge.
- Tra le correzioni di Microsoft c'è il resource lock sui server SQL di produzione. Tenetelo a mente: nella demo il lock c'è, e un delete lanciato a mano lo fermerà Azure stesso, fuori dalla pipeline.
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
[7:00–8:15] Qui tiro le fila, lentamente: è la tesi dell'intera sessione.
- In entrambi i casi nessuno ha sbagliato la sintassi. Lo script di Atlassian e la PR di Azure DevOps erano codice valido, revisionato, testato. I test verificano che il codice faccia quello che dice, non che quello che dice sia giusto.
- Chi approvava percepiva uno scope più piccolo di quello reale: l'app invece del sito, il database invece del server.
- E tra il comando e l'effetto irreversibile non c'era nessun livello indipendente in grado di dire no.
- Frase da dire guardando la sala: il problema non è chi scrive il cambiamento. È cosa lo lascia passare.
- Ponte: adesso al posto della persona mettete un agente, che scrive dieci volte più velocemente e non si stanca mai di aprire PR.
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
[9:00] Stesso schema, attore diverso. Una frase per rassicurare: non è una sessione contro gli agenti. Li uso ogni giorno, e li ho usati anche per costruire questo laboratorio.
""")

s = new("Solo titolo", "Casi agentici: stesso schema", """
[9:00–10:45] Tre casi in un minuto e quarantacinque, tre modi in cui si rompe il perimetro di un agente: le credenziali che trova, le istruzioni che ignora, il codice con cui è costruito.
- PocketOS, aprile 2026. L'agente lavora in staging e trova un token in un file che non c'entrava niente. Il token aveva più permessi del previsto: con una sola chiamata API spariscono il volume con il database di produzione e i backup. L'agente non ha forzato niente: ha usato quello che trovava. Le credenziali raggiungibili sono il suo perimetro reale.
- Replit, luglio 2025. Il fondatore di SaaStr aveva dichiarato un code freeze, in chat. L'agente ha cancellato comunque il database di produzione. Un'istruzione in linguaggio naturale non è un controllo: è una richiesta.
- Amazon Q, luglio 2025. Qui l'agente è la vittima: un token GitHub con permessi troppo ampi, nella configurazione di build, ha permesso di inserire codice malevolo nell'estensione per VS Code, finito in automatico nella release 1.84.0. Non ha fatto danni solo perché conteneva un errore di sintassi. Lo dico così: siamo stati fortunati, non protetti.
- Chiusura: nessuna di queste è una storia contro gli agenti. Sono storie di piattaforme senza confini.
""")
rows = [("Caso", "Cosa è successo", "Lezione"),
        ("PocketOS\naprile 2026", "Un agente in staging usa un token trovato in un file non correlato: una chiamata API cancella database e backup",
         "Le credenziali raggiungibili sono il perimetro reale dell'agente"),
        ("Replit\nluglio 2025", "Durante un code freeze dichiarato, l'agente cancella il database di produzione",
         "Un'istruzione in linguaggio naturale non è un controllo"),
        ("Amazon Q\nluglio 2025", "Un token GitHub con permessi eccessivi fa entrare codice malevolo nella release; non parte solo per un errore di sintassi (AWS-2025-015)",
         "La supply chain dell'agente è superficie d'attacco")]
table(s, rows, (2.2, 6.0, 4.1), row_h=1.1)
source(s, "The Register, 27/04/2026 · AWS Security Bulletin AWS-2025-015 · dettagli in docs/case-study.md")

s = new("Solo titolo", "Copilot: cosa sa e cosa non decide", """
[10:45–13:15] - La review del Code Owner serve per modificare gate e workflow; l'approvazione dell'Environment serve per applicare il workload.
- Senza una review richiesta nelle regole del repository, una PR può essere unita senza approvazione.
- L'agent mode usa il terminale dell'utente e quindi può ereditare le sue credenziali Azure.
""")
columns(s, [
    ("Protezioni già presenti", NAVY, [
        "Copilot apre una PR, ma non può approvarla",
        "GitHub può chiedere approvazione prima dei workflow della PR",
        "VS Code chiede conferma; è possibile attivare l'auto-approvazione",
        "Le istruzioni guidano l'agente, ma non sono un blocco"]),
    ("Cosa può sapere oggi", TEAL, [
        "Update o replace: dalla doc del provider o leggendo un plan",
        "Lo stato reale: risorse, policy, ruoli, con Azure MCP Server",
        "Le regole della piattaforma, se legge il gate nel repo",
        "Per vedere Azure servono credenziali: di chi?"]),
    ("Cosa non deve decidere", RED, [
        "Se il cambio arriva in produzione",
        "Con quali credenziali agire",
        "Chi approva: senza review richiesta, la PR può essere unita",
        "Se cambiare le protezioni che lo bloccano"]),
])
box(s, 0.45, 5.65, 12.4, 0.75, "Sapere non è decidere.  Istruzioni = guida · Gate = controllo.",
    fill=LIGHT, fg=RED, size=20, bold=True)

# ---------------------------------------------------------------- MCP
s = new("Solo titolo", "Azure MCP Server: contesto, non giudizio", """
È la domanda che mi sono fatto preparando la sessione: MCP aiuta o complica la governance? La risposta onesta è: tutte e due.
- MCP è un protocollo: il server espone strumenti, l'intelligenza resta nel modello. Ma «è solo un connettore» è riduttivo. Porta contesto, cioè lo stato reale di Azure, e conoscenza già confezionata: documentazione del provider, regole IaC. È per questo che la slide precedente è cambiata.
- Cosa mi ha sorpreso leggendo la documentazione: le mani sono poche. I tool di Policy e RBAC sono in sola lettura. Sullo Storage crea account e carica blob, ma non c'è un tool per cancellarlo. E il comando az lo genera soltanto: a eseguirlo è il terminale, con le credenziali del terminale. Il rischio vero resta lì.
- Le credenziali: in locale usa quelle di chi lo avvia, tipicamente il vostro az login. Per il cloud agent di Copilot la configurazione ufficiale, azd coding-agent config, crea una managed identity dedicata con ruolo Reader di default. È lo stesso principio del lab: un'identità per ogni ruolo, e all'agente la più piccola.
- Cosa complica: ogni scrittura fatta via MCP salta plan, gate e approvazione. E il server cambia in fretta: la 3.0 è di ottobre 2026 e l'esempio ufficiale usa @azure/mcp@latest. Dopo Amazon Q, «latest» su uno strumento con accesso ad Azure dovrebbe far alzare un sopracciglio.
- Consiglio pratico: versione fissata, --read-only, solo i namespace che servono.
- Chiusura: MCP migliora la proposta. Non sostituisce il gate.
""", mins=1.75)
flow = [("Copilot", "il modello sceglie quale tool chiamare", NAVY),
        ("VS Code", "client MCP: mostra la chiamata e chiede conferma", VIOLET),
        ("Azure MCP Server", "traduce in chiamate Azure", TEAL),
        ("Azure + RBAC", "con le credenziali di chi lo avvia", RED)]
for i, (h, b, c) in enumerate(flow):
    x = 0.45 + i * 3.12
    box(s, x, 1.6, 3.0, 0.7, h, fill=c, size=17, bold=True, shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)
    label(s, x + 0.1, 2.35, 2.8, 0.7, b, size=13, color=GREY, align=PP_ALIGN.CENTER)
columns(s, [
    ("Cosa porta", TEAL, [
        "Stato reale: risorse, policy assegnate, ruoli",
        "Conoscenza curata: doc del provider, regole IaC",
        "Terraform: conftest sulla policy library AVM",
        "Read-only e filtro per namespace o singolo tool"]),
    ("Cosa non risolve", RED, [
        "Usa le credenziali di chi lo avvia: az login o MI",
        "Policy e RBAC solo in lettura; crea Storage e carica blob",
        "Il comando az lo genera: lo esegue il tuo terminale",
        "I tool cambiano tra versioni: fissare la versione"]),
], y=3.0, h=2.5, size=15)
box(s, 0.45, 5.7, 12.4, 0.7, "Porta contesto, non giudizio. Quello che scrive in Azure non passa da plan, gate e approvazione.",
    fill=LIGHT, fg=RED, size=17, bold=True)
source(s, "learn.microsoft.com/azure/developer/azure-mcp-server · Azure MCP Server 3.0, ottobre 2026")

# ---------------------------------------------------------------- Act 3
section(3, "La piattaforma decide, non chi scrive", "Il laboratorio: github.com/carlosacchi/wpc-2026", """
[14:00] Da qui in avanti è tutto codice vero: repository pubblico, gira davvero su Azure, e ogni run che vedrete ha un numero che potete cercare. Il QR è nell'ultima slide.
""")

s = new("Solo titolo", "Tenant simulati, confini reali", """
[14:00–16:30] Il lab. Lo dico subito, prima che me lo chieda qualcuno: una sola subscription, una sola directory Entra, e i tenant sono resource group. È il caso di una piattaforma interna con più team, o di un solo team che separa chi scrive, chi approva e chi gestisce.
- Ogni tenant ha quattro cose sue: resource group con lo Storage, container di state, identità di apply, environment GitHub. Se l'identità di apply di Sales prova a toccare Operations, Azure risponde 403: non è una regola del gate, è RBAC.
- Il resource group sta anche nel file del team, quindi l'agente può cambiarlo. Ma il gate confronta il piano con la sua mappa tenant → resource group e risponde DENY: la mappa vive nel codice della piattaforma, non in quello del team.
- Un'onestà in più: l'identità di plan è una sola e oltre alla lettura può scrivere lo state di entrambi i tenant, perché il plan prende il lock sullo state. È una semplificazione del lab: in produzione la separerei per tenant.
- I nomi dei resource group sono vincolati a wpc-* e mai wpc-2026: nella subscription ci sono anche carichi reali, e bootstrap, workload e gate rifiutano tutto il resto.
""")
box(s, 0.45, 1.6, 12.4, 4.85, fill=None, line=GREY)
label(s, 0.75, 1.68, 6, 0.4, "Subscription · una directory Entra", size=13, color=GREY)
cards = [("wpc-2026 · piattaforma", VIOLET, ["Storage di state (lock)", "Container tfstate-<tenant>", "MI plan: lettura, what-if, state",
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
box(s, 0.75, 5.55, 12.0, 0.7, "La mappa tenant → resource group sta nel gate della piattaforma, non nei file dei team",
    fill=WHITE, fg=RED, size=16, bold=True, line=RED)

s = new("Solo titolo", "Il flusso di un ring", """
[16:30–19:00] Il flusso di un ring. Invito a seguire i colori: ogni colore è un'identità diversa, e la domanda giusta in ogni momento è «chi sta agendo adesso?».
- La CI sulla PR gira senza credenziali Azure, ed è voluto: una PR, anche scritta da un agente, non deve poter toccare Azure.
- Il plan produce due anteprime, terraform plan salvato e Bicep What-If sullo stesso resource group. Perché due? Perché sbagliano in modo diverso: lo vediamo tra poco con la rinomina.
- I gate devono rispondere PASS tutti e due. Se uno solo dice DENY non nasce l'artefatto, e senza artefatto l'environment non viene raggiunto: il revisore non riceve nemmeno la notifica. Non si può approvare per sbaglio qualcosa che non esiste.
- L'apply verifica che il piano sia quello generato in questa run, da questo commit, con lo stesso sha256: non si può approvare un piano e applicarne un altro.
- Un'osservazione che mi piace fare: il gate non è un'AI. Sono meno di 200 righe di JavaScript, leggibili in dieci minuti. È una scelta: un controllo che decide deve essere più semplice di ciò che controlla.
""")
flow = [("PR", "CI validate\nsenza credenziali", GREY), ("Plan", "terraform plan\n+ Bicep what-if", VIOLET),
        ("Gate ×2", "DENY: delete, replace,\nfuori tenant, rinomina", RED), ("Approva", "environment del tenant\nno self-review", ORANGE),
        ("Apply", "MI del tenant\nstesso piano, sha256", TEAL), ("Verify", "privato, lock,\npolicy, no drift", GREEN)]
for i, (h, b, c) in enumerate(flow):
    x = 0.45 + i * 2.1
    box(s, x, 1.9, 1.9, 0.75, h, fill=c, size=17, bold=True, shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)
    label(s, x, 2.75, 1.9, 1.1, b.split("\n"), size=13, align=PP_ALIGN.CENTER)
lanes = [("Chi agisce", INK, ["Copilot + persona", "MI plan", "MI plan", "Revisore umano", "MI apply sales", "MI plan"])]
for i, who in enumerate(lanes[0][2]):
    box(s, 0.55 + i * 2.1, 4.05, 1.7, 0.55, who, fill=LIGHT, fg=INK, size=12)
label(s, 0.45, 4.7, 12.5, 0.4, "Ring 0 sano → Ring 1 (operations), con gli stessi passi e le sue identità", size=16, color=RED, bold=True)
code(s, 0.45, 5.2, 12.4, 1.25, [
    ("gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only", CODE_FG),
    ("PASS: workload plan satisfies the selected lab rules.", CODE_GREEN),
    ("HEALTHY: wpc26salesb0b966 in wpc-2026-sales is private, locked, protected by denyAction and drift-free.", CODE_GREEN),
], size=12)

s = new("Vuota", "Cinque livelli, ognuno presuppone che il precedente fallisca", """
[19:00–21:00] La difesa a livelli. Ogni livello presuppone che il precedente possa fallire, anche quando a sbagliare è una persona che modifica il codice.
- 1 e 2 vivono in GitHub: gate e approvazione. Il 3 è l'identità: anche con tutto il resto aggirato, l'apply di Sales non può toccare Operations. 4 e 5 vivono in Azure: policy e lock funzionano anche se qualcuno passa dal portale o da az, completamente fuori dalla pipeline. È la stessa correzione scelta da Azure DevOps.
- Per chi conosce Terraform: prevent_destroy l'ho messo sullo state e sui resource group dei tenant, non sullo Storage dei workload. Lì Terraform rifiuterebbe il piano prima ancora del gate, e nella demo non vedreste il gate lavorare.
- Se qualcuno chiede perché così tanti livelli: perché ognuno ha un buco. Il gate è codice nello stesso repository, protetto solo dalla review del suo code owner; l'approvazione dipende da una persona attenta; la policy da come è scritta. Perché passi un errore, i buchi devono allinearsi tutti.
""")
picture(s, "defense-layers.jpg", 0, 0, w=13.333)
label(s, 8.85, 0.45, 4.3, 1.4, "Cinque livelli, ognuno presuppone che il precedente fallisca", size=24, color=WHITE, bold=True)
layers = [("Gate in CI", "plan + what-if: niente delete, replace, fuori tenant"),
          ("Approvazione umana", "environment del tenant, no self-review"),
          ("Identità per tenant", "apply limitato al proprio RG e al proprio state"),
          ("Azure Policy DenyAction", "nessun delete degli Storage del lab"),
          ("Resource lock", "CanNotDelete sui RG dei tenant e sullo state")]
for i, (h, b) in enumerate(layers):
    y = 2.0 + i * 0.95
    number(s, 8.85, y, i + 1, d=0.6, fill=[TEAL, BLUE, VIOLET, RED, RED][i])
    label(s, 9.55, y - 0.08, 3.7, 0.45, h, size=19, color=WHITE, bold=True)
    label(s, 9.55, y + 0.32, 3.7, 0.6, b, size=13, color=CODE_FG)

s = new("Solo titolo", "Una rinomina, due rischi", """
[21:00–23:00] La slide tecnica più importante: chi capisce questa, capisce la demo.
- Terraform: il nome di uno Storage account in Azure non si può cambiare. Terraform lo sa e pianifica un replace: -/+, cancella il vecchio e crea il nuovo. Con dei dati dentro, vuol dire perderli. E terraform validate è verde: la sintassi è perfetta.
- Bicep, ed è la parte che sorprende anche chi usa Azure da anni: in modalità incrementale ARM non cancella mai niente. Crea il nuovo Storage e lascia l'originale fuori dal template. Sembra la versione sicura, ma adesso ci sono due Storage, i dati stanno in quello che nessun codice gestisce più, e prima o poi qualcuno lo cancellerà credendolo orfano.
- Stessa riga cambiata, due rischi diversi: perdita di dati da una parte, risorsa orfana dall'altra. Per questo il gate legge entrambe le anteprime.
- Limite da dichiarare: la regola «Create più Storage ignorato uguale rinomina» funziona nel lab, dove ogni tenant ha un solo Storage. Non è una regola generale.
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
[23:00] Due cose prima di iniziare. La demo è live: se un passo non risponde entro un minuto passo alla registrazione, senza drammi. E chi lancia il rollout non può approvarlo: per questo c'è un secondo account, il revisore, su un altro dispositivo.
Runbook: docs/session/demo-runbook.md.
""")

s = new("Solo titolo", "Cosa guardare durante la demo", """
[23:00–38:00] Questa slide resta sullo schermo durante le attese della CI, che non sono poche: ogni job impiega qualche minuto.
- Tempi indicativi: passi 1, 2 e 3 tre minuti ciascuno, passo 4 quattro minuti, passo 5 uno. Un minuto di margine.
- Durante le attese commento chi sta agendo: nella PR nessuna credenziale, nel plan l'identità di plan, nell'apply quella di Sales, nel delete finale io come Owner.
- Passo 1: se Copilot segnala da solo che la rinomina forza un replace, è merito delle istruzioni del repo. Lo dico e confermo comunque la modifica: la demo mostra che il controllo regge anche quando chi propone insiste, persona o agente.
- Passo 2: indico la riga «forces replacement» e le due righe DENY. Poi faccio notare che il revisore non ha ricevuto nessuna richiesta: non c'è niente da approvare.
- Passo 4: mostro che io non posso approvare, poi approva il revisore. L'apply cambia un tag: 0 added, 1 changed, 0 destroyed. Il ring 1 lo racconto a parole: in sala lancio solo il canary, con rings=all partirebbe Operations con la sua approvazione.
- Passo 5: delete dello Storage dal terminale fuori da VS Code, come Owner della subscription. Risposta attesa: RequestDisallowedByPolicy; se risponde prima il lock, ScopeLocked. In entrambi i casi non si cancella niente, e non c'è nessuna pipeline di mezzo.
- Se avanza tempo: nella prova generale del 10 novembre lo script di reset si è fermato a metà per un bug, corretto il giorno dopo. Un buon esempio del perché si prova tutto, anche il rollback.
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
[38:00] Ultima parte, la più onesta: come si rifà tutto domani mattina, e cosa questo lab non dimostra.
""")

s = new("Solo titolo", "Rollback = roll-forward", """
[38:00–39:15] Il rollback. Dopo una demo andata male la tentazione è «cancello e ricreo». Qui il rollback non cancella niente.
- La baseline è versionata in demo/baseline. npm run demo:reset confronta i file dei team con la baseline, apre una PR di ripristino, aspetta la CI, la unisce e lancia il rollout su tutti i ring, con gli stessi gate e la stessa approvazione. Anche tornare indietro è un cambiamento, e passa dallo stesso cancello.
- È idempotente: se tutto è già allineato non apre nemmeno la PR e l'apply viene saltato. È così che preparo il lab prima di ogni sessione.
- Precisazione importante: il reset riporta configurazione e tag, non dati. Se il replace fosse passato, nessun roll-forward riporterebbe indietro i blob. Per i dati servono soft delete, backup e ripristini provati, e il lab non li dimostra.
- Il teardown dopo l'evento è break-glass: disattivo la DenyAction, tolgo il lock, cancello. Tre passi deliberati, approvati e tracciati.
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
[39:15–40:15] Questi limiti li dico io, prima che li trovi qualcuno in sala.
- Il più importante sono i ruoli ereditati. Chi è Contributor sulla subscription attraversa tutti i tenant, perché RBAC eredita verso il basso. Policy e lock restano, ma la separazione tra team no. Mi è successo: nel mio lab il revisore era Contributor sulla subscription, e l'ho tolto preparando questa sessione. Controllate i vostri.
- Il canary qui è per team: non c'è traffico da spostare, quindi niente split al 5%.
- La DenyAction protegge gli Storage che hanno il tag del progetto: chi può cambiare quel tag li fa uscire dalla policy. Il lock resta.
- Il lab protegge il control plane, non i dati: bloccare la cancellazione dello Storage non impedisce di cancellare i blob dentro.
- Chi amministra il repository può cambiare branch protection ed environment. Per questo policy e lock stanno in Azure: chi controlla GitHub non li controlla automaticamente.
""")
fill_text(ph(s, 1).text_frame, [
    "**Una directory, una subscription:** isolamento per RG, identità, state e policy. Ruoli ereditati sulla subscription lo attraversano",
    "**Canary per tenant**, non uno split di traffico",
    "**What-if è un preview:** con ProviderNoRbac non verifica i permessi di scrittura",
    "**DenyAction copre solo il delete** degli Storage del progetto: il replace lo ferma il gate",
    "**I gate sono regole didattiche esplicite**, non uno scanner di sicurezza completo",
    "**Chi amministra il repo** può riconfigurare branch protection ed environment",
], size=20)

s = new("Solo titolo", "Protezioni spesso spente", """
[40:15–41:15] La slide da fotografare. Non la leggo riga per riga: scelgo due o tre righe in base alla sala.
- prevent_destroy accetta solo valori letterali: non si può accendere con una variabile solo in prod. Se il modulo è condiviso tra gli ambienti, di fatto è acceso ovunque.
- prevent_destroy non è un controllo di sicurezza: se qualcuno, persona o agente, cancella il blocco resource o il lifecycle, Terraform distrugge senza avvisare. Per questo serve anche la review dei moduli (qui: CODEOWNERS) e, fuori da Terraform, lock e policy. Per togliere una risorsa dal codice senza distruggerla c'è il blocco removed con lifecycle { destroy = false }.
- Nel lab prevent_destroy è sullo state e sui RG dei tenant, non sullo Storage: lì Terraform fermerebbe il piano prima del gate e nella demo non vedreste il gate.
- Provider azurerm: purge_soft_delete_on_destroy è true di default per Key Vault, App Configuration, API Management e Cognitive Services. Un terraform destroy li cancella anche dal soft delete. prevent_deletion_if_contains_resources sui resource group è true di default: non spegnetelo per comodità.
- Storage: se cancellate un account, il recupero dal portale è possibile entro 14 giorni, se nessuno ha ricreato lo stesso nome, ed è best effort. Microsoft stessa raccomanda il lock. Il soft delete dei blob non aiuta se sparisce l'account intero.
- Azure SQL: il soft delete del server logico è in preview, da 1 a 7 giorni; per i server con meno di due anni è spento di default. È esattamente lo scenario di Azure DevOps.
- Azure Backup: con MUA le operazioni critiche, come spegnere il soft delete o ridurre la retention, richiedono l'autorizzazione di un'altra persona tramite Resource Guard.
- Bicep: con un deployment stack in denyDelete e detachAll, togliere una risorsa dal template non la cancella e nessuno la cancella a mano.
- Domanda probabile: «prevent_destroy su tutti gli ambienti o solo in prod?» Su tutti gli ambienti stabili, sulle risorse che custodiscono dati, chiavi o state: stesso comportamento ovunque, e la procedura per superarlo si impara in dev, non in prod durante un incidente. Non su tutto: su risorse senza dati blocca replace legittimi e insegna a toglierlo per riflesso. Negli ambienti effimeri, per esempio uno per PR, il teardown passa da una procedura esplicita.
""")
table(s, [("Dove", "Attivare o verificare", "Perché: default e trappole"),
          ("Terraform", "prevent_destroy su state, dati, chiavi, database",
           "Se il blocco sparisce dal codice, sparisce la protezione"),
          ("Terraform", "Gate sul plan (niente -/+ o delete); apply del plan salvato",
           "validate verde = sintassi giusta, non effetto giusto"),
          ("azurerm", "key_vault { purge_soft_delete_on_destroy = false }",
           "Default true: destroy purga il Key Vault dal soft delete"),
          ("State", "Backend con versioning, soft delete, lock, solo Entra ID",
           "Senza state, Terraform non sa cosa gestisce"),
          ("Bicep", "What-If; deployment stack con denyDelete e detachAll",
           "Complete cancella ciò che non è nel template"),
          ("Storage", "Soft delete blob e container, versioning, point-in-time",
           "Default solo dal portale: in Terraform va dichiarato"),
          ("Key Vault", "Purge protection",
           "Facoltativa, ma una volta attiva è irreversibile"),
          ("Azure SQL", "Soft delete del server logico (preview), backup LTR",
           "Spento sui server < 2 anni: delete del server definitivo"),
          ("Azure Backup", "Soft delete always-on, immutabilità, MUA (Resource Guard)",
           "Attivo di default, ma si spegne finché non è always-on"),
          ("Azure", "Lock CanNotDelete, Policy DenyAction, PIM",
           "Valgono anche fuori dalla pipeline")],
      (1.65, 5.6, 5.15), x=0.45, y=1.5, row_h=0.42, size=13, head_size=14)
source(s, "Fonti: Microsoft Learn (Storage, Key Vault, Azure SQL, Azure Backup, deployment stacks), "
          "HashiCorp lifecycle, azurerm features block. Verificate a novembre 2026.")

s = new("Solo titolo", "Da portare a casa", """
[41:00–42:15] Tre frasi, lente. Se il pubblico se ne ricorda una sola, va bene lo stesso.
- La prima è per chi scrive pipeline: si decide sul piano, non sulla sintassi. Un validate verde non dice niente sull'effetto.
- La seconda è per chi disegna piattaforme: il raggio d'azione di un agente, o di una persona, è un'architettura di identità, non un'istruzione in un prompt.
- La terza è per chi la notte vuole dormire: una rete di sicurezza dentro Azure, fuori dalla pipeline, perché prima o poi qualcuno la pipeline la aggira.
- Pausa, poi la chiusura: «Copilot accelera. La piattaforma decide.»
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
[42:15–43:30] Lascio il QR sullo schermo per il Q&A: è il modo più semplice per chi vuole rifare la demo.
Domande probabili, con una risposta breve:
- «E se l'agente modifica il gate?» Il gate sta nello stesso repository, ma i file della piattaforma (gate, workflow, test, bootstrap, moduli) hanno in CODEOWNERS un proprietario diverso da me: una PR che li tocca resta ferma finché non approva lui, chiunque l'abbia scritta, io o Copilot. I file dei team invece non hanno proprietario, ed è lì che lavora l'agente. E se qualcuno riconfigura GitHub, identità, policy e lock non dipendono dal repository.
- «Perché non basta Azure Policy?» Perché la policy valuta la singola richiesta, non il piano: non sa che quel delete fa parte di un replace.
- «Funziona con Azure DevOps?» Il principio sì: environment con approvazioni e controlli, service connection con workload identity federation, lo stesso gate in uno step.
- «Quanto costa il lab?» Quasi niente: due Storage praticamente vuoti più lo state. Identità e policy non costano.
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

# ---------------------------------------------------------------- Appendix: full glossary (not timed)
GLOSSARY = sorted([
    ("Platform Engineering", "Team e pratiche che costruiscono una piattaforma interna: i team applicativi arrivano in produzione con regole già incluse."),
    ("IaC (Infrastructure as Code)", "Infrastruttura descritta in file versionati e applicata da strumenti, non da clic nel portale."),
    ("Terraform state", "Il file in cui Terraform registra cosa ha creato. Chi può scriverlo può alterare ciò che Terraform crede esista."),
    ("terraform plan / apply", "plan calcola le differenze tra codice e Azure; apply le esegue. Nel lab l'apply usa solo il piano salvato e approvato."),
    ("Replace (-/+)", "Il cambio non si può fare sul posto: la risorsa viene cancellata e ricreata. Per uno Storage vuol dire perdere i dati."),
    ("prevent_destroy", "Regola Terraform che fa fallire ogni piano che distrugge quella risorsa. Nel lab protegge lo state e i RG dei tenant."),
    ("Bicep", "Linguaggio Microsoft per i template ARM. Nel lab serve solo per il What-If e non viene mai applicato."),
    ("ARM What-If", "Anteprima di Azure Resource Manager: cosa un template creerebbe, modificherebbe o ignorerebbe."),
    ("Modalità incrementale", "Deploy ARM/Bicep in cui le risorse assenti dal template restano dove sono: non vengono cancellate."),
    ("Gate (policy gate)", "Codice in pipeline che legge plan e What-If e risponde PASS o DENY prima di qualsiasi apply."),
    ("Policy as code", "Regole di governance scritte come codice: versionate, revisionate e testate come il resto."),
    ("Azure Policy: Deny", "Effetto che rifiuta la creazione o la modifica di risorse non conformi, per esempio uno Storage pubblico."),
    ("Azure Policy: DenyAction", "Effetto che rifiuta un'azione su risorse esistenti. Nel lab: il delete degli Storage."),
    ("Resource lock (CanNotDelete)", "Blocco in Azure: la risorsa si può modificare ma non cancellare finché il lock non viene rimosso."),
    ("RBAC e minimo privilegio", "Ruoli Azure assegnati su uno scope; ogni identità riceve solo i permessi che le servono."),
    ("Managed Identity (MI)", "Identità Azure senza password, gestita dalla piattaforma. Nel lab: una per il plan, una di apply per ogni tenant."),
    ("OIDC / federazione", "GitHub Actions riceve un token Azure a tempo, legato a repository, branch o environment. Nessun secret salvato."),
    ("Environment GitHub", "Destinazione di deploy con regole: revisori obbligatori, niente self-review, solo dal branch main."),
    ("Branch protection / CODEOWNERS", "Regole per unire una PR: check obbligatori, numero di approvazioni, proprietari dei percorsi."),
    ("Tenant (in questo lab)", "Un team con il suo resource group, state, identità di apply ed environment. Non un tenant Entra ID."),
    ("Canary / ring", "Rilascio a ondate: prima un tenant (ring 0), poi gli altri solo se il primo è sano."),
    ("Drift", "Differenza tra ciò che dice il codice e ciò che esiste in Azure, per esempio dopo una modifica dal portale."),
    ("Blast radius", "Il raggio d'azione: quanto danno può fare un errore o una credenziale compromessa."),
    ("Control plane / data plane", "Gestire le risorse (creare o cancellare uno Storage) contro i dati al loro interno (i blob)."),
    ("Roll-forward", "Tornare a uno stato buono con un nuovo deploy della configurazione nota, invece di \"annullare\"."),
    ("Break-glass", "Procedura d'emergenza deliberata e tracciata per superare una protezione, per esempio il teardown del lab."),
    ("Agent mode / cloud agent", "Copilot in VS Code esegue passi e comandi con conferma; il cloud agent lavora su GitHub e apre PR."),
    ("MCP (Model Context Protocol)", "Protocollo con cui un agente usa strumenti esterni. Azure MCP Server espone strumenti per Azure."),
], key=lambda g: g[0].lower())
PER_PAGE = 7
pages = [GLOSSARY[i:i + PER_PAGE] for i in range(0, len(GLOSSARY), PER_PAGE)]
for n, page in enumerate(pages, 1):
    s = new("Solo titolo", f"Glossario ({n}/{len(pages)})", """
APPENDICE, non si presenta: è per chi scarica il deck.
""")
    table(s, [("Termine", "Significato")] + page, (3.3, 9.1), y=1.55, row_h=0.55, size=14, head_size=15)

TALK_END = CLOCK[0]

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
delta = TALK_END - TALK_SECONDS
print(f"TIME: {mmss(TALK_END)} di {mmss(TALK_SECONDS)}"
      + (f" -> oltre di {mmss(delta)}: tagliare prima di salire sul palco" if delta > 0 else " -> ok"))
