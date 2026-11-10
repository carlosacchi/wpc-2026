# Changelog

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
