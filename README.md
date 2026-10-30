# WPC 2026 — Copilot sotto controllo

Materiale di lavoro per la sessione accettata:

> **Copilot sotto controllo: Platform Eng multi-tenant su Azure con Terraform, Bicep e policy gates**

La sessione mette a fuoco un problema pratico: come far lavorare un agente AI sull'IaC senza affidargli il potere di decidere da solo cosa può arrivare in Azure.

## Stato

- Repository Git inizializzato localmente e collegato a `https://github.com/carlosacchi/wpc-2026.git`.
- Il repository GitHub è privato e al momento non espone branch remoti.
- Analisi, outline delle slide e distinta tecnica sono materiali di preparazione locali, esclusi dal versionamento.
- Nessuna risorsa Azure è stata creata; la valutazione parte da un resource group demo vuoto.

## Prossimo obiettivo

Validare una demo ripetibile, a basso costo, basata su una pull request IaC non conforme, controlli automatici, approvazione umana e Azure Policy come ultima barriera. Terraform sarà il percorso live; Bicep sarà mappato sugli stessi controlli senza duplicare la demo.
