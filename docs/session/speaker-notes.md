# Speaker notes

Generato da `build_deck.py`: modificare lì, non qui.

## 1. Titolo

[0:00–0:30] DA RECITARE
Buongiorno. Chi di voi usa già Copilot, o un altro agente, per scrivere Terraform o Bicep? [pausa]

E prima di applicare quel codice in produzione, chi controlla il piano? [pausa]

Non è un test: oggi vediamo come verificare l'effetto di una modifica prima che arrivi in Azure. Nella demo il gate fermerà una rinomina rischiosa: quello sarà il risultato giusto.

SPUNTI FACOLTATIVI
- Fai una breve pausa dopo ciascuna domanda.
- Se nessuno risponde, vai avanti senza commentare la sala.
- Il gate blocca la rinomina: quello è il risultato atteso della demo.

## 2. Chi sono

[0:30–1:00] DA RECITARE
Sono Carlo Sacchi, lavoro come Lead DevOps in Metyis e mi occupo di Azure e Infrastructure as Code. Sono anche Microsoft MVP per Azure e co-conduco Azure Italia Podcast, un podcast in italiano dedicato ad Azure.

Vivo ad Amsterdam, quindi la pizza che vedete è metà italiana e metà olandese. Ma oggi siamo qui soprattutto per parlare di una domanda concreta: quando un agente può scrivere infrastruttura, chi decide se quella modifica è davvero sicura da applicare?

SPUNTI FACOLTATIVI
Quarantacinque secondi, non di più: il pubblico è qui per la demo.
- Se c'è spazio per una frase sola, quella che lega il mio lavoro al tema: da dove nasce la domanda di questa sessione.
- Azure Italia Podcast: un invito a chi ascolta in italiano, senza pubblicità lunga.
- La pizza mezza italiana e mezza olandese di solito strappa un sorriso: lo lascio e vado avanti.

## 3. Hook

[1:00–2:00] DA RECITARE
Oggi chiedere a un agente di scrivere Terraform costa meno che chiedere un caffè. Il codice arriva in pochi secondi e spesso è scritto molto bene. Ma la qualità del codice non basta a dirci se l'effetto che produrrà è quello giusto.

Per questo non parleremo di prompt migliori. Parleremo di chi ha la chiave del cancello. Non è sfiducia verso Copilot: sono le stesse regole che chiediamo alle persone da anni — review, piano e approvazione. L'agente può entrare in quel processo; non deve sostituirlo.

SPUNTI FACOLTATIVI
Lascio l'immagine parlare per due secondi, poi:
- «Oggi chiedere a un agente di scrivere Terraform costa meno che chiedere un caffè. Il codice arriva in pochi secondi, ed è anche scritto bene. Il problema non è la qualità del codice.»
- «Non parliamo di prompt migliori. Parliamo di chi ha la chiave del cancello.»
- Anticipo l'obiezione: non è sfiducia verso Copilot. Sono le stesse regole che chiediamo alle persone da anni: review, piano, approvazione. L'agente entra in uno schema che esiste già, o che dovrebbe esistere.

## 4. Agenda

[2:00–2:30] DA RECITARE
Partiamo da due incidenti reali, per vedere che il problema dello scope sbagliato esisteva già prima degli agenti. Poi vedremo cosa cambia quando a scrivere è un agente e come una piattaforma può decidere cosa arriva in Azure.

Al centro c'è una demo live. Chiuderemo con il rollback e con i limiti del laboratorio: li esplicito perché è importante distinguere ciò che dimostriamo da ciò che non dimostriamo.

SPUNTI FACOLTATIVI
Trenta secondi. Faccio notare una sola cosa: la demo sta al centro e prende un terzo del tempo.
- Ci arriviamo con due incidenti veri; dopo la demo parliamo di come si torna indietro e di cosa il lab NON dimostra.
- Annunciare subito che c'è una slide di limiti dichiarati crea fiducia: chi è scettico si rilassa.

## 5. Le parole di questa sessione (1/2)

[2:30–3:00] DA RECITARE
Prima di entrare nei casi, allineiamo alcune parole. Non leggerò tutte le definizioni: mi interessa che ci capiamo quando le userò.

Un ring, o canary, è il primo gruppo che riceve un cambiamento; nel nostro laboratorio il gruppo è un team intero. Un Environment di GitHub è la destinazione del deploy e può richiedere l'approvazione di una persona. Il gate è il controllo automatico che legge il piano e decide se la pipeline può proseguire.

Infine, una Managed Identity è un'identità Azure senza password salvate: nel laboratorio ne useremo una per il plan e identità di apply separate per i team.

SPUNTI FACOLTATIVI
Le parole, prima metà. Non le leggo: sono qui perché in sala ci sono profili diversi, e chi fa sviluppo applicativo non deve perdersi al minuto 15. Il deck completo ha un glossario più lungo in fondo.
- Canary: il nome viene dal canarino nelle miniere, che segnalava il gas prima che arrivasse ai minatori. Qui il canarino è un intero team.
- Su Environment GitHub mi fermo un secondo: è la parte meno conosciuta di GitHub Actions ed è il cuore dell'approvazione umana nella demo.
- MI: da qui in avanti uso la sigla. Managed Identity vuol dire niente password da ruotare e niente secret nel repository.

## 6. Le parole di questa sessione (2/2)

