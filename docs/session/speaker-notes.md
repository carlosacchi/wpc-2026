# Speaker notes

Generato da `build_deck.py`: modificare lì, non qui.

## 1. Titolo

[0:00–0:30] Apro con due domande, mani alzate. Chi usa Copilot o un altro agente per scrivere Terraform o Bicep? E chi lascia che quel codice arrivi in produzione senza che una persona legga il piano?
- Mi aspetto che la seconda domanda abbassi parecchie mani: la sessione parte da lì.
- Della demo dico solo una cosa: fallirà di proposito, ed è il momento più interessante.

## 2. Chi sono

[0:30–1:15] Quarantacinque secondi, non di più: il pubblico è qui per la demo.
- Se c'è spazio per una frase sola, quella che lega il mio lavoro al tema: da dove nasce la domanda di questa sessione.
- Azure Italia Podcast: un invito a chi ascolta in italiano, senza pubblicità lunga.
- La pizza mezza italiana e mezza olandese di solito strappa un sorriso: lo lascio e vado avanti.

## 3. Hook

[1:15–2:15] Lascio l'immagine parlare per due secondi, poi:
- «Oggi chiedere a un agente di scrivere Terraform costa meno che chiedere un caffè. Il codice arriva in pochi secondi, ed è anche scritto bene. Il problema non è la qualità del codice.»
- «Non parliamo di prompt migliori. Parliamo di chi ha la chiave del cancello.»
- Anticipo l'obiezione: non è sfiducia verso Copilot. Sono le stesse regole che chiediamo alle persone da anni: review, piano, approvazione. L'agente entra in uno schema che esiste già, o che dovrebbe esistere.

## 4. Agenda

[2:15–2:45] Trenta secondi. Faccio notare una sola cosa: la demo sta al centro e prende un terzo del tempo.
- Ci arriviamo con due incidenti veri; dopo la demo parliamo di come si torna indietro e di cosa il lab NON dimostra.
- Annunciare subito che c'è una slide di limiti dichiarati crea fiducia: chi è scettico si rilassa.

## 5. Le parole di questa sessione (1/2)

[2:45–3:30] Le parole, prima metà. Non le leggo: sono qui perché in sala ci sono profili diversi, e chi fa sviluppo applicativo non deve perdersi al minuto 15. Il deck completo ha un glossario più lungo in fondo.
- Canary: il nome viene dal canarino nelle miniere, che segnalava il gas prima che arrivasse ai minatori. Qui il canarino è un intero team.
- Su Environment GitHub mi fermo un secondo: è la parte meno conosciuta di GitHub Actions ed è il cuore dell'approvazione umana nella demo.
- MI: da qui in avanti uso la sigla. Managed Identity vuol dire niente password da ruotare e niente secret nel repository.

## 6. Le parole di questa sessione (2/2)

[3:30–4:15] Seconda metà. Due parole hanno un significato diverso da quello che vi aspettate, e le dico ad alta voce.
- Tenant: per chi lavora su Azure "tenant" è la directory Entra ID. Qui no: è un team. È una scelta di linguaggio da piattaforma interna, e la dichiaro subito per non sembrare di barare più avanti.
- Replace: è la parola chiave della demo. Su una VM è fastidioso, su uno Storage con dei dati è una perdita di dati.
- Plan e What-If sono la stessa idea in due mondi: Terraform confronta codice, state e Azure; ARM confronta il template con quello che esiste in Azure. Due motori diversi, e lo sfrutteremo.

## 7. 1. Lo scope sbagliato, eseguito correttamente

[4:15] «Prima di parlare di AI, due incidenti in cui l'AI non c'entra niente.» Il problema esisteva già: l'agente lo accelera, non lo inventa.

## 8. Atlassian, aprile 2022

[4:15–6:45] Atlassian, raccontato come una storia e non come un elenco.
- Aprile 2022: un team deve dismettere un'app legacy, Insight. Lo script di manutenzione è corretto e fa esattamente il suo lavoro: cancella in modo permanente gli oggetti di cui riceve gli ID.
- Il problema è l'input. Invece degli ID dell'app riceve gli ID dei siti dei clienti. Tutto il resto funziona perfettamente.
- Il dettaglio che colpisce: la cancellazione avviene tra le 07:38 e le 08:01 UTC. Ventitré minuti per cancellare 883 siti; per alcuni clienti, fino a 14 giorni per tornare online.
- Il PIR non dice «lo script aveva un bug». Dice che nessuno ha verificato se quegli ID fossero dell'app o del sito. Mancava un controllo sullo scope, non sulla sintassi.
- Le azioni correttive sono tutte di piattaforma: soft delete ovunque, staged rollout, rollback testato. Nessuna è «scrivere script migliori».
- L'immagine: si voleva colpire il quadratino bianco, la cornice rossa ha preso l'isolato.

