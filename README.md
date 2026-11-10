# WPC 2026 — Copilot sotto controllo

Materiale di lavoro per la sessione accettata:

> **Copilot sotto controllo: Platform Engineering multi-tenant su Azure con Terraform, Bicep e policy gates**

La sessione affronta un problema concreto: far lavorare un agente AI sull'IaC senza lasciargli decidere da solo cosa arriva in Azure. Il caso di partenza è reale: un'operazione di manutenzione corretta nella forma ma sbagliata nello scope. È successo nel [PIR Atlassian di aprile 2022](https://www.atlassian.com/engineering/post-incident-review-april-2022-outage) e nel [postmortem Azure DevOps di maggio 2023](https://status.dev.azure.com/_event/392143683/post-mortem). Mappatura completa in [docs/case-study.md](docs/case-study.md).

## Cosa dimostra il laboratorio

| Promessa del titolo | Dove è implementata |
|---|---|
| Multi-tenant (simulato) | Un RG per tenant (`wpc-2026-sales`, `wpc-2026-operations`), container di state e identità di apply separati per tenant ([bootstrap](infra/bootstrap/main.tf)) |
| Terraform | [Workload](infra/workload/main.tf) con lo stesso [modulo Storage](infra/modules/workload-storage/main.tf) e [file team versionati](infra/workload/teams/) |
| Bicep | [Template equivalente](infra/compare/storage.bicep) usato **solo** per l'ARM What-If, mai applicato |
| Plan / what-if | `terraform plan` salvato e `az deployment group what-if --validation-level ProviderNoRbac` sullo stesso scope del tenant |
| Policy gates | [Gate Terraform](scripts/plan-policy.mjs) e [gate What-If](scripts/whatif-policy.mjs): devono permettere entrambi |
| Policy-as-code in Azure | Azure Policy `Deny` (Storage pubblico) e `DenyAction` (delete degli Storage del lab) su ogni RG |
| Canary deploy | [rollout.yml](.github/workflows/rollout.yml): ring 0 Sales, poi ring 1 Operations solo se il canary è sano |
| Approvazione umana | Job apply legato all'environment GitHub del tenant (required reviewer, no self-review) |

Il flusso di ogni ring è definito in [tenant-ring.yml](.github/workflows/tenant-ring.yml):

```text
plan (MI plan, Reader)            apply (MI del tenant)             verify (MI plan)
├─ RG dal gate, non dai file team ├─ environment = tenant → umano  ├─ Storage privato e taggato
├─ terraform plan salvato         ├─ stesso run, sha256, commit    ├─ lock CanNotDelete presente
├─ Bicep What-If (ProviderNoRbac) ├─ ricontrollo gate              ├─ denyAction assegnata
├─ gate TF + gate What-If         └─ apply di QUEL piano           └─ plan -detailed-exitcode = 0
└─ artefatto legato alla run
```

## Livelli di difesa

Ogni livello presuppone che il precedente possa fallire, compreso il caso in cui l'agente o una persona modifichi il codice.

1. **Gate in CI**: rifiuta delete e replace (`-/+`), RG fuori dal tenant, proprietà non conformi, rinomina implicita in Bicep incrementale (crea il nuovo Storage e lascia l'originale orfano). La mappa tenant→RG sta nel gate, non nei file che l'agente modifica.
2. **Approvazione umana** nell'environment del tenant, con un revisore diverso da chi lancia il rollout.
3. **Identità di minimo privilegio**: l'apply di Sales ha *Storage Account Contributor* solo su `wpc-2026-sales` e scrive solo in `tfstate-sales`. La MI di plan è Reader e ha un ruolo custom limitato a `whatIf`/`validate`.
4. **Azure Policy `DenyAction`** sul delete degli Storage del lab, con cascade sul RG. Funziona anche se si aggira la pipeline.
5. **Resource lock `CanNotDelete`** sui RG dei tenant e sullo Storage di state, più `prevent_destroy` in Terraform.

I nomi dei RG sono vincolati a `wpc-*` (e mai `wpc-2026`) nel bootstrap, nel workload e nel gate: la subscription contiene altri carichi reali.

## Demo

```sh
# 1. Canary: plan + what-if + gate su Sales; l'apply attende l'approvazione nell'environment "sales"
gh workflow run rollout.yml --repo carlosacchi/wpc-2026 --ref main -f scenario=baseline -f rings=canary-only

# 2. Allargamento: Sales di nuovo (atteso zero cambi), poi Operations dopo il controllo di salute
gh workflow run rollout.yml --repo carlosacchi/wpc-2026 --ref main -f scenario=baseline -f rings=all

# 3. Fallback deterministico della rinomina: entrambi i gate devono rispondere DENY, senza apply
gh workflow run rollout.yml --repo carlosacchi/wpc-2026 --ref main -f scenario=rename-demo -f rings=canary-only
```

Storia principale sul palco:

1. Si chiede a Copilot (chat o coding agent) di rinominare lo Storage di Sales nel [file versionato](infra/workload/teams/sales.tfvars.json). La PR passa `validate`: `terraform validate` non vede il problema.
2. Dopo il merge, `rollout baseline`: il piano mostra `-/+`, il What-If mostra un nuovo Storage e l'originale ignorato. **Entrambi i gate rispondono DENY**, il job fallisce prima dell'artefatto e l'environment non viene mai raggiunto.
3. Si chiede a Copilot di correggere: nome fisico originale e nuova classificazione in `service_label` (solo tag). Nuovo rollout: aggiornamento in-place di un tag, approvazione nell'environment, apply, verifica di salute, poi ring 1.
4. Rete di sicurezza: anche un `az storage account delete` lanciato a mano viene rifiutato prima dal lock e, tolto il lock, dalla DenyAction.

`rename-demo` legge lo stesso file e aggiunge `r` con un override esplicito: è il fallback ripetibile e non va presentato come diff prodotto da Copilot.

## Verifica locale

Prerequisiti: Node.js 22+, Terraform 1.14.9 (come in CI) e Azure CLI 2.76+ con Bicep. Non servono credenziali Azure.

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

## Bootstrap (operatore della piattaforma)

Il bootstrap crea governance e identità. Non è eseguito dalla CI. L'operatore lo applica in locale, dopo aver rivisto il piano.

1. Copiare [terraform.tfvars.example](infra/bootstrap/terraform.tfvars.example) in `terraform.tfvars` (file ignorato da git). Il prefisso del subject OIDC si ricava con il workflow [oidc-subject.yml](.github/workflows/oidc-subject.yml).
2. Se lo state locale è andato perso, rigenerare gli import delle risorse esistenti:
   `node scripts/bootstrap-imports.mjs <storage-di-state>`. Il file `imports.generated.tf` è ignorato da git.
3. `terraform -chdir=infra/bootstrap plan -out=bootstrap.tfplan`. Il piano atteso non contiene `destroy`. Applicare solo dopo approvazione.
4. Creare gli environment GitHub `sales` e `operations` con:
   - required reviewer e *prevent self-review*;
   - solo il branch `main`;
   - la variabile `AZURE_APPLY_CLIENT_ID` uguale all'output `apply_client_ids[<tenant>]`.

   Il job apply rifiuta un ID mancante o uguale a quello di plan.

Variabili di repository: `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_PLAN_CLIENT_ID`, `TF_STATE_ACCOUNT`. Nessun client secret: tutte le identità sono federate con OIDC.

Gli assegnamenti di versioni precedenti (Storage Account Contributor e Blob Data Contributor dell'operatore, accesso della MI di plan al container `tfstate` legacy) non sono più gestiti dal codice. Vanno rimossi a mano dopo approvazione.

## Limiti dichiarati

- **Una sola directory Entra e una sola subscription.** I tenant sono RG con identità, state e policy separati: è l'isolamento di una piattaforma interna multi-team, non quello di un SaaS multi-tenant. Chi ha ruoli ereditati sulla subscription, come Contributor, scavalca questo isolamento.
- **Il canary è per tenant (ring)**, non uno split di traffico: lo Storage non ha traffico da instradare.
- **Il What-If è un preview.** Con `ProviderNoRbac` non verifica i permessi di scrittura. Il ruolo custom (`whatIf`/`validate` più Reader) va confermato alla prima run reale.
- **La DenyAction copre solo `delete`.** Il replace via Terraform è fermato dal gate e da `prevent_destroy`, non dalla policy. Lock e DenyAction rendono deliberato anche il cleanup: prima si tolgono, poi si cancella, sempre con approvazione.
- Il backend di state usa un endpoint pubblico autenticato Entra, senza Shared Key, con un'eccezione nominativa alla policy di rete. I workload non hanno Private Endpoint: il lab dimostra governance del control plane, non accesso ai dati.
- Repository pubblico: codice, log e artefatti vanno considerati pubblici. Usare solo risorse e dati sintetici.
- `CODEOWNERS` e branch protection non sostituiscono l'approvazione dell'environment, e chi amministra il repository può riconfigurarli.
