# Demo "Copilot sotto controllo": guida dalla A alla Z

Questa guida serve a chiunque debba eseguire la demo, anche senza conoscere il progetto. Contiene tutti i comandi, nell'ordine in cui vanno lanciati, e per ognuno dice cosa deve succedere e cosa fare se succede altro.

La demo dura circa 15 minuti. La preparazione la prima volta richiede un'ora; nei giorni successivi bastano 10 minuti di controlli.

La demo si ripete tutte le volte che serve, sempre sullo stesso lab (stessa subscription, stessi resource group). Il ciclo è sempre questo: la pipeline di rollout crea e aggiorna le risorse, la demo cambia un'etichetta, il ripristino (sezione 9) la riporta indietro passando dalla stessa pipeline. Niente viene cancellato e non serve nessun super user. La sezione 11 dice cosa controllare prima di una nuova presentazione; la sezione 12 spiega come smantellare il lab quando non servirà più.

## Indice

1. [Cosa mostra la demo](#1-cosa-mostra-la-demo)
2. [Le parole che incontrerai](#2-le-parole-che-incontrerai)
3. [Chi serve: tre ruoli](#3-chi-serve-tre-ruoli)
4. [Cosa installare](#4-cosa-installare)
5. [Preparazione, una volta sola](#5-preparazione-una-volta-sola)
6. [Il giorno della demo: controlli prima di iniziare](#6-il-giorno-della-demo-controlli-prima-di-iniziare)
7. [La demo, passo per passo](#7-la-demo-passo-per-passo)
8. [Se qualcosa va storto](#8-se-qualcosa-va-storto)
9. [Dopo la demo: rimettere tutto a posto](#9-dopo-la-demo-rimettere-tutto-a-posto)
10. [Cosa non fare mai](#10-cosa-non-fare-mai)
11. [Rifare la demo un'altra volta (stesso lab)](#11-rifare-la-demo-unaltra-volta-stesso-lab)
12. [Smantellare il lab: a mano, non con una pipeline](#12-smantellare-il-lab-a-mano-non-con-una-pipeline)
13. [Riferimenti](#13-riferimenti)

---

## 1. Cosa mostra la demo

Un team (Sales) chiede a GitHub Copilot di rinominare il proprio Storage account su Azure. Copilot fa la modifica, la PR passa i controlli, ma la piattaforma la blocca prima che arrivi in Azure, perché la rinomina cancellerebbe lo Storage e i suoi dati. Poi Copilot corregge la richiesta, una persona approva e il cambiamento arriva in Azure. Alla fine si dimostra che anche un comando di cancellazione lanciato a mano viene rifiutato da Azure.

| Passo | Cosa succede | Durata |
|---|---|---|
| 1 | Copilot rinomina lo Storage di Sales: la PR è verde | ~3 min |
| 2 | Il rollout viene bloccato da due controlli (due `DENY`) | ~3 min |
| 3 | Copilot corregge: il nome resta, cambia solo un'etichetta | ~3 min |
| 4 | Il revisore approva, la modifica arriva in Azure | ~4 min |
| 5 | Un delete lanciato a mano viene rifiutato da Azure | ~1 min |

## 2. Le parole che incontrerai

| Parola | Cosa vuol dire qui |
|---|---|
| **Repository (repo)** | Il progetto su GitHub: https://github.com/carlosacchi/wpc-2026 |
| **Branch** | Una copia di lavoro del codice, separata da `main` |
| **PR (pull request)** | La richiesta di unire un branch in `main` |
| **CI / check `validate`** | I controlli automatici che girano su ogni PR, senza accesso ad Azure |
| **Rollout** | Il workflow GitHub che porta la configurazione in Azure: `rollout.yml` |
| **Ring / canary** | Il rollout parte da un team (Sales, ring 0) e solo dopo passa all'altro (Operations, ring 1) |
| **Gate** | Il controllo che legge l'anteprima delle modifiche e risponde `PASS` o `DENY` |
| **Environment** | Il punto in cui il rollout si ferma e aspetta l'approvazione di una persona |
| **Apply** | Il momento in cui la modifica viene davvero applicata in Azure |
| **Tenant** | In questo progetto: un team (Sales o Operations) con le sue risorse |

## 3. Chi serve: tre ruoli

| Ruolo | Account | Dove lavora | Cosa fa |
|---|---|---|---|
| **Chi presenta** | Un account GitHub con permesso di scrittura sul repo, **diverso da `azureitaliadevops`** | Computer principale: VS Code (terminale A) | Usa Copilot, apre le PR, lancia i rollout |
| **Revisore** | `azureitaliadevops` su GitHub | Un secondo dispositivo (portatile, tablet o telefono) con il browser | Approva il rollout quando la pipeline lo chiede |
| **Operatore Azure** | Un account Azure con ruolo **Owner** sulla subscription del lab | Computer principale, ma in un terminale **fuori** da VS Code (terminale B) | Solo il passo 5: prova a cancellare lo Storage |

Chi presenta e l'operatore Azure possono essere la stessa persona, in due terminali diversi.

> ⚠️ **Il revisore deve essere una persona e un account diversi da chi lancia il rollout.** GitHub impedisce di approvare un rollout che hai avviato tu: è voluto, ed è parte della demo. Se chi presenta usa l'account `azureitaliadevops`, nessuno potrà approvare e la demo si blocca al passo 4.

## 4. Cosa installare

Sul computer principale:

| Strumento | Versione | Per cosa serve | Come verificare |
|---|---|---|---|
| Git | qualsiasi recente | branch e commit | `git --version` |
| Node.js | 22 o successiva | test e script di reset | `node --version` |
| GitHub CLI (`gh`) | 2.50 o successiva | PR, rollout, approvazioni | `gh --version` |
| Azure CLI (`az`) | 2.76 o successiva | solo controlli e passo 5 | `az --version` |
| Terraform | 1.14.9 | per far eseguire a Copilot `terraform validate` | `terraform -version` |
| VS Code + estensione GitHub Copilot Chat | ultima | la parte con l'agente | Copilot Chat aperto, modalità **Agent** disponibile |

Sul secondo dispositivo del revisore basta un browser. L'app GitHub Mobile è comoda perché fa arrivare la notifica di approvazione.

## 5. Preparazione, una volta sola

### 5.1 Scaricare il progetto

In un terminale normale:

```sh
git clone https://github.com/carlosacchi/wpc-2026.git
cd wpc-2026
npm test
```

Atteso: alla fine `pass 95` e `fail 0` (il numero può cambiare, l'importante è `fail 0`). Non serve `npm install`: il progetto non ha dipendenze.

### 5.2 Collegare GitHub CLI con l'account di chi presenta

```sh
gh auth login          # scegli GitHub.com, HTTPS, login dal browser
gh auth status         # deve mostrare l'account di chi presenta, NON azureitaliadevops
```

### 5.3 Preparare il revisore

Sul secondo dispositivo:

1. Accedere a https://github.com con l'account `azureitaliadevops`.
2. Aprire https://github.com/carlosacchi/wpc-2026/actions e lasciare la pagina aperta.
3. Attivare le notifiche (app GitHub Mobile o email): quando servirà l'approvazione arriverà un avviso che c'è un deployment da approvare.

### 5.4 Preparare il terminale B (operatore Azure)

Apri un terminale **fuori da VS Code** (Terminale di macOS, Windows Terminal, ecc.):

```sh
cd wpc-2026
az login                                                   # login con l'account Owner della subscription
az account set --subscription "$(gh variable get AZURE_SUBSCRIPTION_ID)"
az storage account show -g wpc-2026-sales -n wpc26salesb0b966 --query name -o tsv
```

Atteso: l'ultima riga stampa `wpc26salesb0b966`. Lo Storage di Sales esiste.

### 5.5 Preparare VS Code (terminale A, quello dell'agente)

L'idea: Copilot lavora nel terminale integrato di VS Code, e quel terminale **non deve avere un login Azure**. Altrimenti l'agente potrebbe agire con i permessi di chi presenta.

1. Apri VS Code, poi *File → Apri cartella* e scegli la cartella `wpc-2026`.
2. Apri le impostazioni in formato JSON (*Command Palette → "Preferences: Open User Settings (JSON)"*) e aggiungi la riga del tuo sistema operativo:

   ```jsonc
   // macOS
   "terminal.integrated.env.osx": { "AZURE_CONFIG_DIR": "/tmp/wpc-agent-no-azure" },
   // Linux o WSL
   "terminal.integrated.env.linux": { "AZURE_CONFIG_DIR": "/tmp/wpc-agent-no-azure" },
   // Windows
   "terminal.integrated.env.windows": { "AZURE_CONFIG_DIR": "C:\\Temp\\wpc-agent-no-azure" }
   ```

3. Chiudi e riapri VS Code, apri un nuovo terminale integrato (*Terminale → Nuovo terminale*) e verifica:

   ```sh
   az account show
   ```

   Atteso: un errore che chiede di eseguire `az login`. È quello che vogliamo: da qui Azure non è raggiungibile.

4. Nelle impostazioni di VS Code cerca **auto approve** e controlla che l'approvazione automatica dei comandi di Copilot nel terminale sia **disattivata**. Così ogni comando che Copilot vuole eseguire chiede prima la tua conferma.

> ℹ️ Questa separazione è una precauzione, non una barriera di sicurezza: il terminale gira comunque con il tuo utente del computer. Serve a evitare che l'agente usi per sbaglio il tuo login Azure.

### 5.6 Fare una prova generale

Esegui tutta la demo (sezione 7) e poi il ripristino (sezione 9) almeno una volta prima del giorno dell'evento, con il revisore vero.

## 6. Il giorno della demo: controlli prima di iniziare

Un'ora prima, nel **terminale A** (VS Code):

```sh
git switch main
git pull --ff-only
git status --short
npm run demo:status
gh run list --workflow rollout.yml --limit 3
```

| Comando | Risultato atteso | Se non è così |
|---|---|---|
| `git status --short` | nessuna riga | ci sono file modificati: salvali altrove o annulla le modifiche, poi ripeti |
| `npm run demo:status` | **solo** `FILES: team files match demo/baseline.` | vedi la tabella sotto |
| `gh run list ...` | la run più in alto è completata con successo (✓) | una run è ancora in corso o in attesa: falla approvare o annullala (`gh run cancel <id>`) |

Cosa può stampare `npm run demo:status` e cosa fare:

| Messaggio | Significato | Cosa fare |
|---|---|---|
| `DRIFT: ...` | i file dei team non sono quelli di partenza | `npm run demo:reset` (sezione 9) |
| `OPEN PR: #...` | è rimasta aperta una PR di una demo precedente | chiuderla: `gh pr close <numero> --delete-branch` |
| `RUN NOT COMPLETED: ...` | un rollout aspetta ancora un'approvazione | farlo approvare al revisore o annullarlo |

Poi:

- **Terminale A:** `az account show` deve dare errore (vedi 5.5).
- **Terminale B:** `az storage account show -g wpc-2026-sales -n wpc26salesb0b966 --query name -o tsv` deve stampare `wpc26salesb0b966`.
- **Revisore:** collegato, pagina Actions aperta, notifiche attive.
- **Browser di chi presenta:** apri in schede separate le run registrate della [sezione 13](#13-riferimenti). Servono se qualcosa non risponde.
- **VS Code:** apri Copilot Chat e seleziona la modalità **Agent**. Apri [prompts.md](prompts.md) in una scheda, per copiare i prompt.

## 7. La demo, passo per passo

Regola d'oro: **se un passo non risponde entro 60 secondi, passa al piano B** (sezione 8) e vai avanti. Il pubblico non deve aspettare.

Tutti i comandi di questa sezione vanno nel **terminale A**, tranne il passo 5.

### Passo 1: Copilot rinomina lo Storage di Sales (~3 min)

**1a. Crea il branch di lavoro**

```sh
git switch main
git pull --ff-only
git switch -c demo/rename-sales
```

**1b. Chiedi la modifica a Copilot.** In Copilot Chat (modalità Agent) incolla:

```text
Il team Sales vuole che lo Storage account abbia un nome che indichi che è la versione rivista.
Aggiorna infra/workload/teams/sales.tfvars.json aggiungendo una "r" in fondo al nome dello storage account.
Poi esegui npm test e terraform validate su infra/workload.
```

- Copilot propone dei comandi: conferma `npm test`, `terraform init` e `terraform validate`.
- Se propone `terraform plan`, `terraform apply` o comandi `az`, **rifiuta**. È un buon momento per dire al pubblico che quel terminale non ha accesso ad Azure.
- Se Copilot avverte da solo che la rinomina forza la sostituzione dello Storage, dillo al pubblico ("le istruzioni del repo guidano l'agente") e **conferma comunque** la modifica: la demo mostra che a decidere è la piattaforma, non l'agente.

Atteso: nel file `infra/workload/teams/sales.tfvars.json` il nome diventa `wpc26salesb0b966r`; test e validate passano.

**1c. Controlla cosa è cambiato e committa SOLO il file del team**

```sh
git status --short
git diff infra/workload/teams/sales.tfvars.json
```

`git status` deve mostrare `infra/workload/teams/sales.tfvars.json`. Se compaiono altri file (per esempio `infra/workload/.terraform.lock.hcl`, che `terraform init` può aggiornare), **non vanno nella PR**: riportali com'erano.

```sh
git restore infra/workload/.terraform.lock.hcl    # solo se compare in git status
git add infra/workload/teams/sales.tfvars.json
git commit -m "Rename Sales storage account (requested by Sales)"
```

> ⚠️ Perché solo quel file: i file della piattaforma (gate, workflow, test, infrastruttura) hanno un proprietario in `CODEOWNERS`. Una PR che li tocca resta bloccata finché `azureitaliadevops` non la approva. I file dei team invece passano con la sola CI.

**1d. PR, controlli, merge**

```sh
git push -u origin demo/rename-sales
gh pr create --fill --base main
gh pr checks --watch --required
gh pr merge --squash --delete-branch --auto
```

Atteso: `validate` verde in circa un minuto. `--auto` rispetta la protezione di `main`: se qualche requisito è ancora in sospeso, GitHub esegue il merge appena tutti sono soddisfatti. Non usare `--admin` per aggirare i controlli.

Se `gh pr checks` non mostra nulla, verifica il check nella pagina della PR. Prima di avviare il canary, verifica che la PR risulti **Merged** (se il merge è in attesa, non basta che sia stato abilitato `--auto`).

Da dire: "La CI è verde e nel diff c'è solo una lettera in più. Ma `validate` non ci dice se Terraform dovrà sostituire lo Storage account: per scoprirlo serve il piano."

### Passo 2: il rollout viene bloccato, due DENY (~3 min)

**2a. Lancia il rollout solo sul primo team (canary)**

```sh
gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only
sleep 5
RUN=$(gh run list --workflow rollout.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN"
```

Il `sleep 5` serve perché GitHub impiega qualche secondo a creare la run. Senza, `RUN` potrebbe prendere la run precedente.

Atteso: dopo qualche minuto il job **Plan + gates (sales)** fallisce. Il rollout si ferma lì.

**2b. Mostra il motivo**

```sh
gh run view "$RUN" --log \
  | grep -E 'forces replacement|DENY:' \
  | awk '{ gsub(/(\033|\^\[)\[[0-9;]*m/, ""); print }'
```

`awk` rimuove solo i codici colore ANSI: `^[[33m->^[[0m^[[0m` diventa `->`.

Atteso:
- il cambio di nome con `# forces replacement`, che può comparire due volte: Terraform cancellerebbe lo Storage e ne creerebbe uno nuovo;
- due messaggi `DENY:` dei gate, uno da Terraform e uno da Bicep What-If; il filtro può mostrare anche l'annotazione finale del workflow.

In alternativa, apri la run nel browser (`gh run view "$RUN" --web`) e mostra il job **Plan + gates (sales)**.

Da dire: "Nessun artefatto, nessuna approvazione: il revisore non ha ricevuto niente, perché non c'è niente da approvare."

Tieni a portata le righe `DENY:`: servono al passo 3.

### Passo 3: Copilot corregge (~3 min)

**3a. Nuovo branch da `main` aggiornato**

```sh
git switch main
git pull --ff-only
git switch -c demo/fix-sales
```

**3b. In Copilot Chat** incolla questo prompt, sostituendo la riga tra `< >` con le righe `DENY:` del passo 2:

```text
Il rollout è stato bloccato dai gate con questo output:
<incolla le righe DENY del job "Plan + gates (sales)">
Correggi la modifica: lo storage account fisico non deve cambiare. La nuova classificazione del team
va espressa con service_label = "sales-storage-revised". Spiegami l'impatto atteso sul piano.
```

Atteso: nel file il nome torna `wpc26salesb0b966` e `service_label` diventa `sales-storage-revised`. Copilot spiega che è un aggiornamento sul posto di un'etichetta (tag), senza sostituzioni.

**3c. Controlla, committa solo il file del team, PR e merge**

```sh
git diff infra/workload/teams/sales.tfvars.json
git status --short
git restore infra/workload/.terraform.lock.hcl    # solo se compare
git add infra/workload/teams/sales.tfvars.json
git commit -m "Keep Sales storage account, express new classification as service_label"
git push -u origin demo/fix-sales
gh pr create --fill --base main
gh pr checks --watch --required
gh pr merge --squash --delete-branch --auto
```

Come al passo 1d, verifica che la PR risulti **Merged** prima di avviare il rollout.

### Passo 4: approvazione e canary (~4 min)

**4a. Lancia di nuovo il rollout**

```sh
gh workflow run rollout.yml -f scenario=baseline -f rings=canary-only
sleep 5
RUN=$(gh run list --workflow rollout.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN"
```

Atteso: il job **Plan + gates (sales)** passa. Nel piano c'è `Plan: 0 to add, 1 to change, 0 to destroy.` e i due gate rispondono `PASS`. Poi il job **Apply after human approval (sales)** resta in attesa (**Waiting**).

**4b. Mostra che chi presenta non può approvare**

```sh
gh api "repos/carlosacchi/wpc-2026/actions/runs/$RUN/pending_deployments" --jq '.[] | {environment: .environment.name, current_user_can_approve}'
```

Atteso: `"environment": "sales"` e `"current_user_can_approve": false`.

**4c. Il revisore approva**, sul secondo dispositivo:

1. Aprire la run in attesa (dalla notifica, o da https://github.com/carlosacchi/wpc-2026/actions, la run più in alto).
2. Premere **Review deployments**.
3. Spuntare **sales**, eventualmente scrivere un commento, premere **Approve and deploy**.

**4d. Guarda l'apply e il controllo finale**, nel terminale A dove `gh run watch` è ancora attivo.

Atteso:
- nel job **Apply after human approval (sales)**: `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`
- nel job **Ring health check (sales)**: una riga che inizia con `HEALTHY:`.

Da dire: "Con `rings=all` il rollout passerebbe ora al secondo team, Operations, con la sua approvazione. In sala ci fermiamo al canary."

### Passo 5: la rete di sicurezza (~1 min), nel terminale B

```sh
az storage account delete -g wpc-2026-sales -n wpc26salesb0b966 --yes
```

Atteso: il comando **fallisce**, con uno di questi due errori:
- `RequestDisallowedByPolicy`: lo blocca una Azure Policy (DenyAction);
- `ScopeLocked`: lo blocca il resource lock.

In entrambi i casi lo Storage non viene cancellato, anche se il comando arriva da un Owner della subscription e fuori da qualsiasi pipeline.

> ⚠️ Non provare a togliere il lock o a disattivare la policy per "far funzionare" il comando: sono le protezioni che la demo vuole mostrare.

## 8. Se qualcosa va storto

| Problema | Cosa fare |
|---|---|
| Copilot non risponde o fa altro | Fai la modifica a mano nel file `infra/workload/teams/sales.tfvars.json` (passo 1: aggiungi `r` in fondo a `storage_account_name`; passo 3: rimetti il nome originale e scrivi `"service_label": "sales-storage-revised"`), dillo al pubblico e prosegui |
| Il passo 1 non si riesce a completare | Al passo 2 usa la variante che simula la rinomina senza toccare `main`: `gh workflow run rollout.yml -f scenario=rename-demo -f rings=canary-only`. Il risultato è lo stesso: due `DENY`. Al passo 3 serve solo cambiare `service_label` |
| La PR resta bloccata con "Review required" | Hai committato un file oltre a quello del team. Riportalo com'è su `main` e aggiorna la PR: `git checkout origin/main -- <file>` poi `git commit -m "Keep platform files unchanged"` e `git push` |
| La CI o il rollout sono lenti (più di 60 secondi senza novità) | Mostra la run registrata della sezione 13 corrispondente e prosegui; la run vera continua da sola |
| Il nuovo rollout resta "Queued" | I rollout vanno in fila: ce n'è uno precedente in attesa. `gh run list --workflow rollout.yml --limit 5`, poi `gh run cancel <id>` su quello vecchio |
| `RUN` punta alla run sbagliata | Riprendi l'ID giusto con `gh run list --workflow rollout.yml --limit 3` e assegnalo a mano: `RUN=<id>` |
| Il revisore non è raggiungibile | Mostra la slide di backup dell'approvazione o la run registrata del passo 4 |
| Al passo 5 compare un altro errore (per esempio autorizzazione) | Controlla nel terminale B di essere sull'account Owner e sulla subscription giusta (`az account show`), oppure mostra la slide del passo 5 con l'output registrato |

## 9. Dopo la demo: rimettere tutto a posto

La demo ha cambiato un'etichetta (tag) dello Storage di Sales. Il ripristino la riporta al valore di partenza **senza cancellare niente**, passando per la stessa pipeline.

Nel terminale A:

```sh
git switch main
git pull --ff-only
git status --short           # deve essere vuoto: il reset rifiuta di partire con file modificati
npm run demo:reset
```

Cosa fa `demo:reset`, da solo:
1. confronta i file dei team con quelli di partenza (`demo/baseline/`);
2. apre una PR che li ripristina, aspetta la CI e la unisce;
3. lancia il rollout su entrambi i team (`rings=all`).

Cosa devi fare tu:
- Il rollout di **Sales** chiede l'approvazione, perché l'etichetta in Azure è diversa: il revisore approva come al passo 4c.
- **Operations** non ha differenze: l'apply viene saltato e resta solo il controllo finale.

Alla fine:

```sh
npm run demo:status
```

Atteso: **solo** `FILES: team files match demo/baseline.`

> ℹ️ Perché il ripristino si lancia dal tuo terminale e non da un pulsante su GitHub: deve aprire una PR e aspettare la CI. Una PR aperta da un workflow con il token automatico di GitHub non fa partire la CI, quindi resterebbe bloccata senza il check `validate`. Dal terminale la PR è tua e la CI parte normalmente; il rollout poi gira comunque nella pipeline.

Se il reset si ferma con `Checks passed but merge is blocked`, unisci la PR indicata nel messaggio e poi lancia:

```sh
node scripts/demo-reset.mjs rollout
```

Infine chiudi il terminale A di VS Code. Se vuoi, rimuovi la cartella vuota di `AZURE_CONFIG_DIR` (`/tmp/wpc-agent-no-azure`).

Il lab ora è pronto per la prossima volta. Prima di una nuova presentazione segui la sezione 11.

## 10. Cosa non fare mai

- Non lanciare `terraform apply`, `terraform destroy` o comandi `az ... delete` dal terminale di VS Code: le modifiche in Azure passano solo dal rollout.
- Non approvare il rollout con lo stesso account che l'ha lanciato (GitHub comunque non lo permette).
- Durante la demo non mettere nelle PR file diversi da quelli in `infra/workload/teams/`.
- Non togliere lock o disattivare policy in Azure: è la procedura di smantellamento del lab, da fare solo dopo l'evento e con approvazione.
- Non lasciare PR o run aperte alla fine: `npm run demo:status` deve tornare pulito.

## 11. Rifare la demo un'altra volta (stesso lab)

Il lab resta acceso tra una presentazione e l'altra: costa quasi niente (due Storage praticamente vuoti più lo state; identità, policy e lock non costano).

Dopo ogni demo basta il ripristino della sezione 9. Prima della presentazione successiva, **uno o due giorni prima**, fai questi controlli.

**1. Aggiorna il progetto e verifica che sia pulito** (terminale A):

```sh
git switch main
git pull --ff-only
npm test
npm run demo:status            # atteso: solo "FILES: team files match demo/baseline."
```

**2. Controlla tutto il lab senza cambiare niente.** Lancia un rollout sui due team con la configurazione di partenza:

```sh
gh workflow run rollout.yml -f scenario=baseline -f rings=all
sleep 5
RUN=$(gh run list --workflow rollout.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN"
```

Atteso: per Sales e per Operations l'apply viene **saltato** (non c'è niente da cambiare, quindi nessuna approvazione) e il controllo finale stampa `HEALTHY:`. Questo verifica in un colpo solo che Storage, lock, policy e identità siano a posto.

Se invece un team chiede l'approvazione, in Azure qualcosa è diverso dalla configurazione di partenza: apri il job **Plan + gates** di quel team e leggi il piano **prima** di far approvare.

**3. Controlla che le protezioni GitHub siano ancora quelle giuste:**

```sh
gh api repos/carlosacchi/wpc-2026/environments --jq '.environments[] | {name, reviewers: [.protection_rules[].reviewers[]?.reviewer.login], admin_bypass: .can_admins_bypass}'
gh api repos/carlosacchi/wpc-2026/branches/main/protection --jq '{checks: .required_status_checks.contexts, code_owners: .required_pull_request_reviews.require_code_owner_reviews, admins: .enforce_admins.enabled}'
```

Atteso: `sales` e `operations` con revisore `azureitaliadevops` e `admin_bypass: false`; su `main` il check `validate`, `code_owners: true`, `admins: true`.

**4. Controlla chi ha ruoli ampi sulla subscription** (terminale B):

```sh
az role assignment list --scope "/subscriptions/$(gh variable get AZURE_SUBSCRIPTION_ID)" --query "[].{chi:principalName, ruolo:roleDefinitionName}" -o table
```

Nessuno oltre agli amministratori previsti deve essere Owner o Contributor sulla subscription: un ruolo ereditato dall'alto attraversa i confini tra i team.

**5. Ricontrolla gli strumenti e Copilot.** Terraform deve restare alla versione 1.14.9 (la stessa della CI). Se l'estensione Copilot è stata aggiornata, riprova i prompt dei passi 1 e 3: il comportamento può cambiare tra una versione e l'altra. Annota modello e versione in [prompts.md](prompts.md).

**6. Fai una prova generale completa** (sezioni 7 e 9) e aggiorna la tabella delle run registrate nella sezione 13 e in [demo-runbook.md](demo-runbook.md) con i nuovi link.

## 12. Smantellare il lab: a mano, non con una pipeline

**Perché non c'è una pipeline che distrugge.** Per cancellare gli Storage bisogna prima togliere lock e policy, e per farlo serve un'identità con permessi da amministratore sulla subscription (Owner o simili). Metterla in una pipeline vorrebbe dire che chiunque riesca a lanciarla e a farla approvare, persona o agente, può cancellare il lab: è proprio ciò che la sessione insegna a evitare.

Per ripetere la demo non serve: la demo non cancella niente, e il ripristino della sezione 9 annulla le sue modifiche passando dalla stessa pipeline, con le identità normali e senza super user. Lo smantellamento resta un'operazione manuale, rara e deliberata (*break-glass*), da fare solo quando il lab non serve più.


> ⚠️ **Operazione irreversibile.** Cancella gli Storage dei team, lo state e le identità. Si fa solo quando il lab non serve più, dal **terminale B**, con l'account Owner, e possibilmente con una seconda persona che controlla ogni comando. Non è una cosa da fare tra una presentazione e l'altra: per quello basta la sezione 9.

L'ordine conta: prima si tolgono le protezioni, poi si cancella. Le protezioni esistono proprio per rendere questo passaggio deliberato.

**1. Prepara le variabili e guarda cosa c'è**

```sh
SUB=$(gh variable get AZURE_SUBSCRIPTION_ID)
STATE=$(gh variable get TF_STATE_ACCOUNT)
az account set --subscription "$SUB"
az resource list -g wpc-2026-sales -o table
az resource list -g wpc-2026-operations -o table
az resource list -g wpc-2026 -o table
```

> ⚠️ `wpc-2026` è un gruppo **condiviso**: può contenere risorse che non c'entrano con il lab. Non cancellare mai il gruppo intero: cancella solo le risorse indicate sotto.

**2. Togli la policy che impedisce il delete** (è assegnata su tre gruppi):

```sh
for rg in wpc-2026-sales wpc-2026-operations wpc-2026; do
  az policy assignment delete --name wpc-deny-storage-delete --scope "/subscriptions/$SUB/resourceGroups/$rg"
done
```

**3. Togli i lock**

```sh
az lock delete --name wpc-no-delete --resource-group wpc-2026-sales
az lock delete --name wpc-no-delete --resource-group wpc-2026-operations
az lock delete --name wpc-no-delete --resource-group wpc-2026 --resource "$STATE" --resource-type Microsoft.Storage/storageAccounts
```

**4. Cancella i gruppi dei team** (contengono gli Storage dei team e le loro assegnazioni):

```sh
az group delete --name wpc-2026-sales --yes
az group delete --name wpc-2026-operations --yes
```

**5. Cancella le risorse del lab nel gruppo condiviso** (non il gruppo):

```sh
PLAN_ID=$(az identity show -g wpc-2026 -n wpc-2026-plan --query principalId -o tsv)
az role assignment delete --assignee "$PLAN_ID" --scope "/subscriptions/$SUB/resourceGroups/wpc-2026"
az policy assignment delete --name wpc-private-storage --scope "/subscriptions/$SUB/resourceGroups/wpc-2026"
az storage account delete -g wpc-2026 -n "$STATE" --yes
az identity delete -g wpc-2026 -n wpc-2026-plan
az identity delete -g wpc-2026 -n wpc-2026-apply-sales
az identity delete -g wpc-2026 -n wpc-2026-apply-operations
```

**6. Cancella le definizioni create a livello di subscription**

```sh
az policy definition delete --name wpc-2026-deny-storage-delete
az role definition delete --name "wpc-2026 What-If preview" --scope "/subscriptions/$SUB"
```

**7. Verifica**

```sh
az group exists -n wpc-2026-sales           # atteso: false
az group exists -n wpc-2026-operations      # atteso: false
az resource list -g wpc-2026 --query "[?tags.project=='wpc-2026'].name" -o tsv   # atteso: nessuna riga
```

**8. Pulizia locale e su GitHub**

- Se sul tuo computer c'è `infra/bootstrap/terraform.tfstate`, spostalo in un archivio: descrive risorse che non esistono più.
- Il repository, gli environment e le variabili GitHub possono restare: servono se un giorno vorrai ricostruire il lab (procedura nel [README](../../README.md), sezione *Bootstrap*). Finché il lab non viene ricostruito, i rollout falliscono, ed è normale.

## 13. Riferimenti

Run registrate durante la prova generale del 10/11/2026, da aprire se un passo non risponde:

| Passo | Run |
|---|---|
| 2: rinomina, doppio DENY | https://github.com/carlosacchi/wpc-2026/actions/runs/42919010193 |
| 4: correzione, approvazione, `0 added, 1 changed`, HEALTHY | https://github.com/carlosacchi/wpc-2026/actions/runs/42919302894 |
| 4: approvazione del revisore (canary di partenza) | https://github.com/carlosacchi/wpc-2026/actions/runs/42823102175 |
| 9: ripristino dopo la prova | https://github.com/carlosacchi/wpc-2026/actions/runs/42920906060 |

Altri documenti:
- [demo-runbook.md](demo-runbook.md): la versione breve per chi presenta, con i messaggi da dire.
- [prompts.md](prompts.md): i prompt per Copilot.
- [da-portare-a-casa.md](da-portare-a-casa.md): il materiale per chi ha seguito la sessione (controlli, easy win, snippet).
- [README del progetto](../../README.md): come è costruita la piattaforma.
