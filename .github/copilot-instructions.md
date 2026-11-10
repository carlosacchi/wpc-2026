# Istruzioni per GitHub Copilot in questo repository

Questo repository è un laboratorio di Infrastructure as Code governato. Le istruzioni sono una **guida** per l'agente: i controlli che contano sono i gate in CI, l'approvazione negli environment GitHub, Azure Policy e i resource lock. Non presentarle come un meccanismo di sicurezza.

- Non eseguire mai `terraform apply`, `terraform destroy`, `az ... delete`, `az deployment ... create` o comandi che modificano Azure. Le modifiche arrivano in Azure solo tramite `.github/workflows/rollout.yml`.
- Per i workload modifica solo i file in `infra/workload/teams/`. Non modificare gate (`scripts/*-policy.mjs`), test, workflow, bootstrap o state per far passare un cambiamento.
- Quando cambi un file dei team, spiega l'impatto atteso sul piano. Cambiare `storage_account_name` forza la sostituzione (`-/+`) dello Storage esistente: segnalalo esplicitamente. Per una nuova classificazione usa `service_label`, che diventa solo un tag.
- Il resource group di ogni tenant è deciso dalla piattaforma (`scripts/plan-policy.mjs`), non dai file dei team. Non spostare risorse tra tenant.
- Dopo una modifica, i controlli locali senza credenziali sono `npm test` e `terraform -chdir=infra/workload validate`. Ricorda che un `validate` verde non dice nulla sull'impatto in Azure.
