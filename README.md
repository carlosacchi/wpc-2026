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

Il laboratorio è in costruzione: test locali non equivalgono a una prova Azure end-to-end.

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
- Il bootstrap richiede un operatore autorizzato per Storage (anche data plane), managed identity, RBAC e policy. L'identità CI è Reader sul RG e non può fare deployment. Il bootstrap assegna i permessi Storage per l'apply a un utente umano esplicitamente selezionato, non a GitHub.
- Il repository è pubblico dal 30 ottobre 2026: [i required reviewers degli environment sono disponibili sui repository pubblici con Free, Pro e Team](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#required-reviewers). Le protezioni non sono ancora configurate: il codice attuale resta **plan in CI, revisione e apply manuali fuori dalla CI** e non offre un approval gate GitHub né separazione obbligatoria tra due persone. Per aggiungere apply protetto servono secondo revisore reale, no self-review, no bypass admin e identità federata separata; la sola visibilità pubblica non li attiva.
- Impostare `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_PLAN_CLIENT_ID`, `TF_STATE_ACCOUNT`, `SALES_STORAGE_NAME` e `OPERATIONS_STORAGE_NAME` come variabili GitHub. Non esiste un client apply della pipeline.
- Ricavare il subject OIDC effettivo di `main` con il workflow di ispezione e inserirlo nel bootstrap: non assumere il formato legacy. Nessun client secret è necessario.
- Proteggere `main` con review e check richiesti se il piano GitHub lo permette: `CODEOWNERS` da solo non obbliga una review. Senza branch protection non dichiarare enforced il percorso PR.
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

Il backend usa un endpoint pubblico autenticato Entra, senza Shared Key né accesso anonimo, con eccezione nominativa alla policy di rete. I workload hanno rete pubblica disabilitata ma nessun Private Endpoint: il laboratorio dimostra provisioning e governance del control plane, non accesso applicativo ai dati. Nel solo provider workload impostiamo [`features.storage.data_plane_available = false`](https://registry.terraform.io/providers/hashicorp/azurerm/5.12.0/docs/guides/features-block): evita i controlli data plane dello Storage Account; non usare qui `queue_properties` o `static_website`. Il backend e il container bootstrap richiedono comunque accesso data plane.

Il principal plan è Reader sul control plane, ma ha accesso di scrittura al container state per locking. Gli artefatti plan sono potenzialmente sensibili. Delete e replacement vengono rifiutati dal gate; cleanup solo con piano separato e approvazione esplicita.

Su un repository pubblico considerare pubblici codice e log; non trattare gli artefatti come deposito confidenziale. Usare solo risorse e dati sintetici, evitare credenziali e valori sensibili nei piani. Il cambio di visibilità non pubblica automaticamente i materiali locali esclusi da Git.