[3:00–3:30] DA RECITARE
Due parole avranno qui un significato preciso. Quando dico tenant intendo un team, non una directory Entra ID: in questo laboratorio Sales e Operations sono due tenant simulati, isolati con resource group e identità diverse.

Quando dico replace intendo che una risorsa viene cancellata e ricreata. Per uno Storage che contiene dati non è una semplice rinomina: può significare perdere quei dati.

Plan e What-If sono entrambi anteprime, ma arrivano da strumenti diversi. Terraform confronta codice, state e Azure; ARM confronta il template con ciò che esiste. Useremo entrambi per confrontare due modi diversi in cui una rinomina può andare male.

SPUNTI FACOLTATIVI
Seconda metà. Due parole hanno un significato diverso da quello che vi aspettate, e le dico ad alta voce.
- Tenant: per chi lavora su Azure "tenant" è la directory Entra ID. Qui no: è un team. È una scelta di linguaggio da piattaforma interna, e la dichiaro subito per non sembrare di barare più avanti.
- Replace: è la parola chiave della demo. Su una VM è fastidioso, su uno Storage con dei dati è una perdita di dati.
- Plan e What-If sono la stessa idea in due mondi: Terraform confronta codice, state e Azure; ARM confronta il template con quello che esiste in Azure. Due motori diversi, e lo sfrutteremo.

## 7. 1. Lo scope sbagliato, eseguito correttamente

[3:30] DA RECITARE
Prima di parlare di intelligenza artificiale, guardiamo due incidenti in cui l'intelligenza artificiale non c'entra. In entrambi, il codice ha fatto esattamente ciò che gli era stato chiesto. Il problema era l'ampiezza dello scope e l'assenza di un controllo indipendente prima dell'effetto.

SPUNTI FACOLTATIVI
«Prima di parlare di AI, due incidenti in cui l'AI non c'entra niente.» Il problema esisteva già: l'agente lo accelera, non lo inventa.

## 8. Atlassian, aprile 2022

[3:30–5:45] DA RECITARE
Nell'aprile 2022 Atlassian stava dismettendo un'applicazione legacy chiamata Insight. Lo script di manutenzione era corretto: riceveva una lista di ID e cancellava gli oggetti corrispondenti. Il problema è che la lista conteneva gli ID dei siti dei clienti, non quelli dell'applicazione.

In ventitré minuti furono cancellati 883 siti, che coinvolgevano 775 clienti. Per alcuni, il ripristino richiese fino a quattordici giorni. Il codice non aveva un bug di sintassi: nessuno aveva verificato che gli ID appartenessero allo scope giusto.

Le correzioni furono di piattaforma: soft delete, rollout graduale e rollback testato. La lezione non è “scriviamo script migliori”. È che il sistema deve limitare e verificare l'effetto di uno script corretto prima che colpisca lo scope sbagliato.

SPUNTI FACOLTATIVI
Atlassian, raccontato come una storia e non come un elenco.
- Aprile 2022: un team deve dismettere un'app legacy, Insight. Lo script di manutenzione è corretto e fa esattamente il suo lavoro: cancella in modo permanente gli oggetti di cui riceve gli ID.
- Il problema è l'input. Invece degli ID dell'app riceve gli ID dei siti dei clienti. Tutto il resto funziona perfettamente.
- Il dettaglio che colpisce: la cancellazione avviene tra le 07:38 e le 08:01 UTC. Ventitré minuti per cancellare 883 siti; per alcuni clienti, fino a 14 giorni per tornare online.
- Il PIR non dice «lo script aveva un bug». Dice che nessuno ha verificato se quegli ID fossero dell'app o del sito. Mancava un controllo sullo scope, non sulla sintassi.
- Le azioni correttive sono tutte di piattaforma: soft delete ovunque, staged rollout, rollback testato. Nessuna è «scrivere script migliori».
- L'immagine: si voleva colpire il quadratino bianco, la cornice rossa ha preso l'isolato.

## 9. Azure DevOps, maggio 2023

[5:45–8:00] DA RECITARE
Il secondo caso riguarda Microsoft: Azure DevOps è il servizio, non il nome dell'azienda. Nel maggio 2023, durante una migrazione molto ampia del SDK di Azure, un refuso trasformò il job che doveva eliminare uno snapshot di database in un job che eliminava il server SQL che lo ospitava.

Il ring interno passò senza problemi, ma non conteneva snapshot abbastanza vecchi da attivare quel job. Quando il cambiamento arrivò in South Brazil, la condizione si verificò: furono cancellati diciassette database di produzione e il disservizio durò circa dieci ore.

Il canary aveva ridotto il raggio d'azione, ma non aveva verificato l'effetto pericoloso. Tra le correzioni ci fu anche un resource lock sui server SQL di produzione. Tenetelo a mente: nella nostra demo vedremo un lock fermare una cancellazione persino fuori dalla pipeline.

