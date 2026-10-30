# WPC 2026 — Copilot sotto controllo

Materiale di lavoro per la sessione accettata:

> **Copilot sotto controllo: Platform Eng multi-tenant su Azure con Terraform, Bicep e policy gates**

La sessione mette a fuoco un problema pratico: come far lavorare un agente AI sull'IaC senza affidargli il potere di decidere da solo cosa può arrivare in Azure.

## Laboratorio

- [Bootstrap](infra/bootstrap/main.tf): backend Terraform, identità federate, RBAC e Azure Policy.
- [Workload Terraform](infra/workload/main.tf): Sales e Operations con lo stesso [modulo Storage](infra/modules/workload-storage/main.tf).
- [Bicep di confronto](infra/compare/storage.bicep): baseline equivalente, non un secondo deployment della stessa risorsa.
- [Gate sul piano](scripts/plan-policy.mjs): regole didattiche esplicite e [test](tests/plan-policy.test.mjs), non uno scanner di sicurezza completo.
- [Pipeline](.github/workflows/): validazione senza credenziali sulle PR, solo plan manuale da `main`, ispezione dei subject OIDC senza login Azure.
- [Verifica artefatto](scripts/plan-artifact.mjs): checksum, commit, run, tentativo, team e destinazione prima dell'apply manuale dell'operatore.

