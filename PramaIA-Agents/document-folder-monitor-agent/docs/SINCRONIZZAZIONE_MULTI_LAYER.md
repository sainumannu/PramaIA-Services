# Strategia Multi-layer di Sincronizzazione File System / Vectorstore

Questo documento descrive la strategia multi-layer implementata nel PDF Folder Monitor Agent per garantire la sincronizzazione tra il file system locale e il vectorstore remoto.

## Problema

L'agente monitora cartelle sul file system per rilevare cambiamenti (nuovi file, modifiche, eliminazioni) e sincronizzarli con il vectorstore sul server. Tuttavia, possono verificarsi alcune situazioni critiche:

1. **Disconnessioni temporanee**: Se la connessione tra agente e server si interrompe, i cambiamenti nel file system non vengono propagati al vectorstore.
2. **Modifiche durante disconnessione**: Se vengono apportate modifiche al file system mentre l'agente è disconnesso, queste modifiche potrebbero non essere rilevate.
3. **Modifiche concorrenti**: Modifiche simultanee da più fonti possono causare incoerenze.

## Soluzione: Strategia Multi-layer

Abbiamo implementato una strategia multi-layer per garantire una sincronizzazione robusta e affidabile:

### Layer 1: Event Buffering

- Implementato tramite `event_buffer.py` e `smart_file_handler.py`
- Gli eventi del file system vengono bufferizzati in un database SQLite locale
- Gli eventi vengono inviati al server quando possibile
- Se l'invio fallisce, gli eventi rimangono nel buffer e verranno ritentati
- Gestisce efficacemente disconnessioni brevi (secondi/minuti)

### Layer 2: Riconciliazione Periodica

- Implementato tramite `reconciliation_service.py`
- Scansione periodica completa del file system (default: ogni ora)
- Confronto con lo stato del vectorstore tramite API
- Rilevamento intelligente delle differenze (file mancanti, modificati, eliminati)
- Sincronizzazione bidezionale delle differenze
- Gestisce disconnessioni più lunghe e modifiche mancate
- **Importante**: Opera solo sulle cartelle attivamente monitorate

### Layer 3: Connection Recovery Sync

- Implementato tramite `recovery_sync.py`
- Rileva quando la connessione viene ripristinata dopo un'interruzione
- Avvia automaticamente una riconciliazione completa al ripristino della connessione
- Intelligente: considera la durata della disconnessione per decidere se riconciliare
- Gestisce scenari di riconnessione dopo interruzioni significative

## Componenti Chiave

### FileHashTracker

- Memorizza hash efficienti dei file per rilevare cambiamenti
- Utilizza una combinazione di size, mtime e hash parziale per efficienza
- Persiste gli hash in un database SQLite per confronti tra riavvii

### FolderReconciliationService

- Servizio asincrono per la riconciliazione periodica
- Gestisce il confronto tra file system e vectorstore
- Implementa la logica di riconciliazione per risolvere le differenze

### ConnectionState

- Traccia lo stato della connessione con il server
- Rileva transizioni connesso -> disconnesso e viceversa
- Attiva callback al ripristino della connessione

## Endpoint di Controllo

L'agente espone alcuni endpoint per il controllo della sincronizzazione:

- `POST /monitor/reconcile?folder_path={path}`: Forza la riconciliazione manuale di una cartella
- `POST /monitor/force-sync`: Forza la trasmissione di eventi bufferizzati
- `GET /monitor/sync-status`: Ottiene lo stato del sistema di sincronizzazione

## Configurazione

Il comportamento della sincronizzazione può essere configurato tramite variabili d'ambiente:

- `RECONCILIATION_INTERVAL`: Intervallo in secondi tra riconciliazioni periodiche (default: 3600)
- `AUTO_RECONCILE_ON_RECONNECT`: Abilita/disabilita riconciliazione automatica al ripristino connessione (default: true)
- `MIN_DISCONNECTION_FOR_RECONCILE`: Durata minima in minuti della disconnessione per attivare riconciliazione (default: 1)

## Gestione della Riconciliazione Periodica

Il sistema di riconciliazione periodica è progettato per funzionare solo sulle cartelle **attivamente monitorate**. Questo comportamento è fondamentale per evitare scenari in cui:

1. Una cartella viene configurata ma il monitoraggio viene disattivato intenzionalmente
2. Il servizio di riconciliazione continua a processare la cartella anche se non più monitorata

Per garantire questo comportamento:

- Il metodo `get_active_folders()` della classe `FolderMonitor` restituisce solo le cartelle con monitoraggio attivo
- Il servizio di riconciliazione utilizza questa lista per decidere quali cartelle sincronizzare periodicamente
- L'interfaccia utente mostra chiaramente quali cartelle sono attivamente monitorate e quali no

Questo permette all'utente di:
- Disattivare temporaneamente il monitoraggio di una cartella senza doverla rimuovere dalla configurazione
- Mantenere la possibilità di eseguire riconciliazioni manuali su cartelle inattive quando necessario
- Avere una chiara visibilità di quali cartelle saranno incluse nella riconciliazione automatica

## Benefici

1. **Robustezza**: Garantisce la sincronizzazione anche in presenza di disconnessioni
2. **Efficienza**: Utilizza hash efficienti e confronti intelligenti per minimizzare il traffico di rete
3. **Completezza**: Implementa una strategia multi-layer per coprire diversi scenari di errore
4. **Auto-riparazione**: Capace di rilevare e risolvere incoerenze automaticamente

## Limitazioni

1. **Risorse**: La riconciliazione completa richiede risorse significative per cartelle molto grandi
2. **Latenza**: Possono esserci brevi periodi di incoerenza tra file system e vectorstore
3. **Conflitti**: In caso di modifiche concorrenti, prevale la versione più recente