SPUNTI FACOLTATIVI
Azure DevOps è il servizio Microsoft. Il rollout graduale c'era già, ma il ring interno non conteneva il caso critico.
- Una PR molto grande: migrazione dei pacchetti da Microsoft.Azure.Management a Azure.ResourceManager. Il tipo di PR che si approva con fiducia, perché «è solo una migrazione di SDK».
- Dentro c'è un refuso: il job che doveva cancellare un database snapshot adesso cancella l'Azure SQL Server che lo ospita.
- Ring 0, interno: non c'erano snapshot abbastanza vecchi da far scattare il job. Il canary è passato verde senza mai incontrare la condizione pericolosa.
- Ring 1, South Brazil: la condizione c'è. Diciassette database di produzione, circa dieci ore di disservizio.
- Lo dico ad alta voce: il canary riduce il raggio d'azione, non verifica l'effetto. Se il ring 0 non contiene il caso critico, non ti protegge.
- Tra le correzioni di Microsoft c'è il resource lock sui server SQL di produzione. Tenetelo a mente: nella demo il lock c'è, e un delete lanciato a mano lo fermerà Azure stesso, fuori dalla pipeline.

## 10. Lo schema comune

[8:00–9:15] DA RECITARE
I due casi hanno lo stesso schema. La sintassi era valida; il codice era stato revisionato e testato. I test verificavano che il codice facesse ciò che diceva, ma non che ciò che diceva fosse la cosa giusta.

Chi approvava immaginava uno scope più piccolo: l'applicazione invece dei siti, il database invece del server. E tra il comando e l'effetto irreversibile non c'era un livello indipendente che potesse dire di no.

Quindi il problema non è chi scrive il cambiamento. È cosa lo lascia passare. Ora mettiamo al posto della persona un agente, capace di preparare cambiamenti molto più velocemente.

SPUNTI FACOLTATIVI
Qui tiro le fila, lentamente: è la tesi dell'intera sessione.
- In entrambi i casi nessuno ha sbagliato la sintassi. Lo script di Atlassian e la PR di Azure DevOps erano codice valido, revisionato, testato. I test verificano che il codice faccia quello che dice, non che quello che dice sia giusto.
- Chi approvava percepiva uno scope più piccolo di quello reale: l'app invece del sito, il database invece del server.
- E tra il comando e l'effetto irreversibile non c'era nessun livello indipendente in grado di dire no.
- Frase da dire guardando la sala: il problema non è chi scrive il cambiamento. È cosa lo lascia passare.
- Ponte: adesso al posto della persona mettete un agente, che scrive dieci volte più velocemente e non si stanca mai di aprire PR.

## 11. 2. Ora il cambiamento lo scrive un agente

[9:15] DA RECITARE
Lo schema resta lo stesso; cambia l'attore e aumenta la velocità. Preciso subito una cosa: questa non è una sessione contro gli agenti. Li uso ogni giorno e li ho usati anche per costruire questo laboratorio.

La domanda è come dare loro un perimetro adeguato: quali credenziali possono raggiungere, quali azioni possono eseguire e quali decisioni devono restare alla piattaforma e alle persone.

SPUNTI FACOLTATIVI
Stesso schema, attore diverso. Una frase per rassicurare: non è una sessione contro gli agenti. Li uso ogni giorno, e li ho usati anche per costruire questo laboratorio.

## 12. Casi agentici: stesso schema

[9:15–11:00] DA RECITARE
Tre casi mostrano tre modi diversi in cui il perimetro di un agente può fallire.

Nel caso PocketOS, un agente che lavorava in staging trovò un token in un file non correlato. Quel token aveva permessi eccessivi e bastò una chiamata per cancellare il volume con il database di produzione e i backup. L'agente non aveva forzato alcun limite: aveva usato una credenziale che poteva raggiungere. Le credenziali accessibili definiscono il suo perimetro reale.

Nel caso Replit, l'agente cancellò il database di produzione nonostante un code freeze dichiarato in chat. Un'istruzione in linguaggio naturale è una richiesta, non un controllo tecnico.

Nel caso Amazon Q, un token GitHub troppo ampio permise di inserire codice malevolo nella build dell'estensione. La release non fece danni solo perché il codice conteneva un errore di sintassi. Siamo stati fortunati, non protetti.

Non sono storie contro gli agenti: sono storie di piattaforme senza confini sufficienti.

SPUNTI FACOLTATIVI
Tre casi in un minuto e quarantacinque, tre modi in cui si rompe il perimetro di un agente: le credenziali che trova, le istruzioni che ignora, il codice con cui è costruito.
- PocketOS, aprile 2026. L'agente lavora in staging e trova un token in un file che non c'entrava niente. Il token aveva più permessi del previsto: con una sola chiamata API spariscono il volume con il database di produzione e i backup. L'agente non ha forzato niente: ha usato quello che trovava. Le credenziali raggiungibili sono il suo perimetro reale.
- Replit, luglio 2025. Il fondatore di SaaStr aveva dichiarato un code freeze, in chat. L'agente ha cancellato comunque il database di produzione. Un'istruzione in linguaggio naturale non è un controllo: è una richiesta.
- Amazon Q, luglio 2025. Qui l'agente è la vittima: un token GitHub con permessi troppo ampi, nella configurazione di build, ha permesso di inserire codice malevolo nell'estensione per VS Code, finito in automatico nella release 1.84.0. Non ha fatto danni solo perché conteneva un errore di sintassi. Lo dico così: siamo stati fortunati, non protetti.
- Chiusura: nessuna di queste è una storia contro gli agenti. Sono storie di piattaforme senza confini.

## 13. Copilot: cosa sa e cosa non decide

[11:00–13:30] DA RECITARE
Partiamo dalla pull request. Copilot non può approvare la propria PR. Ma questo, da solo, non ferma un merge: se il repository non richiede una review, la PR può essere unita senza approvazione.