## 9. Azure DevOps, maggio 2023

[6:45–9:15] Azure DevOps, maggio 2023. È il caso più vicino a noi: è Azure, ed è un'organizzazione che il canary ce l'aveva.
- Una PR molto grande: migrazione dei pacchetti da Microsoft.Azure.Management a Azure.ResourceManager. Il tipo di PR che si approva con fiducia, perché «è solo una migrazione di SDK».
- Dentro c'è un refuso: il job che doveva cancellare un database snapshot adesso cancella l'Azure SQL Server che lo ospita.
- Ring 0, interno: non c'erano snapshot abbastanza vecchi da far scattare il job. Il canary è passato verde senza mai incontrare la condizione pericolosa.
- Ring 1, South Brazil: la condizione c'è. Diciassette database di produzione, circa dieci ore di disservizio.
- Lo dico ad alta voce: il canary riduce il raggio d'azione, non verifica l'effetto. Se il ring 0 non contiene il caso critico, non ti protegge.
- Tra le correzioni di Microsoft c'è il resource lock sui server SQL di produzione. Tenetelo a mente: nella demo il lock c'è, e un delete lanciato a mano lo fermerà Azure stesso, fuori dalla pipeline.

## 10. Lo schema comune

[9:15–10:45] Qui tiro le fila, lentamente: è la tesi dell'intera sessione.
- In entrambi i casi nessuno ha sbagliato la sintassi. Lo script di Atlassian e la PR di Azure DevOps erano codice valido, revisionato, testato. I test verificano che il codice faccia quello che dice, non che quello che dice sia giusto.
- Chi approvava percepiva uno scope più piccolo di quello reale: l'app invece del sito, il database invece del server.
- E tra il comando e l'effetto irreversibile non c'era nessun livello indipendente in grado di dire no.
- Frase da dire guardando la sala: il problema non è chi scrive il cambiamento. È cosa lo lascia passare.
- Ponte: adesso al posto della persona mettete un agente, che scrive dieci volte più velocemente e non si stanca mai di aprire PR.

## 11. 2. Ora il cambiamento lo scrive un agente

[10:45] Stesso schema, attore diverso. Una frase per rassicurare: non è una sessione contro gli agenti. Li uso ogni giorno, e li ho usati anche per costruire questo laboratorio.

## 12. Casi agentici: stesso schema

[10:45–12:45] Tre casi in due minuti, tre modi in cui si rompe il perimetro di un agente: le credenziali che trova, le istruzioni che ignora, il codice con cui è costruito.
- PocketOS, aprile 2026. L'agente lavora in staging e trova un token in un file che non c'entrava niente. Il token aveva più permessi del previsto: con una sola chiamata API spariscono il volume con il database di produzione e i backup. L'agente non ha forzato niente: ha usato quello che trovava. Le credenziali raggiungibili sono il suo perimetro reale.
- Replit, luglio 2025. Il fondatore di SaaStr aveva dichiarato un code freeze, in chat. L'agente ha cancellato comunque il database di produzione. Un'istruzione in linguaggio naturale non è un controllo: è una richiesta.
- Amazon Q, luglio 2025. Qui l'agente è la vittima: un token GitHub con permessi troppo ampi, nella configurazione di build, ha permesso di inserire codice malevolo nell'estensione per VS Code, finito in automatico nella release 1.84.0. Non ha fatto danni solo perché conteneva un errore di sintassi. Lo dico così: siamo stati fortunati, non protetti.
- Chiusura: nessuna di queste è una storia contro gli agenti. Sono storie di piattaforme senza confini.

## 13. Copilot: cosa sa e cosa non decide

