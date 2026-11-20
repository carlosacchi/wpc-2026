# Changelog

## 0.5.4

### Aggiunto
- Deck: slide "Protezioni spesso spente" (dopo "Limiti dichiarati"), con tabella delle impostazioni Terraform, Bicep e Azure da attivare o verificare contro cancellazioni e perdita di dati: `prevent_destroy`, `purge_soft_delete_on_destroy` del provider azurerm, backend dello state, deployment stack, soft delete di blob, Key Vault, Azure SQL e Azure Backup, lock e policy. Fonti Microsoft Learn e HashiCorp verificate a novembre 2026. Note con la risposta a «`prevent_destroy` su tutti gli ambienti o solo in prod?».

### Modificato
- `.gitignore`: restano esclusi solo state, tfvars, piani, artefatti generati, cache e ambienti locali. Template WPC, foto, loghi e deck generato (`docs/session/out/`) si versionano, per lavorare da più macchine.
- Deck: "Rollback = roll-forward" e "Limiti dichiarati" accorciate di 30 secondi ciascuna, il Q&A di 15, per restare a 45 minuti.

### Corretto
- `build_deck.py`: due spunti facoltativi (Azure DevOps, Copilot) riallineati a `speaker-notes.md`, modificato a mano nel commit precedente; ora la build rigenera le note senza perderli.

## 0.5.3

### Aggiunto
- `docs/session/demo-guida-a-z.md`: guida completa alla demo, con squash merge dopo i check obbligatori e output del canary senza codici colore ANSI.

## 0.5.0

### Aggiunto
- Deck: slide "Chi sono" con ruolo, Microsoft MVP e Azure Italia Podcast (foto da `docs/CarloSacchiBio.png`, loghi MVP e Azure Italia Podcast da `docs/`, stemma `assets/pizza-it-nl.png`; se un file manca usa iniziali o numeri), due slide "Le parole di questa sessione" con 12 termini in ordine alfabetico (definizione generale e significato nella sessione) e glossario completo in appendice (28 termini in ordine alfabetico, non presentato).
- Deck: slide "Azure MCP Server: contesto, non giudizio", basata sulla documentazione Microsoft Learn e sulla release 3.0 (ottobre 2026).
- `build_deck.py`: i tempi delle note sono calcolati dalla durata di ogni slide e la build stampa la durata totale rispetto ai 45 minuti.

### Modificato
- `.github/CODEOWNERS`: i file della piattaforma (gate e script, test, `package.json`, workflow, bootstrap, moduli, workload root, confronto Bicep, baseline della demo) sono di `@azureitaliadevops`; i file dei team non hanno proprietario. Rimosso il proprietario generico `* @carlosacchi`, che con la review dei code owner attiva avrebbe bloccato le PR del relatore. Ha effetto solo dopo aver attivato *Require review from Code Owners* nella branch protection di `main`.
- Deck: "Copilot: cosa copre e cosa no" diventa "Copilot: cosa sa e cosa non decide". Con la documentazione del provider e Azure MCP Server Copilot può sapere se un cambio è un replace: il punto non è cosa sa, ma cosa decide.
- `.gitignore`: esclusi gli ambienti Python locali (`.venv*/`, `venv/`) e `.DS_Store`.
- Note dello speaker riscritte in forma discorsiva: dettagli dei post-mortem, osservazioni sul lab, cosa dire durante la demo, domande probabili nel Q&A. Non ripetono più il testo delle slide.

### Corretto
- Amazon Q (deck e `docs/case-study.md`): la causa è un token GitHub con permessi eccessivi nella configurazione di build, e il codice non è stato eseguito per un errore di sintassi (AWS-2025-015). Non un contributo esterno.
- Deck, README e `docs/case-study.md`: la MI di plan non è solo Reader (scrive anche lo state); `prevent_destroy` protegge solo lo state e i RG dei tenant, non lo Storage dei workload, quindi il quinto livello del deck è il resource lock; i ruoli ereditati attraversano i tenant ma non annullano policy e lock.
- Deck: i gate rispondono `PASS` o `DENY` (non "ALLOW"); la mappa tenant → RG è nel gate, "non nei file dei team" (il nome del RG è anche nel file del team).
- Note dello speaker allineate tra loro e con slide, runbook e codice: il passo 5 può rispondere la policy o il lock; in sala si lancia solo il canary; la risposta su "e se l'agente modifica il gate?" dichiara che oggi la branch protection non richiede una review separata sui file della piattaforma.

## 0.4.1

Correzioni emerse dalla prova generale.

### Corretto
- `scripts/demo-reset.mjs`: il reset si interrompeva dopo l'apertura della PR (`Cannot read properties of null`) perché l'attesa dei check ignorava lo stdout. Emerso nella prima prova generale con drift reale.
- `docs/session/build_deck.py`: nella slide "Tenant simulati, confini reali" la didascalia della subscription non si sovrappone più al bordo del riquadro.