In VS Code c'è un controllo diverso: l'agent mode può chiedermi conferma prima di eseguire un comando, ma posso anche attivare l'auto-approvazione. Inoltre l'agente usa il mio terminale: se lì sono già autenticato ad Azure, i suoi comandi possono usare le mie credenziali. Nella demo ho isolato la configurazione Azure come precauzione, ma non è un confine d'identità.

Copilot può conoscere l'effetto di una modifica. Per esempio, può leggere che rinominare uno Storage richiede un replace, o consultare le regole del repository. Ma sapere cosa succederà non significa avere il permesso di decidere se farlo.

Nel laboratorio ci sono due approvazioni distinte. Per applicare una modifica ai file di un team, il rollout si ferma sull'Environment GitHub del team e approva una persona diversa da chi l'ha avviato. Se invece una PR modifica i controlli della piattaforma, come gate o workflow, deve approvarla un Code Owner prima del merge.

SPUNTI FACOLTATIVI
- La review del Code Owner serve per modificare gate e workflow; l'approvazione dell'Environment serve per applicare il workload.
- Senza una review richiesta nelle regole del repository, una PR può essere unita senza approvazione.
- L'agent mode usa il terminale dell'utente e quindi può ereditare le sue credenziali Azure.

## 14. Azure MCP Server: contesto, non giudizio

[13:30–15:15] DA RECITARE
MCP aiuta la governance o la complica? La risposta è: può fare entrambe le cose. MCP è un protocollo con cui un modello usa strumenti esterni. Azure MCP Server porta contesto sullo stato di Azure e conoscenza utile, ma la decisione resta al modello e le credenziali restano quelle con cui il server viene avviato.

Nella configurazione locale, quindi, attenzione al vostro accesso ad Azure. Per il cloud agent si può configurare una managed identity dedicata e con privilegi limitati. Alcuni strumenti sono in sola lettura, ma ogni scrittura effettuata direttamente tramite un tool può saltare il percorso di plan, gate e approvazione.

La regola pratica è fissare la versione, abilitare la modalità read-only quando basta e caricare solo i namespace necessari. MCP può migliorare la proposta e dare contesto; non sostituisce il gate.

SPUNTI FACOLTATIVI
È la domanda che mi sono fatto preparando la sessione: MCP aiuta o complica la governance? La risposta onesta è: tutte e due.
- MCP è un protocollo: il server espone strumenti, l'intelligenza resta nel modello. Ma «è solo un connettore» è riduttivo. Porta contesto, cioè lo stato reale di Azure, e conoscenza già confezionata: documentazione del provider, regole IaC. È per questo che la slide precedente è cambiata.
- Cosa mi ha sorpreso leggendo la documentazione: le mani sono poche. I tool di Policy e RBAC sono in sola lettura. Sullo Storage crea account e carica blob, ma non c'è un tool per cancellarlo. E il comando az lo genera soltanto: a eseguirlo è il terminale, con le credenziali del terminale. Il rischio vero resta lì.
- Le credenziali: in locale usa quelle di chi lo avvia, tipicamente il vostro az login. Per il cloud agent di Copilot la configurazione ufficiale, azd coding-agent config, crea una managed identity dedicata con ruolo Reader di default. È lo stesso principio del lab: un'identità per ogni ruolo, e all'agente la più piccola.
- Cosa complica: ogni scrittura fatta via MCP salta plan, gate e approvazione. E il server cambia in fretta: la 3.0 è di ottobre 2026 e l'esempio ufficiale usa @azure/mcp@latest. Dopo Amazon Q, «latest» su uno strumento con accesso ad Azure dovrebbe far alzare un sopracciglio.
- Consiglio pratico: versione fissata, --read-only, solo i namespace che servono.
- Chiusura: MCP migliora la proposta. Non sostituisce il gate.

## 15. 3. La piattaforma decide, non chi scrive

[15:15] DA RECITARE
Da qui in avanti vedrete codice vero, in un repository pubblico, collegato a un laboratorio che gira davvero su Azure. Le run sono consultabili e il QR per il repository è alla fine.

Prima di guardare la demo, chiarisco come sono costruiti i confini del laboratorio e quali identità agiscono in ogni fase.

SPUNTI FACOLTATIVI
Da qui in avanti è tutto codice vero: repository pubblico, gira davvero su Azure, e ogni run che vedrete ha un numero che potete cercare. Il QR è nell'ultima slide.

## 16. Tenant simulati, confini reali

[15:15–17:45] DA RECITARE
Questo laboratorio usa una sola subscription e una sola directory Entra. I “tenant” sono resource group che rappresentano due team, Sales e Operations. È un modello utile per ragionare su una piattaforma interna multi-team, ma non va confuso con l'isolamento tra directory Entra separate.

Ogni team ha il proprio resource group, il proprio state, la propria identità di apply e il proprio Environment GitHub. Se l'identità di Sales prova a modificare Operations, Azure la ferma con RBAC. Se un file di team cambia il resource group, il gate lo confronta con una mappa che vive nel codice della piattaforma e lo rifiuta.

C'è anche una semplificazione dichiarata: l'identità di plan può scrivere lo state di entrambi i team. In produzione la separerei per tenant. Anche i nomi dei resource group sono vincolati per non coinvolgere carichi reali presenti nella subscription.

