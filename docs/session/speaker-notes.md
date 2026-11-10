# Speaker notes

Generato da `build_deck.py`: modificare lì, non qui.

## 1. Titolo

[0:00–1:00] Presentazione.
- Chi sono, una frase. Poi subito la domanda: quanti usano Copilot o un agente per scrivere IaC? Quanti lo lasciano arrivare in produzione?
- Promessa: 45 minuti, un caso reale, una piattaforma vera su Azure, una demo live che fallisce di proposito.

## 2. Hook

[1:00–2:00] Il gancio.
- L'agente porta blocchi di infrastruttura in pochi secondi. Il cancello in mezzo non lo apre l'agente.
- "Oggi non parliamo di prompt migliori. Parliamo di chi ha la chiave del cancello."
- Non è sfiducia verso Copilot: è lo stesso schema che usiamo per le persone.

## 3. Agenda

[2:00–2:30] Agenda in 30 secondi. La demo è al centro e dura un terzo della sessione.

## 4. 1. Lo scope sbagliato, eseguito correttamente

[2:30] Prima di parlare di AI, due incidenti senza AI. Il problema esisteva già.

## 5. Atlassian, aprile 2022

[2:30–5:00] Atlassian.
- Script di manutenzione per rimuovere un'app legacy (Insight). Riceve gli ID dei siti, non dell'app.
- Lo script fa esattamente quello che gli è stato chiesto: cancellazione permanente.
- 883 siti, 775 clienti, fino a 14 giorni per tornare online.
- Il PIR dice: nessun cross-check degli ID. Azioni: soft delete ovunque, staged rollout, rollback testato.
- Immagine: si voleva colpire il quadratino bianco, la cornice rossa ha preso l'isolato.

## 6. Azure DevOps, maggio 2023

[5:00–7:30] Azure DevOps, South Brazil.
- Una PR enorme di migrazione SDK. Dentro, un refuso: "cancella lo snapshot" diventa "cancella il server SQL".
- Il canary c'era! Ring 0 interno: nessuno snapshot abbastanza vecchio, quindi nessun effetto.
- Ring 1 South Brazil: condizione presente, 17 database di produzione cancellati, circa 10 ore.
- Messaggio: il canary riduce il raggio, ma non sostituisce il controllo sull'effetto. Tra le correzioni: resource lock.
- Teniamo a mente il lock: lo ritroveremo nella demo.

## 7. Lo schema comune

[7:30–9:00] Lo schema.
- 1: lo scope reale è più grande di quello percepito.
- 2: tutto è sintatticamente valido; validate e review del diff non vedono l'effetto.
- 3: nessun livello indipendente tra il comando e l'effetto irreversibile.
- Frase chiave: il problema non è chi scrive il cambiamento, è cosa lo lascia passare.
- Ponte: e se a scriverlo è un agente che lavora dieci volte più veloce?

## 8. 2. Ora il cambiamento lo scrive un agente

[9:00] Stesso schema, attore diverso.

## 9. Casi agentici: stesso schema

[9:00–11:00] Tre casi, una frase ciascuno.
- PocketOS: l'agente trova un token in un file non correlato, il token può fare tutto, una chiamata API cancella volume e backup. Le credenziali raggiungibili sono il perimetro reale.
- Replit: code freeze dichiarato in chat, l'agente cancella comunque il DB. Un'istruzione non è un controllo.
- Amazon Q: prompt distruttivo entrato via contributo esterno nell'estensione. Anche la supply chain dell'agente è superficie d'attacco.
- Non sono storie contro gli agenti: sono storie di piattaforme senza confini.

## 10. Copilot: cosa copre e cosa no

[11:00–14:00] Onestà su Copilot.
- Il coding agent ha già protezioni serie: branch propri, non approva né unisce le sue PR, workflow da approvare, firewall.
- La regola "chi chiede la PR non la approva" funziona solo se la branch protection richiede almeno un'approvazione. Nel mio repo era a zero: regola inattiva.
- In VS Code agent mode i comandi chiedono conferma, ma l'auto-approvazione è un'impostazione. E il terminale dell'agente è il MIO terminale, con il MIO az login.
- Le istruzioni del repo (.github/copilot-instructions.md) le uso e le mostro: guidano, non bloccano.
- Ciò che Copilot non può sapere è il contesto della piattaforma: quale tenant, update o replace, quali credenziali. È lavoro del Platform Engineering.

## 11. 3. La piattaforma decide, non chi scrive

[14:00] Passiamo dal problema alla piattaforma. Tutto quello che vedete è nel repo pubblico e gira davvero in Azure.

## 12. Tenant simulati, confini reali

[14:00–16:30] Il lab.
- Una subscription, una directory: lo dico subito. È il caso di una piattaforma interna multi-team, o di un solo team con ruoli separati.
- Ogni tenant è un resource group con: il suo Storage, il suo container di state, la sua identità di apply, il suo environment GitHub.
- La MI di apply di Sales non può toccare Operations né lo state di Operations.
- La MI di plan è Reader, con un ruolo custom solo per il what-if.
- Su ogni RG: policy Deny per lo Storage pubblico, DenyAction sul delete, lock CanNotDelete.
- La mappa tenant → RG sta nel gate, non nei file che l'agente modifica.