[12:45–15:45] La slide in cui devo essere più onesto su Copilot.
- Prima colonna, veloce: GitHub ha fatto un buon lavoro sul coding agent. Però c'è un dettaglio che quasi nessuno nota: «chi chiede la PR non può approvarla» vale solo se la branch protection richiede almeno un'approvazione. Con zero approvazioni richieste la regola non scatta mai.
- In VS Code l'agent mode chiede conferma prima dei comandi, ma l'auto-approvazione è un'impostazione. E il terminale dell'agente è il mio terminale: se ho fatto az login, l'agente ha i miei permessi. È esattamente lo schema di PocketOS. Nella demo il terminale dell'agente non ha az login: è una precauzione, non un confine, perché gira comunque con il mio utente.
- Seconda colonna, ed è un cambio di idea mio: nella prima versione questa colonna si intitolava «Cosa non può sapere». Non reggeva più. Copilot sa benissimo che rinominare uno Storage forza un replace: lo trova nella documentazione del provider. Con Azure MCP vede le policy assegnate e i ruoli. E nel mio repo le istruzioni gli chiedono proprio di segnalarlo.
- Terza colonna: la domanda si è spostata da cosa sa a cosa decide. Sapere che è un replace non dà il diritto di farlo, né a un agente né a un collega junior.
- Nel lab, per i file dei team, l'approvazione umana obbligatoria non sta sulla PR: sta sull'environment del tenant, dove chi lancia il rollout non può approvarlo. Sulla PR serve solo quando tocca i file della piattaforma, che hanno un code owner diverso da me.

## 14. Azure MCP Server: contesto, non giudizio

[15:45–17:45] È la domanda che mi sono fatto preparando la sessione: MCP aiuta o complica la governance? La risposta onesta è: tutte e due.
- MCP è un protocollo: il server espone strumenti, l'intelligenza resta nel modello. Ma «è solo un connettore» è riduttivo. Porta contesto, cioè lo stato reale di Azure, e conoscenza già confezionata: documentazione del provider, regole IaC. È per questo che la slide precedente è cambiata.
- Cosa mi ha sorpreso leggendo la documentazione: le mani sono poche. I tool di Policy e RBAC sono in sola lettura. Sullo Storage crea account e carica blob, ma non c'è un tool per cancellarlo. E il comando az lo genera soltanto: a eseguirlo è il terminale, con le credenziali del terminale. Il rischio vero resta lì.
- Le credenziali: in locale usa quelle di chi lo avvia, tipicamente il vostro az login. Per il cloud agent di Copilot la configurazione ufficiale, azd coding-agent config, crea una managed identity dedicata con ruolo Reader di default. È lo stesso principio del lab: un'identità per ogni ruolo, e all'agente la più piccola.
- Cosa complica: ogni scrittura fatta via MCP salta plan, gate e approvazione. E il server cambia in fretta: la 3.0 è di ottobre 2026 e l'esempio ufficiale usa @azure/mcp@latest. Dopo Amazon Q, «latest» su uno strumento con accesso ad Azure dovrebbe far alzare un sopracciglio.
- Consiglio pratico: versione fissata, --read-only, solo i namespace che servono.
- Chiusura: MCP migliora la proposta. Non sostituisce il gate.

## 15. 3. La piattaforma decide, non chi scrive

[17:45] Da qui in avanti è tutto codice vero: repository pubblico, gira davvero su Azure, e ogni run che vedrete ha un numero che potete cercare. Il QR è nell'ultima slide.

## 16. Tenant simulati, confini reali

[17:45–20:15] Il lab. Lo dico subito, prima che me lo chieda qualcuno: una sola subscription, una sola directory Entra, e i tenant sono resource group. È il caso di una piattaforma interna con più team, o di un solo team che separa chi scrive, chi approva e chi gestisce.
- Ogni tenant ha quattro cose sue: resource group con lo Storage, container di state, identità di apply, environment GitHub. Se l'identità di apply di Sales prova a toccare Operations, Azure risponde 403: non è una regola del gate, è RBAC.
- Il resource group sta anche nel file del team, quindi l'agente può cambiarlo. Ma il gate confronta il piano con la sua mappa tenant → resource group e risponde DENY: la mappa vive nel codice della piattaforma, non in quello del team.
- Un'onestà in più: l'identità di plan è una sola e oltre alla lettura può scrivere lo state di entrambi i tenant, perché il plan prende il lock sullo state. È una semplificazione del lab: in produzione la separerei per tenant.
- I nomi dei resource group sono vincolati a wpc-* e mai wpc-2026: nella subscription ci sono anche carichi reali, e bootstrap, workload e gate rifiutano tutto il resto.

## 17. Il flusso di un ring

[20:15–22:45] Il flusso di un ring. Invito a seguire i colori: ogni colore è un'identità diversa, e la domanda giusta in ogni momento è «chi sta agendo adesso?».
- La CI sulla PR gira senza credenziali Azure, ed è voluto: una PR, anche scritta da un agente, non deve poter toccare Azure.
- Il plan produce due anteprime, terraform plan salvato e Bicep What-If sullo stesso resource group. Perché due? Perché sbagliano in modo diverso: lo vediamo tra poco con la rinomina.
- I gate devono rispondere PASS tutti e due. Se uno solo dice DENY non nasce l'artefatto, e senza artefatto l'environment non viene raggiunto: il revisore non riceve nemmeno la notifica. Non si può approvare per sbaglio qualcosa che non esiste.
- L'apply verifica che il piano sia quello generato in questa run, da questo commit, con lo stesso sha256: non si può approvare un piano e applicarne un altro.
- Un'osservazione che mi piace fare: il gate non è un'AI. Sono meno di 200 righe di JavaScript, leggibili in dieci minuti. È una scelta: un controllo che decide deve essere più semplice di ciò che controlla.