SPUNTI FACOLTATIVI
Il lab. Lo dico subito, prima che me lo chieda qualcuno: una sola subscription, una sola directory Entra, e i tenant sono resource group. È il caso di una piattaforma interna con più team, o di un solo team che separa chi scrive, chi approva e chi gestisce.
- Ogni tenant ha quattro cose sue: resource group con lo Storage, container di state, identità di apply, environment GitHub. Se l'identità di apply di Sales prova a toccare Operations, Azure risponde 403: non è una regola del gate, è RBAC.
- Il resource group sta anche nel file del team, quindi l'agente può cambiarlo. Ma il gate confronta il piano con la sua mappa tenant → resource group e risponde DENY: la mappa vive nel codice della piattaforma, non in quello del team.
- Un'onestà in più: l'identità di plan è una sola e oltre alla lettura può scrivere lo state di entrambi i tenant, perché il plan prende il lock sullo state. È una semplificazione del lab: in produzione la separerei per tenant.
- I nomi dei resource group sono vincolati a wpc-* e mai wpc-2026: nella subscription ci sono anche carichi reali, e bootstrap, workload e gate rifiutano tutto il resto.

## 17. Il flusso di un ring

[17:45–20:15] DA RECITARE
Seguiamo il flusso da sinistra a destra, chiedendoci ogni volta chi sta agendo. La pull request esegue la CI senza credenziali Azure. Il plan produce un piano Terraform salvato e un Bicep What-If sullo stesso resource group.

Due gate leggono le anteprime. Devono passare entrambi: se uno rileva un delete, un replace o una modifica fuori tenant, la pipeline si ferma prima di raggiungere l'Environment. Non c'è quindi un'approvazione da concedere per un piano che è già stato rifiutato.

Se il piano passa, una persona diversa da chi ha avviato il rollout approva l'Environment. L'apply usa l'identità limitata al tenant e verifica che il piano approvato sia quello prodotto da questa run e da questo commit. Alla fine un controllo verifica lo stato atteso.

Il gate è codice semplice e leggibile, non un'intelligenza artificiale: è intenzionale, perché la regola che decide dovrebbe essere più semplice del sistema che controlla.

SPUNTI FACOLTATIVI
Il flusso di un ring. Invito a seguire i colori: ogni colore è un'identità diversa, e la domanda giusta in ogni momento è «chi sta agendo adesso?».
- La CI sulla PR gira senza credenziali Azure, ed è voluto: una PR, anche scritta da un agente, non deve poter toccare Azure.
- Il plan produce due anteprime, terraform plan salvato e Bicep What-If sullo stesso resource group. Perché due? Perché sbagliano in modo diverso: lo vediamo tra poco con la rinomina.
- I gate devono rispondere PASS tutti e due. Se uno solo dice DENY non nasce l'artefatto, e senza artefatto l'environment non viene raggiunto: il revisore non riceve nemmeno la notifica. Non si può approvare per sbaglio qualcosa che non esiste.
- L'apply verifica che il piano sia quello generato in questa run, da questo commit, con lo stesso sha256: non si può approvare un piano e applicarne un altro.
- Un'osservazione che mi piace fare: il gate non è un'AI. Sono meno di 200 righe di JavaScript, leggibili in dieci minuti. È una scelta: un controllo che decide deve essere più semplice di ciò che controlla.

## 18. Cinque livelli, ognuno presuppone che il precedente fallisca

[20:15–22:15] DA RECITARE
La difesa ha cinque livelli. I primi due sono in GitHub: il gate sul piano e l'approvazione umana. Il terzo è l'identità di apply, limitata al resource group del proprio team. Gli ultimi due sono in Azure: una policy che blocca l'azione e un resource lock.

Questi ultimi livelli funzionano anche se qualcuno passa dal portale o usa direttamente la riga di comando, fuori dalla pipeline. Per questo il resource lock richiamato nel caso Azure DevOps ricompare nella demo.

Ogni livello può avere un buco: un errore nel gate, una persona distratta, una regola di policy configurata male. L'obiettivo è che per produrre l'effetto indesiderato debbano fallire più livelli indipendenti.

SPUNTI FACOLTATIVI
La difesa a livelli. Ogni livello presuppone che il precedente possa fallire, anche quando a sbagliare è una persona che modifica il codice.
- 1 e 2 vivono in GitHub: gate e approvazione. Il 3 è l'identità: anche con tutto il resto aggirato, l'apply di Sales non può toccare Operations. 4 e 5 vivono in Azure: policy e lock funzionano anche se qualcuno passa dal portale o da az, completamente fuori dalla pipeline. È la stessa correzione scelta da Azure DevOps.
- Per chi conosce Terraform: prevent_destroy l'ho messo sullo state e sui resource group dei tenant, non sullo Storage dei workload. Lì Terraform rifiuterebbe il piano prima ancora del gate, e nella demo non vedreste il gate lavorare.
- Se qualcuno chiede perché così tanti livelli: perché ognuno ha un buco. Il gate è codice nello stesso repository, protetto solo dalla review del suo code owner; l'approvazione dipende da una persona attenta; la policy da come è scritta. Perché passi un errore, i buchi devono allinearsi tutti.

## 19. Una rinomina, due rischi

[22:15–24:15] DA RECITARE
Questa è la slide tecnica che spiega la demo. In Azure il nome di uno Storage account non si cambia sul posto. Terraform pianifica un replace: elimina la risorsa vecchia e ne crea una nuova. Se la vecchia contiene dati, il rischio è perderli. Eppure la validazione della sintassi può essere verde.