## 13. Il flusso di un ring

[16:30–19:00] Il flusso. Seguite i colori delle identità.
- PR: la CI validate gira senza credenziali Azure.
- Plan: Terraform plan salvato E Bicep what-if sullo stesso RG. Due motori, due preview.
- Due gate: devono dire ALLOW entrambi. Se uno dice DENY non esiste artefatto e l'environment non viene mai raggiunto.
- Approvazione: environment del tenant, revisore obbligatorio, chi lancia non può approvare, niente bypass admin.
- Apply: identità del tenant, e solo il piano di QUESTA run: stesso commit, stesso sha256.
- Verify: Storage privato, lock, policy, nessun drift. Solo allora parte il ring successivo.

## 14. Cinque livelli, ognuno presuppone che il precedente fallisca

[19:00–21:00] Difesa a livelli. Ogni livello presuppone che il precedente possa fallire, anche se chi fallisce è una persona che modifica il codice.
- 1 gate in CI, 2 approvazione umana, 3 identità per tenant, 4 Azure Policy DenyAction, 5 lock e prevent_destroy.
- I livelli 4 e 5 vivono in Azure, fuori dalla pipeline: funzionano anche se qualcuno aggira GitHub. Come la correzione di Azure DevOps.

## 15. Una rinomina, due rischi

[21:00–23:00] La slide tecnica più importante.
- Terraform: cambiare il nome forza la sostituzione. -/+ vuol dire: cancello quello vecchio e ne creo uno nuovo. Su uno Storage con dati, è una perdita di dati.
- Bicep in modalità incrementale non cancella: crea il nuovo e lascia l'originale orfano, fuori dal template. Sembra innocuo, ma ora hai due Storage e i dati sono in quello che nessuno gestisce.
- Il gate legge entrambi i preview e dice DENY a entrambi. terraform validate e bicep build invece passano.

## 16. 4. Demo

[23:00] Demo. Runbook: docs/session/demo-runbook.md. Se qualcosa non risponde entro 60 secondi, passo alle run registrate (slide di backup nascoste).

## 17. Cosa guardare durante la demo

[23:00–38:00] Slide di orientamento: la lascio sullo schermo nei momenti di attesa della CI.
- 1 ~3 min, 2 ~3 min, 3 ~3 min, 4 ~4 min, 5 ~1 min. Margine 1 min.
- Nei tempi di attesa: commentare le identità (chi sta agendo adesso?).
- Se Copilot segnala da solo il rischio della rinomina: bene, lo dico e procedo con la modifica esplicita. È la dimostrazione che l'istruzione guida, ma il gate decide comunque.

## 18. 5. Rollback, limiti, takeaway

[38:00] Ultima parte: come rifare tutto domani, e cosa NON dimostra il lab.

## 19. Rollback = roll-forward

[38:00–40:00] Rollback.
- Non si torna indietro cancellando: si riporta in produzione l'ultima configurazione nota e buona, con gli stessi gate e la stessa approvazione.
- demo/baseline è versionata. npm run demo:reset apre la PR di ripristino, attende la CI, fa il merge e lancia il rollout.
- Idempotente: se tutto è allineato non cambia nulla e l'apply viene saltato. Così ho preparato questa sala.
- Il teardown è break-glass: disattivo la DenyAction, tolgo il lock, cancello. Tre passi deliberati, con approvazione.

## 20. Limiti dichiarati

[40:00–41:30] Onestà. Questi limiti li dico io prima che li chieda il pubblico.
- Il più importante: chi ha ruoli ereditati sulla subscription scavalca tutto. Nel mio lab il revisore era Contributor sulla subscription: l'ho tolto prima di questa sessione. Controllate i vostri.

## 21. Da portare a casa

[41:30–43:00] Tre frasi. Ripeterle lentamente.
- La decisione si prende sul piano, non sulla sintassi.
- Credenziali e approvazioni per tenant: il raggio d'azione è un'architettura, non un'istruzione.
- Una rete di sicurezza fuori dalla pipeline, perché prima o poi qualcuno la aggira.
- Chiusura: Copilot accelera. La piattaforma decide.

## 22. Grazie! Codice, demo e fonti

[43:00–45:00] Q&A. Lasciare il QR sullo schermo.

## 23. Backup: approvazione dell'environment

BACKUP (nascosta). Run reale 42823102175: il revisore azureitaliadevops approva il deployment sales. Chi ha lanciato la run (carlosacchi) non può approvare: current_user_can_approve = false.

## 24. Backup: canary Sales, output reali

BACKUP (nascosta). Run 42823102175 (canary) e 42917201757 (rings=all: Sales senza modifiche, apply saltato).
