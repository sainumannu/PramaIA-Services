# Interfaccia di Sincronizzazione per il PDF Monitor Agent

Questo documento descrive l'interfaccia di monitoraggio della sincronizzazione implementata per il PDF Monitor Agent. Questa interfaccia consente di visualizzare lo stato di sincronizzazione tra il file system e il vector store, e di eseguire operazioni di riconciliazione manuale.

## Accesso all'Interfaccia

La nuova interfaccia di sincronizzazione è accessibile tramite il pannello di monitoraggio PDF nella sezione "Gestione Documenti" dell'applicazione server. È stata aggiunta una nuova scheda chiamata "Sincronizzazione" che consente di:

1. Visualizzare lo stato di connessione del client
2. Monitorare il servizio di riconciliazione
3. Verificare lo stato del sistema di recupero (recovery sync)
4. Eseguire operazioni di manutenzione come la riconciliazione forzata

## Componenti dell'Interfaccia

### Selezione del Client

Prima di accedere alle funzionalità di sincronizzazione, è necessario selezionare un client dalla lista nella scheda "Client PDF Monitor". Il client selezionato sarà evidenziato in azzurro e tutte le operazioni di sincronizzazione saranno eseguite su quel client specifico.

### Scheda Sincronizzazione

La scheda "Sincronizzazione" presenta tre sezioni principali:

#### 1. Stato Connessione

Questa sezione mostra:
- Stato corrente della connessione (Connesso/Disconnesso)
- Numero di successi e fallimenti consecutivi
- Timestamp dell'ultima connessione e disconnessione
- Durata dell'ultima disconnessione

#### 2. Servizio di Riconciliazione

Questa sezione mostra:
- Stato del servizio di riconciliazione (Attivo/Inattivo)
- Intervallo di sincronizzazione configurato
- Lista delle cartelle monitorate con:
  - Stato di monitoraggio (Attivo/Inattivo)
  - Timestamp dell'ultima sincronizzazione
  - Pulsante per forzare la riconciliazione
- Pulsante per forzare la sincronizzazione degli eventi bufferizzati

**Nota importante**: Solo le cartelle con stato **Attivo** sono incluse nella riconciliazione periodica automatica. Le cartelle configurate ma non attivamente monitorate (stato **Inattivo**) richiedono una riconciliazione manuale.

#### 3. Recovery Sync

Questa sezione mostra:
- Stato del servizio di recovery (Abilitato/Disabilitato)
- Stato della riconciliazione automatica
- Informazioni sul funzionamento del recovery sync

## Operazioni Disponibili

### Forza Riconciliazione

Permette di eseguire una riconciliazione immediata di una specifica cartella monitorata. Questa operazione:
- Scansiona la cartella selezionata
- Confronta i file presenti con quelli registrati nel vector store
- Risolve eventuali discrepanze (file mancanti o aggiuntivi)

### Forza Sync Eventi

Forza l'invio immediato di tutti gli eventi bufferizzati nel database locale al server. Utile quando:
- Si sospetta che alcuni eventi non siano stati inviati correttamente
- Dopo un periodo di disconnessione per accelerare la sincronizzazione

### Forza Registrazione

Forza la registrazione del client al server. Utile quando:
- Il client mostra uno stato di disconnessione persistente
- Dopo problemi di rete o riavvii del server

## Frequenza di Aggiornamento

È possibile configurare la frequenza di aggiornamento automatico delle informazioni di sincronizzazione:
- 5 secondi
- 10 secondi (default)
- 30 secondi
- 1 minuto

## Risoluzione dei Problemi Comuni

### Client Offline

Se il client risulta offline, sarà visualizzato un messaggio di avviso nella scheda sincronizzazione. In questo caso è possibile:
1. Verificare che il servizio di monitoraggio sia in esecuzione
2. Premere il pulsante "Forza Registrazione" per tentare una nuova registrazione
3. Controllare eventuali problemi di connessione di rete

### Discrepanze tra File System e Vector Store

Se si notano file presenti nel file system ma non nel vector store (o viceversa):
1. Selezionare la cartella interessata
2. Premere il pulsante "Forza Riconciliazione"
3. Attendere il completamento della riconciliazione
4. Verificare nuovamente

### Eventi Bloccati nel Buffer Locale

Se si sospetta che alcuni eventi non siano stati elaborati:
1. Premere il pulsante "Forza Sync Eventi"
2. Attendere il completamento dell'operazione
3. Verificare nella scheda "Attività Recenti" che gli eventi siano stati elaborati correttamente

## Note Tecniche

L'interfaccia comunica con i seguenti endpoint del PDF Monitor Agent:
- `/monitor/sync-status` - Ottiene lo stato di sincronizzazione
- `/monitor/reconcile` - Avvia una riconciliazione forzata
- `/monitor/force-sync` - Forza l'invio degli eventi bufferizzati
- `/monitor/register` - Forza la registrazione del client

Questi endpoint sono forniti dal sistema di sincronizzazione multi-layer implementato nell'agent.
