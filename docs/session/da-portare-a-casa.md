# Copilot sotto controllo: cosa portare a casa

Materiale della sessione WPC 2026 *"Copilot sotto controllo: Platform Engineering multi-tenant su Azure con Terraform, Bicep e policy gates"*.

Qui trovi i messaggi della sessione, una lista di controlli da fare sul tuo ambiente, cosa attivare subito e cosa dopo, e gli snippet da copiare e adattare. Il laboratorio completo, funzionante su Azure, è in questo repository: https://github.com/carlosacchi/wpc-2026

## Indice

1. [I messaggi della sessione](#1-i-messaggi-della-sessione)
2. [Dieci controlli da fare sul tuo ambiente](#2-dieci-controlli-da-fare-sul-tuo-ambiente)
3. [Easy win: da attivare subito](#3-easy-win-da-attivare-subito)
4. [Dopo: per una sicurezza maggiore](#4-dopo-per-una-sicurezza-maggiore)
5. [Snippet da copiare e adattare](#5-snippet-da-copiare-e-adattare)

---

## 1. I messaggi della sessione

1. **Si decide sul piano, non sulla sintassi.** `terraform validate` e `bicep build` verdi non dicono niente sull'effetto. L'effetto si vede in `terraform plan` e nel What-If, e lì va messo un controllo automatico che sa dire no.
2. **Il raggio d'azione è un'architettura, non un'istruzione.** Quello che un agente (o una persona) può rompere dipende dalle credenziali che raggiunge, non da cosa c'è scritto nel prompt.
3. **Una rete di sicurezza dentro Azure, fuori dalla pipeline.** Lock e Azure Policy valgono anche per chi passa dal portale o dalla riga di comando. Prima o poi qualcuno la pipeline la aggira.
4. **Sapere non è decidere.** Copilot oggi può sapere che un cambio è un *replace*: lo legge nella documentazione del provider o in un plan. Questo non gli dà il diritto di farlo. La decisione resta alla piattaforma e a una persona.
5. **MCP porta contesto, non giudizio.** Azure MCP Server dà all'agente lo stato reale di Azure, con le credenziali di chi lo avvia. Usalo in sola lettura, con una versione fissata e un'identità dedicata.
6. **Tornare indietro vuol dire andare avanti.** Il rollback della configurazione è un nuovo rilascio della versione buona, con gli stessi controlli. Per i dati invece servono soft delete, backup e ripristini provati: nessun roll-forward riporta indietro un blob cancellato.

## 2. Dieci controlli da fare sul tuo ambiente

Ogni controllo è una domanda. Se la risposta è quella "da sistemare", trovi il rimedio nella sezione 3 o 4. I comandi usano Azure CLI (`az`) e GitHub CLI (`gh`); sostituisci i valori tra `< >`.

| # | Domanda | Risposta sana | Come verificarlo |
|---|---|---|---|
| 1 | L'agente, nel suo terminale, è già collegato ad Azure? | No | Nel terminale integrato di VS Code: `az account show`. Se risponde con una subscription, l'agente ha i tuoi permessi |
| 2 | I comandi proposti dall'agente partono senza la tua conferma? | No | VS Code → Impostazioni → cerca *auto approve*: l'approvazione automatica dei comandi deve essere spenta |
| 3 | Una PR verso `main` può essere unita senza che nessuno la approvi? | No | `gh api repos/<owner>/<repo>/branches/main/protection --jq '.required_pull_request_reviews'`: serve almeno un'approvazione, oppure la review dei code owner sui file critici |
| 4 | Il deploy in produzione aspetta l'ok di una persona diversa da chi l'ha lanciato? | Sì | `gh api repos/<owner>/<repo>/environments --jq '.environments[] \| {name, rules: .protection_rules}'`: revisori obbligatori e *prevent self-review* |
| 5 | Prima dell'apply qualcosa legge il piano e blocca cancellazioni e sostituzioni? | Sì | Cerca nella pipeline un passo dopo `terraform plan` che fallisce se il piano contiene `delete` (snippet 5.1) |
| 6 | La pipeline usa password o segreti per entrare in Azure? | No, usa OIDC | Cerca `client-secret`, `ARM_CLIENT_SECRET` o `AZURE_CREDENTIALS` nei workflow: se ci sono, stai usando un segreto |
| 7 | La stessa identità fa plan e apply, su tutti gli ambienti? | No | `az role assignment list --assignee <client-id> --all -o table`: un'identità con Contributor su tutta la subscription è un raggio d'azione enorme |
| 8 | Chi ha Owner o Contributor sull'intera subscription? | Solo chi deve | `az role assignment list --scope /subscriptions/<id> --query "[].{chi:principalName, ruolo:roleDefinitionName}" -o table`: i ruoli ereditati dall'alto attraversano ogni confine tra team |
| 9 | Le risorse che non devono sparire hanno un lock? | Sì | `az lock list -g <resource-group> -o table` |
| 10 | Se qualcuno cancella dei blob, si possono recuperare? | Sì | `az storage account blob-service-properties show -n <storage> -g <rg> --query "{blob: deleteRetentionPolicy, container: containerDeleteRetentionPolicy}"`: il soft delete deve essere `enabled: true` |

## 3. Easy win: da attivare subito

Si fanno in poche ore, senza cambiare architettura, e chiudono i buchi più comuni.

| Cosa | Perché | Tempo | Snippet |
|---|---|---|---|
| **Terminale dell'agente senza `az login`** e conferma obbligatoria dei comandi | L'agente non agisce con i tuoi permessi per sbaglio | 10 minuti | 5.9 |
| **Istruzioni di repository per Copilot** | L'agente segnala i replace e non tocca gate e pipeline. È una guida, non un controllo | 15 minuti | 5.10 |
| **Approvazione su `main`** (almeno una review, o review dei code owner sui file della piattaforma) | Una PR, anche scritta da un agente, non entra da sola | 15 minuti | 5.5 |
| **Environment di produzione con revisore e *prevent self-review*** | Chi lancia il deploy non può approvarlo | 15 minuti | 5.4 |
| **Resource lock `CanNotDelete`** sui resource group critici | Un delete, da qualunque parte arrivi, viene rifiutato | 10 minuti | 5.6 |
| **Soft delete** per blob e container | Un errore sui dati diventa recuperabile | 10 minuti | 5.12 |
| **Gate minimo sul piano Terraform** | La pipeline si ferma se il piano cancella o sostituisce qualcosa | 1 ora | 5.1 |
| **Revisione di Owner e Contributor sulla subscription** | Toglie i permessi ereditati che scavalcano tutto il resto | 1 ora | controllo 8 |

## 4. Dopo: per una sicurezza maggiore

Richiedono più lavoro e qualche decisione di architettura. L'ordine è quello consigliato.

1. **Identità senza segreti (OIDC)** per GitHub Actions o Azure DevOps, con **identità separate per plan e apply** e una di apply per ogni ambiente o team, ciascuna limitata al suo resource group (snippet 5.3).
2. **Il piano approvato è il piano applicato.** Salva il plan come artefatto, applica esattamente quel file e verifica che venga dalla stessa run e dallo stesso commit (snippet 5.3; versione completa nel lab: `scripts/plan-artifact.mjs`).
3. **Azure Policy `DenyAction`** sul delete delle risorse critiche, con *cascade* sul resource group (snippet 5.7).
4. **Gate anche sul What-If** se usi Bicep o ARM: in modalità incrementale una rinomina non cancella, ma lascia una risorsa orfana (snippet 5.2).
5. **I file della piattaforma hanno un proprietario.** Gate, workflow e moduli con un code owner diverso da chi propone le modifiche, o in un repository separato (snippet 5.5).
6. **Rilascio a ondate (ring)** con un controllo di salute tra un'ondata e l'altra: prima un team o un ambiente, poi gli altri.
7. **Agente isolato davvero:** dev container o VM senza credenziali montate, invece di un terminale con una variabile d'ambiente diversa. Azure MCP Server in sola lettura con un'identità dedicata con ruolo Reader (snippet 5.11).
8. **Dati:** backup con ripristino provato, non solo configurato. Il soft delete protegge da un errore, non da tutto.
9. **Break-glass documentato:** chi può togliere lock e policy, con quale approvazione, e come resta traccia. Le operazioni distruttive devono essere rare e deliberate, non un pulsante in pipeline.

## 5. Snippet da copiare e adattare

Sono versioni semplificate di quello che gira nel laboratorio. Ogni snippet dice cosa adattare. In produzione fissa le GitHub Actions allo SHA del commit invece che al tag, come fa il repository del lab.

### 5.1 Gate minimo sul piano Terraform

Blocca la pipeline se il piano cancella o sostituisce una risorsa (un replace è `delete` + `create`).

```sh
#!/usr/bin/env bash
# gate.sh: uso ./gate.sh plan.json
set -euo pipefail
plan_json="${1:-plan.json}"

destructive=$(jq -r '
  .resource_changes[]?
  | select(.change.actions | any(. == "delete"))
  | "\(.address): \(.change.actions | join("/"))"' "$plan_json")

if [ -n "$destructive" ]; then
  echo "DENY: il piano cancella o sostituisce risorse:"
  echo "$destructive"
  exit 1
fi
echo "PASS: nessun delete o replace nel piano."
```

Come produrre `plan.json`:

```sh
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
./gate.sh plan.json
```

**Adatta:** se alcuni delete sono legittimi, aggiungi una lista di indirizzi permessi invece di togliere il controllo. Il lab controlla anche resource group, tag e proprietà di sicurezza: `scripts/plan-policy.mjs`.

### 5.2 Gate minimo sul What-If di Bicep / ARM

```sh
az deployment group what-if \
  --resource-group <rg> \
  --template-file main.bicep \
  --parameters @main.parameters.json \
  --no-pretty-print > whatif.json

# Fallisce se il What-If contiene cancellazioni o modifiche non valutabili
jq -e '[.changes[] | select(.changeType == "Delete" or .changeType == "Unsupported")] | length == 0' whatif.json \
  && echo "PASS" || { echo "DENY: delete o modifiche non valutabili nel What-If"; exit 1; }

# Segnale di rinomina implicita: si crea una risorsa mentre una dello stesso tipo resta fuori dal template
jq -r '.changes[] | select(.changeType == "Create" or .changeType == "Ignore") | "\(.changeType) \(.resourceId)"' whatif.json
```

**Adatta:** in modalità incrementale le risorse fuori dal template compaiono come `Ignore`, non come `Delete`. Un `Create` più un `Ignore` dello stesso tipo è spesso una rinomina: il lab lo trasforma in `DENY` (`scripts/whatif-policy.mjs`), ma la regola va calibrata sul tuo caso.

### 5.3 GitHub Actions: plan, gate, approvazione, apply dello stesso piano, senza segreti

```yaml
name: deploy
on: workflow_dispatch

permissions:
  contents: read
  id-token: write          # serve per OIDC

env:
  ARM_USE_OIDC: "true"
  ARM_TENANT_ID: ${{ vars.AZURE_TENANT_ID }}
  ARM_SUBSCRIPTION_ID: ${{ vars.AZURE_SUBSCRIPTION_ID }}

jobs:
  plan:
    runs-on: ubuntu-latest
    env:
      ARM_CLIENT_ID: ${{ vars.AZURE_PLAN_CLIENT_ID }}     # identità di sola lettura
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform plan -out=tfplan
      - run: terraform show -json tfplan > plan.json
      - run: ./gate.sh plan.json                          # snippet 5.1
      - uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: tfplan

  apply:
    needs: plan
    runs-on: ubuntu-latest
    environment: production        # revisore obbligatorio + prevent self-review (snippet 5.4)
    env:
      ARM_CLIENT_ID: ${{ vars.AZURE_APPLY_CLIENT_ID }}    # identità di apply, limitata al suo resource group
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - uses: actions/download-artifact@v4
        with:
          name: tfplan
      - run: terraform init
      - run: terraform apply tfplan                       # applica esattamente il piano approvato
```

**Adatta:** le due identità sono managed identity (o app registration) con una *federated credential* per il repository: quella di plan sul branch `main`, quella di apply sull'environment `production`. Il backend dello state va configurato con autenticazione Entra ID. La versione completa del lab, con verifica di run, commit e sha256 del piano, è in `.github/workflows/tenant-ring.yml`.

### 5.4 Environment con approvazione obbligatoria

In GitHub: *Settings → Environments → New environment* (`production`):

- **Required reviewers:** una persona o un team, attivando **Prevent self-review**;
- **Allow administrators to bypass:** disattivato;
- **Deployment branches:** solo `main`.

Verifica:

```sh
gh api repos/<owner>/<repo>/environments --jq '.environments[] | {name, admin_bypass: .can_admins_bypass, rules: [.protection_rules[] | {type, prevent_self_review, reviewers: [.reviewers[]?.reviewer.login]}]}'
```

### 5.5 Proteggere i file della piattaforma: CODEOWNERS e branch protection

`.github/CODEOWNERS`:

```text
# I file della piattaforma hanno un proprietario diverso da chi propone le modifiche
/.github/          @<org>/platform-team
/scripts/          @<org>/platform-team
/infra/modules/    @<org>/platform-team

# Le configurazioni dei team restano senza proprietario: decidono gate e approvazione del deploy
/infra/teams/
```

Attiva la review dei code owner sul branch `main`:

```sh
gh api -X PATCH repos/<owner>/<repo>/branches/main/protection/required_pull_request_reviews \
  -F require_code_owner_reviews=true -F dismiss_stale_reviews=true
```

**Adatta:** non mettere un proprietario generico `*` se poi chi apre le PR è anche l'unico proprietario: nessuno può approvare la propria PR, e resterebbero tutte bloccate. Se la branch protection non esiste ancora, creala prima da *Settings → Branches*.

### 5.6 Resource lock

```sh
az lock create \
  --name no-delete \
  --lock-type CanNotDelete \
  --resource-group <rg> \
  --notes "Cancellazioni solo con una procedura approvata"
```

Il lock vale per il gruppo e per tutto ciò che contiene, anche per un Owner: per cancellare bisogna prima toglierlo, e questo rende la cancellazione un atto deliberato.

### 5.7 Azure Policy DenyAction: nessuno cancella le risorse critiche

`rules.json`:

```json
{
  "if": {
    "allOf": [
      { "field": "type", "equals": "Microsoft.Storage/storageAccounts" },
      { "field": "tags['critical']", "equals": "true" }
    ]
  },
  "then": {
    "effect": "[parameters('effect')]",
    "details": {
      "actionNames": ["delete"],
      "cascadeBehaviors": { "resourceGroup": "deny" }
    }
  }
}
```

`params.json`:

```json
{
  "effect": {
    "type": "String",
    "allowedValues": ["DenyAction", "Disabled"],
    "defaultValue": "DenyAction"
  }
}
```

```sh
az policy definition create --name deny-delete-critical-storage --mode Indexed \
  --rules rules.json --params params.json
az policy assignment create --name deny-delete-critical-storage \
  --policy deny-delete-critical-storage \
  --scope /subscriptions/<id>/resourceGroups/<rg>
```

**Adatta:** cambia il tipo di risorsa e la condizione. Attenzione: se la protezione dipende da un tag, chi può cambiare quel tag può far uscire la risorsa dalla policy. Su resource group dedicati conviene proteggere tutte le risorse di quel tipo, senza condizione sul tag. La policy protegge il *control plane*: non impedisce di cancellare i dati dentro la risorsa.

### 5.8 Terraform `prevent_destroy`

```hcl
resource "azurerm_storage_account" "state" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}
```

Terraform rifiuta qualsiasi piano che distrugge questa risorsa. Ideale per lo state e per le risorse che non devono mai sparire. Vale solo per chi usa Terraform: lock e policy (5.6, 5.7) proteggono anche dagli altri strumenti.

### 5.9 Terminale dell'agente senza credenziali Azure (VS Code)

Nelle impostazioni utente di VS Code (`settings.json`), la riga del tuo sistema operativo:

```jsonc
"terminal.integrated.env.osx":     { "AZURE_CONFIG_DIR": "/tmp/agent-no-azure" },
"terminal.integrated.env.linux":   { "AZURE_CONFIG_DIR": "/tmp/agent-no-azure" },
"terminal.integrated.env.windows": { "AZURE_CONFIG_DIR": "C:\\Temp\\agent-no-azure" }
```

Nel terminale integrato `az account show` deve chiedere di fare `az login`. È una precauzione, non un confine: il terminale gira comunque con il tuo utente. Per un isolamento vero usa un dev container o una VM senza credenziali montate.

### 5.10 Istruzioni di repository per Copilot

`.github/copilot-instructions.md`:

```markdown
# Istruzioni per GitHub Copilot

- Non eseguire mai `terraform apply`, `terraform destroy` o comandi `az ... delete`:
  le modifiche arrivano in Azure solo tramite la pipeline.
- Modifica solo le configurazioni dei team. Non modificare gate, test o workflow
  per far passare un cambiamento.
- Quando cambi l'infrastruttura, spiega l'impatto atteso sul piano e segnala
  esplicitamente ogni sostituzione (`-/+`) o cancellazione.
- Un `terraform validate` verde non dice nulla sull'impatto in Azure.
```

Sono una guida per l'agente, non un controllo: chi decide restano gate e approvazione.

### 5.11 Azure MCP Server in sola lettura (VS Code)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "azure": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure/mcp@<versione>", "server", "start",
               "--read-only", "--namespace", "storage", "--namespace", "policy"]
    }
  }
}
```

**Adatta:**
- fissa la versione (`npm view @azure/mcp version` mostra l'ultima) invece di usare `@latest`;
- esponi solo i namespace che ti servono;
- il server usa le credenziali di chi lo avvia: se lo usa un agente, dagli un'identità dedicata con ruolo Reader, come fa la configurazione ufficiale del cloud agent di Copilot (`azd coding-agent config`).

### 5.12 Soft delete per blob e container

```sh
az storage account blob-service-properties update \
  --account-name <storage> --resource-group <rg> \
  --enable-delete-retention true --delete-retention-days 14 \
  --enable-container-delete-retention true --container-delete-retention-days 14
```

Un blob o un container cancellato per errore resta recuperabile per 14 giorni. Non sostituisce un backup con ripristino provato.

---

Domande, segnalazioni o miglioramenti: apri una issue nel repository.