Bicep in modalità incrementale si comporta diversamente: crea il nuovo Storage e lascia quello vecchio in Azure, anche se non è più nel template. A prima vista sembra più prudente, ma il vecchio Storage resta orfano e conserva i dati senza essere più gestito dal codice.

La stessa riga modificata produce quindi due rischi diversi: perdita dei dati o risorsa orfana. Per questo il gate confronta entrambe le anteprime. La regola specifica del laboratorio sfrutta il fatto che ogni team ha un solo Storage; non è una regola universale.

SPUNTI FACOLTATIVI
La slide tecnica più importante: chi capisce questa, capisce la demo.
- Terraform: il nome di uno Storage account in Azure non si può cambiare. Terraform lo sa e pianifica un replace: -/+, cancella il vecchio e crea il nuovo. Con dei dati dentro, vuol dire perderli. E terraform validate è verde: la sintassi è perfetta.
- Bicep, ed è la parte che sorprende anche chi usa Azure da anni: in modalità incrementale ARM non cancella mai niente. Crea il nuovo Storage e lascia l'originale fuori dal template. Sembra la versione sicura, ma adesso ci sono due Storage, i dati stanno in quello che nessun codice gestisce più, e prima o poi qualcuno lo cancellerà credendolo orfano.
- Stessa riga cambiata, due rischi diversi: perdita di dati da una parte, risorsa orfana dall'altra. Per questo il gate legge entrambe le anteprime.
- Limite da dichiarare: la regola «Create più Storage ignorato uguale rinomina» funziona nel lab, dove ogni tenant ha un solo Storage. Non è una regola generale.

## 20. 4. Demo

[24:15] DA RECITARE
Ora passiamo alla demo. È live; se un passaggio non risponde entro un minuto, userò la registrazione e proseguiremo senza perdere il filo.

Il revisore è collegato da un secondo dispositivo. Chi avvia il rollout non può approvarlo: questa separazione è parte della dimostrazione, non un dettaglio organizzativo. Mentre guardiamo i passaggi, teniamo d'occhio chi agisce e quali controlli intervengono.

SPUNTI FACOLTATIVI
Due cose prima di iniziare. La demo è live: se un passo non risponde entro un minuto passo alla registrazione, senza drammi. E chi lancia il rollout non può approvarlo: per questo c'è un secondo account, il revisore, su un altro dispositivo.
Runbook: docs/session/demo-runbook.md.

## 21. Cosa guardare durante la demo

[24:15–39:15] DA RECITARE
Cominciamo chiedendo a Copilot di rinominare lo Storage di Sales. La pull request può risultare verde perché la validazione controlla la forma del codice, non l'effetto della modifica. Se Copilot segnala il replace, bene: le istruzioni del repository lo aiutano a riconoscerlo. Ma proseguiamo lo stesso, così vediamo che la protezione non dipende dal fatto che l'agente obbedisca.

Quando avviamo il rollout, guardiamo il piano Terraform: compare il replace. Poi guardiamo Bicep: il nuovo Storage verrebbe creato e quello vecchio resterebbe fuori dal template. I due gate rispondono DENY. Non nasce un deploy approvabile, quindi il revisore non riceve una richiesta.

Copilot corregge la modifica usando il nome originale e cambiando solo un tag. Questa volta le anteprime passano. Io non posso approvare il rollout; lo fa il revisore. L'apply cambia il tag senza aggiungere o distruggere risorse e il controllo finale conferma lo stato atteso. In produzione si potrebbe poi passare al ring Operations con la sua approvazione.

Infine, fuori dalla pipeline, provo a cancellare lo Storage direttamente da Azure come Owner. La policy o il lock rifiuta la richiesta. Questa protezione non dipende dal fatto che GitHub o il gate siano stati consultati.

SPUNTI FACOLTATIVI
Questa slide resta sullo schermo durante le attese della CI, che non sono poche: ogni job impiega qualche minuto.
- Tempi indicativi: passi 1, 2 e 3 tre minuti ciascuno, passo 4 quattro minuti, passo 5 uno. Un minuto di margine.
- Durante le attese commento chi sta agendo: nella PR nessuna credenziale, nel plan l'identità di plan, nell'apply quella di Sales, nel delete finale io come Owner.
- Passo 1: se Copilot segnala da solo che la rinomina forza un replace, è merito delle istruzioni del repo. Lo dico e confermo comunque la modifica: la demo mostra che il controllo regge anche quando chi propone insiste, persona o agente.
- Passo 2: indico la riga «forces replacement» e le due righe DENY. Poi faccio notare che il revisore non ha ricevuto nessuna richiesta: non c'è niente da approvare.
- Passo 4: mostro che io non posso approvare, poi approva il revisore. L'apply cambia un tag: 0 added, 1 changed, 0 destroyed. Il ring 1 lo racconto a parole: in sala lancio solo il canary, con rings=all partirebbe Operations con la sua approvazione.
- Passo 5: delete dello Storage dal terminale fuori da VS Code, come Owner della subscription. Risposta attesa: RequestDisallowedByPolicy; se risponde prima il lock, ScopeLocked. In entrambi i casi non si cancella niente, e non c'è nessuna pipeline di mezzo.
- Se avanza tempo: nella prova generale del 10 novembre lo script di reset si è fermato a metà per un bug, corretto il giorno dopo. Un buon esempio del perché si prova tutto, anche il rollback.

