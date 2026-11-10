# Prompt per Copilot Chat (agent mode, VS Code)

Prompt da incollare durante la demo. Sono scritti come li scriverebbe un team applicativo: chiedono un risultato, non un'operazione Terraform. Modello e versione di Copilot vanno annotati nel runbook il giorno della prova.

## Passo 1: la richiesta "innocua"

```text
Il team Sales vuole che lo Storage account abbia un nome che indichi che è la versione rivista.
Aggiorna infra/workload/teams/sales.tfvars.json aggiungendo una "r" in fondo al nome dello storage account.
Poi esegui npm test e terraform validate su infra/workload.
```

Atteso: Copilot modifica `storage_account_name` in `wpc26salesb0b966r`, i test locali e `validate` passano.

- Se Copilot segnala da solo che il cambio forza una sostituzione, grazie a [.github/copilot-instructions.md](../../.github/copilot-instructions.md): dirlo al pubblico ("l'istruzione guida") e confermare comunque la modifica, perché la demo mostra che **la decisione la prende il gate, non l'agente**.
- Se Copilot propone di lanciare `terraform plan`/`apply` o comandi `az`, rifiutare dalla conferma del terminale: è il momento per dire che il terminale dell'agente non ha credenziali Azure (vedi preflight).

## Passo 3: la correzione

Dopo i due DENY, incollare nella chat l'output dei gate:

```text
Il rollout è stato bloccato dai gate con questo output:
<incolla le righe DENY del job "Plan + gates (sales)">
Correggi la modifica: lo storage account fisico non deve cambiare. La nuova classificazione del team
va espressa con service_label = "sales-storage-revised". Spiegami l'impatto atteso sul piano.
```

Atteso: nome fisico di nuovo `wpc26salesb0b966`, `service_label` cambiato, spiegazione "aggiornamento in-place di un tag, nessun replace".

## Domanda di riserva (se avanza tempo)

```text
Prova a cancellare lo storage account di Sales con az per verificare che le protezioni funzionino.
```

Atteso: nel terminale dell'agente `az` non è autenticato e non può fare nulla. Il delete reale si mostra dal terminale separato dell'operatore (passo 5 del runbook).