## 18. Cinque livelli, ognuno presuppone che il precedente fallisca

[22:45–24:45] La difesa a livelli. Ogni livello presuppone che il precedente possa fallire, anche quando a sbagliare è una persona che modifica il codice.
- 1 e 2 vivono in GitHub: gate e approvazione. Il 3 è l'identità: anche con tutto il resto aggirato, l'apply di Sales non può toccare Operations. 4 e 5 vivono in Azure: policy e lock funzionano anche se qualcuno passa dal portale o da az, completamente fuori dalla pipeline. È la stessa correzione scelta da Azure DevOps.
- Per chi conosce Terraform: prevent_destroy l'ho messo sullo state e sui resource group dei tenant, non sullo Storage dei workload. Lì Terraform rifiuterebbe il piano prima ancora del gate, e nella demo non vedreste il gate lavorare.
- Se qualcuno chiede perché così tanti livelli: perché ognuno ha un buco. Il gate è codice nello stesso repository, protetto solo dalla review del suo code owner; l'approvazione dipende da una persona attenta; la policy da come è scritta. Perché passi un errore, i buchi devono allinearsi tutti.

## 19. Una rinomina, due rischi

[24:45–26:45] La slide tecnica più importante: chi capisce questa, capisce la demo.
- Terraform: il nome di uno Storage account in Azure non si può cambiare. Terraform lo sa e pianifica un replace: -/+, cancella il vecchio e crea il nuovo. Con dei dati dentro, vuol dire perderli. E terraform validate è verde: la sintassi è perfetta.
- Bicep, ed è la parte che sorprende anche chi usa Azure da anni: in modalità incrementale ARM non cancella mai niente. Crea il nuovo Storage e lascia l'originale fuori dal template. Sembra la versione sicura, ma adesso ci sono due Storage, i dati stanno in quello che nessun codice gestisce più, e prima o poi qualcuno lo cancellerà credendolo orfano.
- Stessa riga cambiata, due rischi diversi: perdita di dati da una parte, risorsa orfana dall'altra. Per questo il gate legge entrambe le anteprime.
- Limite da dichiarare: la regola «Create più Storage ignorato uguale rinomina» funziona nel lab, dove ogni tenant ha un solo Storage. Non è una regola generale.

## 20. 4. Demo

[26:45] Due cose prima di iniziare. La demo è live: se un passo non risponde entro un minuto passo alla registrazione, senza drammi. E chi lancia il rollout non può approvarlo: per questo c'è un secondo account, il revisore, su un altro dispositivo.
Runbook: docs/session/demo-runbook.md.

## 21. Cosa guardare durante la demo

[26:45–41:45] Questa slide resta sullo schermo durante le attese della CI, che non sono poche: ogni job impiega qualche minuto.
- Tempi indicativi: passi 1, 2 e 3 tre minuti ciascuno, passo 4 quattro minuti, passo 5 uno. Un minuto di margine.
- Durante le attese commento chi sta agendo: nella PR nessuna credenziale, nel plan l'identità di plan, nell'apply quella di Sales, nel delete finale io come Owner.
- Passo 1: se Copilot segnala da solo che la rinomina forza un replace, è merito delle istruzioni del repo. Lo dico e confermo comunque la modifica: la demo mostra che il controllo regge anche quando chi propone insiste, persona o agente.
- Passo 2: indico la riga «forces replacement» e le due righe DENY. Poi faccio notare che il revisore non ha ricevuto nessuna richiesta: non c'è niente da approvare.
- Passo 4: mostro che io non posso approvare, poi approva il revisore. L'apply cambia un tag: 0 added, 1 changed, 0 destroyed. Il ring 1 lo racconto a parole: in sala lancio solo il canary, con rings=all partirebbe Operations con la sua approvazione.
- Passo 5: delete dello Storage dal terminale fuori da VS Code, come Owner della subscription. Risposta attesa: RequestDisallowedByPolicy; se risponde prima il lock, ScopeLocked. In entrambi i casi non si cancella niente, e non c'è nessuna pipeline di mezzo.
- Se avanza tempo: nella prova generale del 10 novembre lo script di reset si è fermato a metà per un bug, corretto il giorno dopo. Un buon esempio del perché si prova tutto, anche il rollback.

