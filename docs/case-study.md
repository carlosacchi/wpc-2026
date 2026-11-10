# Caso di studio: lo scope sbagliato, eseguito correttamente

Il laboratorio non inventa uno scenario. Riproduce in piccolo un modo di fallire documentato in post-mortem pubblici: **un cambiamento legittimo nella forma colpisce più di quanto chi lo approva crede**, e nessun livello lo ferma prima dell'effetto irreversibile.

## Casi di riferimento

### Atlassian, aprile 2022 (caso principale)

[Post-Incident Review ufficiale](https://www.atlassian.com/engineering/post-incident-review-april-2022-outage).

- Uno script di manutenzione doveva rimuovere un'app legacy (Insight). Ha ricevuto gli **ID dei siti** invece degli ID dell'app e li ha cancellati in modalità permanente.
- Risultato: **883 siti (775 clienti)** cancellati tra le 07:38 e le 08:01 UTC. Per alcuni clienti il ripristino ha richiesto **fino a 14 giorni**.
- Il PIR osserva che lo script non ha verificato se gli ID si riferissero all'app o all'intero sito. Tra le azioni correttive indica soft delete universali e, per cancellazioni di questo tipo, più livelli di protezione, inclusi *staged rollout* e rollback testato.

### Azure DevOps, maggio 2023 (caso Azure)

[Post-mortem ufficiale](https://status.dev.azure.com/_event/392143683/post-mortem) ([sintesi di The Register](https://www.theregister.com/software/2023/06/03/typo-blamed-for-microsoft-azure-devops-outage-in-brazil/508301)).

- Una PR di grandi dimensioni migrava i pacchetti da `Microsoft.Azure.Management.*` a `Azure.ResourceManager.*`. Al suo interno un refuso trasformava "cancella il database snapshot" in "**cancella l'Azure SQL Server** che lo ospita".
- Il **Ring 0** interno è passato senza problemi perché non conteneva snapshot abbastanza vecchi. Nel **Ring 1** di South Brazil la condizione si è verificata: sono stati cancellati il server e **17 database di produzione**, con circa 10 ore di disservizio.
- Tra le correzioni: test sull'intero ciclo di vita del job e **resource lock** sui server SQL di produzione.

### Casi agentici (stesso schema, attore diverso)

| Caso | Cosa è successo | Lezione |
|---|---|---|
| [PocketOS, aprile 2026](https://www.theregister.com/software/2026/04/27/cursor-opus-agent-snuffs-out-startups-production-database/5224442) | Un agente di coding in staging trova un token in un file non correlato. Il token, con permessi più ampi del previsto, gli permette con una sola chiamata API di cancellare un volume con il database di produzione e i backup. | Le credenziali raggiungibili dall'agente sono il suo perimetro reale; ai delete serve un confine indipendente dal prompt. |
| Replit / SaaStr, luglio 2025 | Un agente cancella un database di produzione durante un *code freeze* dichiarato. | Un'istruzione in linguaggio naturale non è un controllo. |
| Amazon Q Developer, luglio 2025 (bollettino AWS-2025-015) | Un prompt distruttivo viene introdotto tramite contributo esterno in una versione dell'estensione. | La supply chain dell'agente fa parte della superficie d'attacco. |

## Dal post-mortem al laboratorio

Il lab simula una piattaforma interna con due tenant, Sales e Operations. È la situazione di una grande organizzazione multi-team, ma anche di un singolo team con ruoli separati: chi scrive codice, chi approva, chi gestisce la piattaforma.

| Modo di fallire osservato | Dove si vede nei casi | Controllo nel lab | Tipo |
|---|---|---|---|
| Lo scope reale è più ampio di quello percepito | Atlassian (sito invece di app), ADO (server invece di DB) | Il gate risolve il RG dal tenant e rifiuta qualsiasi risorsa fuori scope. La mappa tenant→RG non sta nei file che l'agente modifica. | Preventivo, CI |
| Il cambiamento "sembra" un aggiornamento ma implica una distruzione | ADO (refuso in una PR enorme), rinomina in Terraform | `terraform plan` + gate: `-/+` e delete → DENY. What-If Bicep + gate: rinomina implicita → DENY. | Preventivo, CI |
| La validazione sintattica passa | ADO (test non coprivano la condizione) | `terraform validate` passa: la decisione si basa sul **piano**, non sulla sintassi. | Didattico |
| Il canary non incontra la condizione critica | ADO (Ring 0 senza snapshot) | Il ring 1 parte solo se il ring 0 supera il controllo di salute: Storage privato, lock, DenyAction e assenza di drift. I gate girano **in ogni ring**, non solo nel canary. | Detective + preventivo |
| Credenziali troppo ampie | PocketOS, Atlassian | MI di plan Reader con ruolo custom solo `whatIf`/`validate`. Una MI di apply per tenant, limitata al suo RG e al suo container di state. | Minimo privilegio |
| Nessun umano tra il piano e l'effetto | Tutti | Environment GitHub per tenant: revisore obbligatorio, no self-review, solo `main`. L'artefatto approvato è legato a run, commit e sha256. | Approvazione |
| Il delete arriva per un'altra strada | PocketOS (API diretta) | `DenyAction` di Azure Policy e lock `CanNotDelete` sul RG, indipendenti dalla pipeline. | Piattaforma |

## Copilot: cosa copre già e cosa no

Il [coding agent di GitHub Copilot](https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations) offre già mitigazioni importanti:

- lavora solo su branch propri;
- non può approvare né unire le proprie PR;
- i workflow sulle sue PR richiedono approvazione;
- ha un firewall configurabile.

La regola "chi ha chiesto la PR non può approvarla" ha effetto **solo se la branch protection richiede almeno un'approvazione**. Nessuna di queste protezioni conosce lo scope Azure, la differenza tra update e replace o il tenant giusto: è il ruolo della piattaforma. Il messaggio della sessione è che **il controllo non dipende da chi scrive il cambiamento**, persona o agente.

## Limiti onesti della simulazione

- Una directory Entra e una subscription: l'isolamento è per RG, identità, state e policy. Chi ha ruoli ereditati sulla subscription lo scavalca.
- Il canary è per ring di tenant, non uno split di traffico.
- La DenyAction copre solo `delete`. Il replace via Terraform è fermato dal gate e da `prevent_destroy`.