## 22. 5. Rollback, limiti, takeaway

[39:15] DA RECITARE
Chiudiamo con come ripristinare il laboratorio e con ciò che questa dimostrazione non prova. Tornare indietro non significa cancellare e ricreare: significa applicare una configurazione nota attraverso gli stessi controlli.

SPUNTI FACOLTATIVI
Ultima parte, la più onesta: come si rifà tutto domani mattina, e cosa questo lab non dimostra.

## 23. Rollback = roll-forward

[39:15–40:30] DA RECITARE
Dopo una demo, la tentazione può essere cancellare tutto e ripartire. Qui il reset è un roll-forward: confronta i file dei team con una baseline versionata, apre una pull request di ripristino, passa dalla CI e dallo stesso rollout approvato.

Il reset è idempotente: se i file sono già allineati non serve una pull request e l'apply viene saltato. Ma ripristina la configurazione, non i dati. Se un replace avesse cancellato i blob, il roll-forward non li riporterebbe indietro: servono backup e procedure di ripristino provate.

Il teardown finale è una procedura break-glass deliberata, con passaggi approvati e tracciati.

SPUNTI FACOLTATIVI
Il rollback. Dopo una demo andata male la tentazione è «cancello e ricreo». Qui il rollback non cancella niente.
- La baseline è versionata in demo/baseline. npm run demo:reset confronta i file dei team con la baseline, apre una PR di ripristino, aspetta la CI, la unisce e lancia il rollout su tutti i ring, con gli stessi gate e la stessa approvazione. Anche tornare indietro è un cambiamento, e passa dallo stesso cancello.
- È idempotente: se tutto è già allineato non apre nemmeno la PR e l'apply viene saltato. È così che preparo il lab prima di ogni sessione.
- Precisazione importante: il reset riporta configurazione e tag, non dati. Se il replace fosse passato, nessun roll-forward riporterebbe indietro i blob. Per i dati servono soft delete, backup e ripristini provati, e il lab non li dimostra.
- Il teardown dopo l'evento è break-glass: disattivo la DenyAction, tolgo il lock, cancello. Tre passi deliberati, approvati e tracciati.

## 24. Limiti dichiarati

[40:30–41:30] DA RECITARE
Prima che me lo chiediate, ecco i limiti principali. Il più importante riguarda i ruoli ereditati: un Contributor a livello di subscription può agire anche nei resource group dei team. La policy e il lock restano, ma la separazione tra i team non è più garantita. Per questo bisogna controllare i ruoli assegnati agli scope superiori.

Il canary qui è un team, non una percentuale di traffico. La policy protegge l'azione di delete sugli Storage con il tag previsto, non i blob al loro interno; il laboratorio protegge il control plane, non i dati.

Infine, chi amministra il repository può cambiare le protezioni di GitHub. Policy e lock sono in Azure proprio per aggiungere controlli che non dipendono solo dalla configurazione del repository.

SPUNTI FACOLTATIVI
Questi limiti li dico io, prima che li trovi qualcuno in sala.
- Il più importante sono i ruoli ereditati. Chi è Contributor sulla subscription attraversa tutti i tenant, perché RBAC eredita verso il basso. Policy e lock restano, ma la separazione tra team no. Mi è successo: nel mio lab il revisore era Contributor sulla subscription, e l'ho tolto preparando questa sessione. Controllate i vostri.
- Il canary qui è per team: non c'è traffico da spostare, quindi niente split al 5%.
- La DenyAction protegge gli Storage che hanno il tag del progetto: chi può cambiare quel tag li fa uscire dalla policy. Il lock resta.
- Il lab protegge il control plane, non i dati: bloccare la cancellazione dello Storage non impedisce di cancellare i blob dentro.
- Chi amministra il repository può cambiare branch protection ed environment. Per questo policy e lock stanno in Azure: chi controlla GitHub non li controlla automaticamente.

## 25. Protezioni spesso spente

[41:30–42:30] DA RECITARE
Il laboratorio protegge il control plane, non i dati. Quindi, prima di tornare in ufficio, ecco cosa controllare. Non c'è niente di esotico: sono impostazioni che esistono già, ma spesso sono spente di default, oppure qualcuno può spegnerle.

In Terraform, prevent_destroy sulle risorse che custodiscono dati e sullo state, e un gate che legga il piano. E attenzione al provider azurerm: di default, un destroy purga il Key Vault anche dal soft delete.

In Azure, soft delete e versioning sui blob, purge protection sul Key Vault, soft delete del server SQL, backup immutabili. E poi lock e policy, che valgono anche fuori dalla pipeline.

Non dovete ricordarla adesso: la trovate nel deck, sul repository.