Codice e workflow sono pubblicati. La [prima esecuzione CI](https://github.com/carlosacchi/wpc-2026/actions/runs/41131228129) ha superato test Node, Terraform mock, gate sui piani e compilazione Bicep. Anche la [diagnostica OIDC](https://github.com/carlosacchi/wpc-2026/actions/runs/41131232709) è riuscita. Il bootstrap Azure è stato applicato dopo approvazione: 9 risorse, poi piano senza modifiche; backend, federazione e policy riletti da Azure. Il workload e la sequenza replacement restano da verificare end-to-end.

## Demo: una rinomina che implica una distruzione

Non mostriamo un `destroy` eseguito: rinominiamo il parametro di uno Storage sandbox esistente e lasciamo che Terraform ne calcoli l'impatto.

1. **Preparazione:** configurare le variabili GitHub e lanciare il piano baseline Sales. Dopo review, l'operatore crea lo Storage applicando esattamente quell'artefatto su una postazione isolata.
2. **Baseline:** ripetere il piano, che deve risultare senza cambiamenti.
3. **Errore plausibile:** lanciare `rename-demo`. Il workflow aggiunge `r` al nome richiesto, senza modificare state o codice e senza cambiare gli altri parametri.
4. **Impatto:** `terraform validate` passa; il piano mostra il nome che forza replacement, `-/+` e una creazione/cancellazione. Un piano riuscito non significa cambiamento autorizzato.
5. **Blocco:** lo step `Enforce policy` mostra `IMPACT`, `OBSERVED` e `DENY`, termina con errore. Nessun artefatto applicabile viene pubblicato per `rename-demo`; non esiste alcun job apply.
6. **Correzione:** rilanciare `baseline`: nome originale, zero modifiche, gate verde; controllare che ID e configurazione Azure siano invariati.

```sh
gh workflow run plan.yml --repo carlosacchi/wpc-2026 --ref main \
  -f team=sales -f scenario=baseline
# Solo dopo creazione e verifica dello Storage iniziale:
gh workflow run plan.yml --repo carlosacchi/wpc-2026 --ref main \
  -f team=sales -f scenario=rename-demo
```

Il primo comando produce soltanto un piano: non crea il workload. La demo negativa deve fallire per **replacement osservato**, non per credenziali mancanti o un generico errore. Se lo Storage iniziale manca, il controllo `--expect-rename` restituisce un errore esplicito, non spaccia una creazione per una sostituzione. Le fixture dei test restano sintetiche.

Questa variante riproducibile non richiede Copilot: in sessione si può chiedere la stessa rinomina all'agente e ispezionare il diff. Il controllo non dipende da chi scrive il cambiamento. Il gate rifiuta il replacement: **non** offre un bottone per approvarlo comunque. Un piano consentito passa invece alla review/apply manuale descritta sotto; nessun environment GitHub attende un'approvazione umana.

## Verifica locale

Prerequisiti: Node.js 22+, Terraform 1.14.9 e Azure CLI con Bicep. AzureRM è bloccato dai lock file; non servono credenziali Azure per questi test.

```sh
npm test
terraform fmt -check -recursive infra
terraform -chdir=infra/bootstrap init -backend=false -lockfile=readonly
terraform -chdir=infra/bootstrap validate
terraform -chdir=infra/bootstrap test
terraform -chdir=infra/workload init -backend=false -lockfile=readonly
terraform -chdir=infra/workload validate
terraform -chdir=infra/workload test -verbose -json > terraform-test-events.jsonl
node scripts/check-mock-plans.mjs terraform-test-events.jsonl
az bicep build --file infra/compare/storage.bicep --stdout > /dev/null
```

## Prima di usare Azure e le pipeline

- Il resource group di laboratorio `wpc-2026` deve già esistere in Italy North. Compilare i file `.example` con nomi univoci e subscription autorizzata; non committare state, piani o credenziali.
- Il bootstrap richiede un operatore autorizzato per il control plane Storage, managed identity, RBAC e policy. Il container usa `storage_account_id`: in AzureRM 5.12.0 la creazione avviene tramite ARM. L'accesso Blob data plane serve poi a CI e operatore per state e locking. L'identità CI è Reader sul RG e non può fare deployment. Il bootstrap assegna i permessi Storage per l'apply a un utente umano esplicitamente selezionato, non a GitHub.
- Il repository è pubblico dal 30 ottobre 2026: [i required reviewers degli environment sono disponibili sui repository pubblici con Free, Pro e Team](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#required-reviewers). Le protezioni non sono ancora configurate: il codice attuale resta **plan in CI, revisione e apply manuali fuori dalla CI** e non offre un approval gate GitHub né separazione obbligatoria tra due persone. Per aggiungere apply protetto servono secondo revisore reale, no self-review, no bypass admin e identità federata separata; la sola visibilità pubblica non li attiva.
- Impostare `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_PLAN_CLIENT_ID`, `TF_STATE_ACCOUNT`, `SALES_STORAGE_NAME` e `OPERATIONS_STORAGE_NAME` come variabili GitHub. Non esiste un client apply della pipeline.
- Ricavare il subject OIDC effettivo di `main` con il workflow di ispezione e inserirlo nel bootstrap: non assumere il formato legacy. Nessun client secret è necessario.
- `main` richiede PR, check `validate` dell'app GitHub Actions e branch aggiornato; le regole si applicano anche agli amministratori, force push e cancellazione sono disabilitati. Non sono richieste approvazioni umane delle PR: manca un secondo revisore. `CODEOWNERS` non dimostra una review e questi controlli non sono un gate sul deployment. Chi può amministrare le protezioni può comunque riconfigurarle.
- Approvare costo e piano prima di qualsiasi apply. Nessun provisioning o cleanup viene eseguito dai test locali.

## Handoff all'operatore

Su una copia pulita del commit della run, con Terraform 1.14.9, `gh` autenticato al repository e Azure CLI autenticata come utente operatore:

1. Scaricare con `gh run download RUN_ID --name reviewed-plan-sales --dir DIRECTORY` (oppure Operations). Non usare artefatti di altre run.
2. Impostare `OPERATOR_OBJECT_ID` e `STATE_ACCOUNT` con gli output del bootstrap. Selezionare la subscription corretta in Azure CLI.
3. Eseguire `node scripts/plan-artifact.mjs check DIRECTORY sales carlosacchi/wpc-2026`. Il controllo verifica anche run riuscita, tentativo, commit locale, versione Terraform, login operatore, tenant, subscription e backend. Richiede la lettura del proprio profilo Entra.
4. Usare `ARM_USE_OIDC=false`, `ARM_USE_CLI=true`, `ARM_USE_AZUREAD=true`; rimuovere variabili di autenticazione residue di service principal, OIDC, MSI, SAS o Shared Key. Inizializzare lo stesso backend e la stessa chiave `sales.tfstate` con `-lockfile=readonly`, senza salvare opzioni OIDC o client ID nel backend.
5. Leggere il piano binario con `terraform show`, rigenerarne il JSON e ripetere `scripts/check-plan.mjs`. Verificare anche il diff del codice. Il checksum rileva incongruenze, non è un'attestazione crittografica di provenienza né un'approvazione.
6. Solo dopo l'approvazione umana eseguire `terraform apply` con il percorso assoluto di **quel piano salvato**, senza un nuovo plan. Il piano salvato non richiede un secondo prompt; il comando manuale è il punto di autorizzazione.

Eseguire l'apply da una postazione o account OS isolato dagli strumenti dell'agente, senza cache o file di credenziali condivisi. **Un altro terminale dello stesso utente non isola `az login`.** GitHub non applica, non conserva credenziali di deployment e non serializza gli apply manuali: è responsabilità dell'operatore procedere Sales → verifica → Operations. Il flusso Azure end-to-end deve ancora essere provato.

## Limiti intenzionali

Un solo RG e una directory Entra: state e tag distinti **non** dimostrano isolamento RBAC tra tenant. L'operatore apply ha permessi Storage sull'intero RG, compreso il backend; in produzione separare scope, backend e identità. Usare un operatore dedicato senza ruoli amministrativi ereditati, distinto dal bootstrap: questi assegnamenti non rimuovono eventuali privilegi preesistenti.

Il backend usa un endpoint pubblico autenticato Entra, senza Shared Key né accesso anonimo, con eccezione nominativa alla policy di rete. I workload hanno rete pubblica disabilitata ma nessun Private Endpoint: il laboratorio dimostra provisioning e governance del control plane, non accesso applicativo ai dati. Nel solo provider workload impostiamo [`features.storage.data_plane_available = false`](https://registry.terraform.io/providers/hashicorp/azurerm/5.12.0/docs/guides/features-block); non usare qui `queue_properties` o `static_website`. Il backend Terraform richiede comunque accesso Blob data plane per state e locking, distinto dalla creazione ARM del container.

Il principal plan è Reader sul control plane, ma ha accesso di scrittura al container state per locking. Gli artefatti plan sono potenzialmente sensibili. Delete e replacement vengono rifiutati dal gate; cleanup solo con piano separato e approvazione esplicita.

Su un repository pubblico considerare pubblici codice e log; non trattare gli artefatti come deposito confidenziale. Usare solo risorse e dati sintetici, evitare credenziali e valori sensibili nei piani. Il cambio di visibilità non pubblica automaticamente i materiali locali esclusi da Git.