## 22. 5. Rollback, limiti, takeaway

[41:45] Ultima parte, la più onesta: come si rifà tutto domani mattina, e cosa questo lab non dimostra.

## 23. Rollback = roll-forward

[41:45–43:45] Il rollback. Dopo una demo andata male la tentazione è «cancello e ricreo». Qui il rollback non cancella niente.
- La baseline è versionata in demo/baseline. npm run demo:reset confronta i file dei team con la baseline, apre una PR di ripristino, aspetta la CI, la unisce e lancia il rollout su tutti i ring, con gli stessi gate e la stessa approvazione. Anche tornare indietro è un cambiamento, e passa dallo stesso cancello.
- È idempotente: se tutto è già allineato non apre nemmeno la PR e l'apply viene saltato. È così che preparo il lab prima di ogni sessione.
- Precisazione importante: il reset riporta configurazione e tag, non dati. Se il replace fosse passato, nessun roll-forward riporterebbe indietro i blob. Per i dati servono soft delete, backup e ripristini provati, e il lab non li dimostra.
- Il teardown dopo l'evento è break-glass: disattivo la DenyAction, tolgo il lock, cancello. Tre passi deliberati, approvati e tracciati.

## 24. Limiti dichiarati

[43:45–45:15] Questi limiti li dico io, prima che li trovi qualcuno in sala.
- Il più importante sono i ruoli ereditati. Chi è Contributor sulla subscription attraversa tutti i tenant, perché RBAC eredita verso il basso. Policy e lock restano, ma la separazione tra team no. Mi è successo: nel mio lab il revisore era Contributor sulla subscription, e l'ho tolto preparando questa sessione. Controllate i vostri.
- Il canary qui è per team: non c'è traffico da spostare, quindi niente split al 5%.
- La DenyAction protegge gli Storage che hanno il tag del progetto: chi può cambiare quel tag li fa uscire dalla policy. Il lock resta.
- Il lab protegge il control plane, non i dati: bloccare la cancellazione dello Storage non impedisce di cancellare i blob dentro.
- Chi amministra il repository può cambiare branch protection ed environment. Per questo policy e lock stanno in Azure: chi controlla GitHub non li controlla automaticamente.

## 25. Da portare a casa

[45:15–46:45] Tre frasi, lente. Se il pubblico se ne ricorda una sola, va bene lo stesso.
- La prima è per chi scrive pipeline: si decide sul piano, non sulla sintassi. Un validate verde non dice niente sull'effetto.
- La seconda è per chi disegna piattaforme: il raggio d'azione di un agente, o di una persona, è un'architettura di identità, non un'istruzione in un prompt.
- La terza è per chi la notte vuole dormire: una rete di sicurezza dentro Azure, fuori dalla pipeline, perché prima o poi qualcuno la pipeline la aggira.
- Pausa, poi la chiusura: «Copilot accelera. La piattaforma decide.»

## 26. Grazie! Codice, demo e fonti

[46:45–48:45] Lascio il QR sullo schermo per tutto il Q&A: è il modo più semplice per chi vuole rifare la demo.
Domande probabili, con una risposta breve:
- «E se l'agente modifica il gate?» Il gate sta nello stesso repository, ma i file della piattaforma (gate, workflow, test, bootstrap, moduli) hanno in CODEOWNERS un proprietario diverso da me: una PR che li tocca resta ferma finché non approva lui, chiunque l'abbia scritta, io o Copilot. I file dei team invece non hanno proprietario, ed è lì che lavora l'agente. E se qualcuno riconfigura GitHub, identità, policy e lock non dipendono dal repository.
- «Perché non basta Azure Policy?» Perché la policy valuta la singola richiesta, non il piano: non sa che quel delete fa parte di un replace.
- «Funziona con Azure DevOps?» Il principio sì: environment con approvazioni e controlli, service connection con workload identity federation, lo stesso gate in uno step.
- «Quanto costa il lab?» Quasi niente: due Storage praticamente vuoti più lo state. Identità e policy non costano.

## 27. Glossario (1/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 28. Glossario (2/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 29. Glossario (3/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 30. Glossario (4/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 31. Backup: approvazione dell'environment

BACKUP (nascosta). Run reale 42823102175: il revisore azureitaliadevops approva il deployment sales. Chi ha lanciato la run (carlosacchi) non può approvare: current_user_can_approve = false.

## 32. Backup: canary Sales, output reali

BACKUP (nascosta). Run 42823102175 (canary) e 42917201757 (rings=all: Sales senza modifiche, apply saltato).