SPUNTI FACOLTATIVI
La slide da fotografare. Non la leggo riga per riga: scelgo due o tre righe in base alla sala.
- prevent_destroy accetta solo valori letterali: non si può accendere con una variabile solo in prod. Se il modulo è condiviso tra gli ambienti, di fatto è acceso ovunque.
- prevent_destroy non è un controllo di sicurezza: se qualcuno, persona o agente, cancella il blocco resource o il lifecycle, Terraform distrugge senza avvisare. Per questo serve anche la review dei moduli (qui: CODEOWNERS) e, fuori da Terraform, lock e policy. Per togliere una risorsa dal codice senza distruggerla c'è il blocco removed con lifecycle { destroy = false }.
- Nel lab prevent_destroy è sullo state e sui RG dei tenant, non sullo Storage: lì Terraform fermerebbe il piano prima del gate e nella demo non vedreste il gate.
- Provider azurerm: purge_soft_delete_on_destroy è true di default per Key Vault, App Configuration, API Management e Cognitive Services. Un terraform destroy li cancella anche dal soft delete. prevent_deletion_if_contains_resources sui resource group è true di default: non spegnetelo per comodità.
- Storage: se cancellate un account, il recupero dal portale è possibile entro 14 giorni, se nessuno ha ricreato lo stesso nome, ed è best effort. Microsoft stessa raccomanda il lock. Il soft delete dei blob non aiuta se sparisce l'account intero.
- Azure SQL: il soft delete del server logico è in preview, da 1 a 7 giorni; per i server con meno di due anni è spento di default. È esattamente lo scenario di Azure DevOps.
- Azure Backup: con MUA le operazioni critiche, come spegnere il soft delete o ridurre la retention, richiedono l'autorizzazione di un'altra persona tramite Resource Guard.
- Bicep: con un deployment stack in denyDelete e detachAll, togliere una risorsa dal template non la cancella e nessuno la cancella a mano.
- Domanda probabile: «prevent_destroy su tutti gli ambienti o solo in prod?» Su tutti gli ambienti stabili, sulle risorse che custodiscono dati, chiavi o state: stesso comportamento ovunque, e la procedura per superarlo si impara in dev, non in prod durante un incidente. Non su tutto: su risorse senza dati blocca replace legittimi e insegna a toglierlo per riflesso. Negli ambienti effimeri, per esempio uno per PR, il teardown passa da una procedura esplicita.

## 26. Da portare a casa

[42:30–43:45] DA RECITARE
Tre idee da portare a casa. La prima: si decide sul piano, non sulla sintassi. Una validazione verde non ci dice quale sarà l'effetto.

La seconda: il raggio d'azione di un agente, come quello di una persona, dipende dall'architettura delle identità, non da una frase nel prompt.

La terza: serve una rete di sicurezza fuori dalla pipeline, perché prima o poi qualcuno la pipeline la aggirerà. Se ricordate una sola frase, ricordate questa: Copilot accelera. La piattaforma decide.

SPUNTI FACOLTATIVI
Tre frasi, lente. Se il pubblico se ne ricorda una sola, va bene lo stesso.
- La prima è per chi scrive pipeline: si decide sul piano, non sulla sintassi. Un validate verde non dice niente sull'effetto.
- La seconda è per chi disegna piattaforme: il raggio d'azione di un agente, o di una persona, è un'architettura di identità, non un'istruzione in un prompt.
- La terza è per chi la notte vuole dormire: una rete di sicurezza dentro Azure, fuori dalla pipeline, perché prima o poi qualcuno la pipeline la aggira.
- Pausa, poi la chiusura: «Copilot accelera. La piattaforma decide.»

## 27. Grazie! Codice, demo e fonti

[43:45–45:00] DA RECITARE
Grazie. Lascio il QR sullo schermo per le domande e per chi vuole esplorare o ripetere la demo: nel repository trovate il codice, le fonti e il runbook.

Una domanda che spesso arriva è se il gate possa essere modificato dall'agente. I file della piattaforma richiedono la review di un code owner; i file dei team sono invece quelli su cui l'agente può lavorare. E anche se qualcuno cambiasse le regole di GitHub, le identità, le policy e i lock in Azure resterebbero controlli separati.

Grazie, e sono felice di rispondere alle vostre domande.

SPUNTI FACOLTATIVI
Lascio il QR sullo schermo per il Q&A: è il modo più semplice per chi vuole rifare la demo.
Domande probabili, con una risposta breve:
- «E se l'agente modifica il gate?» Il gate sta nello stesso repository, ma i file della piattaforma (gate, workflow, test, bootstrap, moduli) hanno in CODEOWNERS un proprietario diverso da me: una PR che li tocca resta ferma finché non approva lui, chiunque l'abbia scritta, io o Copilot. I file dei team invece non hanno proprietario, ed è lì che lavora l'agente. E se qualcuno riconfigura GitHub, identità, policy e lock non dipendono dal repository.
- «Perché non basta Azure Policy?» Perché la policy valuta la singola richiesta, non il piano: non sa che quel delete fa parte di un replace.
- «Funziona con Azure DevOps?» Il principio sì: environment con approvazioni e controlli, service connection con workload identity federation, lo stesso gate in uno step.
- «Quanto costa il lab?» Quasi niente: due Storage praticamente vuoti più lo state. Identità e policy non costano.

## 28. Glossario (1/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 29. Glossario (2/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 30. Glossario (3/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 31. Glossario (4/4)

APPENDICE, non si presenta: è per chi scarica il deck.

## 32. Backup: approvazione dell'environment

BACKUP (nascosta). Run reale 42823102175: il revisore azureitaliadevops approva il deployment sales. Chi ha lanciato la run (carlosacchi) non può approvare: current_user_can_approve = false.

## 33. Backup: canary Sales, output reali

BACKUP (nascosta). Run 42823102175 (canary) e 42917201757 (rings=all: Sales senza modifiche, apply saltato).