### Verificato
- Prova generale completa in Azure: rinomina → PR verde → doppio DENY (run 42919010193); correzione → approvazione del revisore → `0 added, 1 changed` → HEALTHY (run 42919302894); `demo:reset` → PR #9 unita; il rollout di riallineamento (run 42920906060) attende l'approvazione del revisore.

## 0.4.0

Materiali della sessione WPC 2026: deck, note dello speaker, demo e immagini.

### Aggiunto
- `docs/session/build_deck.py`: genera il deck da 45 minuti (22 slide più 2 di backup nascoste) sul template ufficiale, con diagrammi nativi, output reali dei gate e note dello speaker con i tempi; scrive anche `speaker-notes.md`.
- `docs/session/assets/`: illustrazioni generate (copertina, scope sbagliato, livelli di difesa) e screenshot reale dell'approvazione dell'environment.
- `docs/session/demo-runbook.md` e `docs/session/prompts.md`: demo live con Copilot Chat in agent mode, ruoli separati (relatore, revisore, terminale dell'operatore), terminale dell'agente senza credenziali Azure, fallback e reset.
- `.github/copilot-instructions.md`: istruzioni di repository per Copilot (mai apply/delete, spiegare l'impatto del piano), presentate come guida e non come controllo.

### Modificato
- `.gitignore`: esclusi il template WPC e il deck generato (`docs/session/out/`).

## 0.3.0

Reset ripetibile della demo e rollback governato.

### Aggiunto
- `demo/baseline/`: stato iniziale versionato dei file dei team (entrambi gli Storage esistenti con configurazione baseline).
- `scripts/demo-reset.mjs` (`npm run demo:status`, `npm run demo:reset`): rileva le differenze dalla baseline, apre una PR che ripristina i file, attende la CI, esegue il merge e lancia `rollout baseline rings=all`. Il rollback è un roll-forward: nessun delete, solo riallineamento in-place attraverso gli stessi gate e approvazioni. È idempotente e serve anche da seed su un lab vuoto.
- Test sulla baseline: stessa forma dei file dei team, RG del tenant, rilevamento delle modifiche della demo.

### Verificato
- Bootstrap applicato in Azure (6 import, 28 add, 0 destroy), ri-plan senza modifiche, lock e DenyAction attivi sui RG dei tenant.
- Environment `sales`/`operations` con revisore obbligatorio, no self-review, nessun bypass admin, solo `main`.
- Primo rollout canary: entrambi i gate PASS, l'apply attende il revisore e chi ha lanciato la run non può approvare.

## 0.2.0

Rollout governato multi-tenant: le promesse del titolo diventano pipeline reali.

### Aggiunto
- Tenant simulati con un RG ciascuno (`wpc-2026-sales`, `wpc-2026-operations`), con container di state e managed identity di apply separati e federati sull'environment GitHub del tenant.
- `rollout.yml` e `tenant-ring.yml`: ring canary (Sales, poi Operations), plan Terraform e Bicep What-If (`ProviderNoRbac`) sullo stesso scope, doppio gate, approvazione umana tramite environment, apply del piano salvato, controllo di salute e drift.
- Gate What-If (`scripts/whatif-policy.mjs`, `check-whatif.mjs`): solo Create/Modify/NoChange/Ignore, solo Storage nel RG del tenant, proprietà conformi, DENY sulla rinomina implicita in modalità incrementale.
- `plan-artifact verify`: l'artefatto deve provenire dalla stessa run, dallo stesso commit e dallo stesso target, con sha256 identico.
- Azure Policy `DenyAction` sul delete degli Storage del lab, lock `CanNotDelete` su RG dei tenant e Storage di state, `prevent_destroy` sui RG dei tenant.
- Ruolo custom per il What-If, limitato a `whatIf`/`validate`.
- `scripts/bootstrap-imports.mjs`: rigenera gli import per le risorse esistenti se lo state locale del bootstrap va perso.
- `docs/case-study.md`: Atlassian 2022, Azure DevOps 2023 e casi agentici mappati sui controlli del lab.
- Test di coerenza tra bootstrap, file dei team, gate e workflow.

### Modificato
- Il gate Terraform risolve il RG dal tenant e rifiuta il RG condiviso `wpc-2026`, i RG di altri tenant e qualsiasi nome fuori da `wpc-*`.
- Il workload richiede `resource_group_name`, con la stessa validazione.
- La variabile `plan_oidc_subject` del bootstrap è sostituita da `github_oidc_subject_prefix`. Il subject di plan deriva da `main` e quelli di apply dagli environment.

### Rimosso
- `plan.yml`, sostituito da `rollout.yml`.
- L'apply manuale dell'operatore e la variabile `operator_object_id`. Gli assegnamenti esistenti in Azure vanno rimossi a mano dopo approvazione.

## 0.1.0

- Laboratorio iniziale: bootstrap, workload Terraform Sales/Operations, confronto Bicep, gate sul piano, workflow plan-only e ispezione dei subject OIDC.
