# Runbook della demo (circa 15 minuti)

Demo live con Copilot Chat in agent mode in VS Code, con fallback registrati. Regola: se un passo non risponde entro 60 secondi, si passa al backup (link qui sotto o slide nascoste del deck) e si prosegue.

## Ruoli

| Chi | Dove | Cosa fa |
|---|---|---|
| Relatore (carlosacchi) | VS Code, **terminale A** senza credenziali Azure | Copilot, branch, PR, merge, avvio rollout |
| Relatore | **Terminale B**, fuori da VS Code, `az login` come operatore | Solo il passo 5 (delete negato) |
| Revisore (azureitaliadevops) | Secondo dispositivo, browser già autenticato su GitHub | Approva l'environment `sales` (e `operations`) |

Chi lancia il rollout non può approvarlo: è voluto ed è parte della demo.

## Preflight (T-60 minuti)

```sh
npm run demo:status                         # atteso: "FILES: team files match demo/baseline.", nessuna PR o run aperta
git switch main && git pull --ff-only
gh run list --workflow rollout.yml --limit 3   # l'ultima run baseline deve essere success
```

- Verificare in Azure che esistano `wpc26salesb0b966` (wpc-2026-sales) e `wpc26opsb0b966` (wpc-2026-operations); l'ultima run baseline li controlla entrambi (HEALTHY).
- Se non è tutto pulito: `npm run demo:reset` e far approvare gli eventuali ring. Il reset richiede un working tree pulito: file non tracciati (per esempio un template fuori da `.gitignore`) lo bloccano.
- **Credenziali dell'agente.** Il terminale integrato di VS Code non deve avere accesso ad Azure, altrimenti l'agente agisce con i permessi Owner del relatore (lo schema del caso PocketOS). Nel terminale A:

  ```sh
  export AZURE_CONFIG_DIR="$(mktemp -d)"   # oppure impostarlo in terminal.integrated.env.linux prima di aprire VS Code
  az account show                            # atteso: "Please run 'az login'"
  ```

- In VS Code: disattivare l'auto-approvazione dei comandi del terminale per l'agent mode, così ogni comando chiede conferma.
- Revisore collegato su https://github.com/carlosacchi/wpc-2026/actions, notifiche attive.
- Aprire nel browser le run di backup (sotto) in schede separate.

## Passi

### 1. Copilot rinomina lo Storage di Sales (~3 min)

```sh
git switch -c demo/rename-sales
```

In Copilot Chat (agent mode) il prompt del passo 1 di [prompts.md](prompts.md). Poi:

```sh
git commit -am "Rename Sales storage account (requested by Sales)"
git push -u origin demo/rename-sales
gh pr create --fill --base main
gh pr checks --watch                 # validate verde: è il punto
gh pr merge --squash --delete-branch
```

Messaggio: la CI senza credenziali è verde, la review del diff vede una lettera in più.

### 2. Rollout: due DENY (~3 min)

```sh
gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only
gh run watch "$(gh run list --workflow rollout.yml --limit 1 --json databaseId -q '.[0].databaseId')"
```

Nel job **Plan + gates (sales)** mostrare `-/+ … forces replacement` e le due righe `DENY:`. L'apply non parte e l'environment non viene raggiunto: il revisore non riceve nulla da approvare.

Fallback: `gh workflow run rollout.yml -f scenario=rename-demo -f rings=canary-only` (stesso risultato senza modificare `main`) oppure la run registrata.

### 3. Copilot corregge (~3 min)

```sh
git switch main && git pull --ff-only && git switch -c demo/fix-sales
```

Prompt del passo 3 di [prompts.md](prompts.md), incollando le righe DENY. Poi commit, PR, `gh pr checks --watch`, merge come al passo 1.

### 4. Approvazione e canary (~4 min)

```sh
gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only
```

- Plan: `~ tags` in-place, entrambi i gate `PASS`.
- Il job di apply resta in **Waiting**. Mostrare che il relatore non può approvare; il revisore approva dal secondo dispositivo.
- Apply con la MI di Sales: verifica di commit e sha256 del piano, `1 changed`, poi `HEALTHY`.
- A parole: con `rings=all` partirebbe Operations, con la propria approvazione.

### 5. Rete di sicurezza (~1 min), dal terminale B

```sh
az storage account delete -g wpc-2026-sales -n wpc26salesb0b966 --yes
```

Atteso: `RequestDisallowedByPolicy` (DenyAction), oppure `ScopeLocked` dal lock: in entrambi i casi nulla viene cancellato, anche se a lanciare il comando è l'Owner della subscription.

## Dopo la sessione

```sh
npm run demo:reset   # PR di ripristino → CI → merge → rollout rings=all
```

Il revisore approva i ring che riportano il tag `serviceLabel` alla baseline; poi `npm run demo:status` deve tornare pulito. Chiudere il terminale A e rimuovere la `AZURE_CONFIG_DIR` temporanea.

## Run di backup

Prova generale completa eseguita il 10/11/2026 (passi 1–4 e reset; il passo 5 era stato verificato in precedenza).

| Passo | Run |
|---|---|
| Canary baseline approvato (apply + HEALTHY) | https://github.com/carlosacchi/wpc-2026/actions/runs/42823102175 |
| Baseline rings=all (Sales senza modifiche) | https://github.com/carlosacchi/wpc-2026/actions/runs/42917201757 |
| Rinomina → doppio DENY (prova generale) | https://github.com/carlosacchi/wpc-2026/actions/runs/42919010193 |
| Correzione → approvazione → `0 added, 1 changed` → HEALTHY | https://github.com/carlosacchi/wpc-2026/actions/runs/42919302894 |
| Reset dopo la prova (`demo:reset`, rings=all) | https://github.com/carlosacchi/wpc-2026/actions/runs/42920906060 |
