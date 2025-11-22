# Guida al servizio PramaIA-LogService

## Introduzione

PramaIA-LogService è un sistema centralizzato di logging progettato specificamente per l'ecosistema PramaIA. Questo servizio consente di raccogliere, archiviare e analizzare i log provenienti da tutti i componenti dell'ecosistema in un unico punto centrale, facilitando il monitoraggio, la diagnostica e il debugging delle applicazioni.

## Caratteristiche principali

- **Centralizzazione dei log**: tutti i log dell'ecosistema PramaIA sono raccolti in un unico database
- **API RESTful**: interfaccia standardizzata per l'invio e la consultazione dei log
- **Client multipiattaforma**: librerie client per Python e JavaScript/TypeScript
- **Dashboard web**: interfaccia web per visualizzare, filtrare e analizzare i log
- **Autenticazione sicura**: sistema di autenticazione basato su API key
- **Archivio persistente**: memorizzazione dei log in database SQLite
- **Gestione della rotazione**: pulizia automatica dei log più vecchi
- **Tracciamento documenti**: monitoraggio completo del ciclo di vita dei documenti

## Integrazione con l'ecosistema PramaIA

Il servizio è progettato per integrarsi perfettamente con i seguenti componenti:

- **PramaIAServer**: backend e frontend
- **PramaIA-PDK**: server e editor di workflow
- **PramaIA-Agents**: agenti di monitoraggio e automazione
- **PramaIA-Plugins**: plugin per il PDK

## Architettura

```
+-------------------------+     +------------------------+
|                         |     |                        |
|   PramaIAServer         +---->+                        |
|   (Python/FastAPI)      |     |                        |
|                         |     |                        |
+-------------------------+     |                        |
                                |                        |
+-------------------------+     |   PramaIA-LogService   |
|                         |     |   (FastAPI + SQLite)   |
|   PramaIA-PDK           +---->+                        |
|   (TypeScript/Node.js)  |     |                        |
|                         |     |                        |
+-------------------------+     |                        |
                                |                        |
+-------------------------+     |                        |
|                         |     |                        |
|   PramaIA-Agents        +---->+                        |
|   (Python)              |     |                        |
|                         |     |                        |
+-------------------------+     +------------------------+
```

## Configurazione

### Server

La configurazione del servizio avviene tramite variabili d'ambiente o file `.env`:

- `PRAMAIALOG_HOST`: host su cui il servizio ascolta (default: 127.0.0.1)
- `PRAMAIALOG_PORT`: porta su cui il servizio ascolta (default: 8081)
- `PRAMAIALOG_DEBUG`: modalità debug (default: false)
- `PRAMAIALOG_LOG_LEVEL`: livello di log del servizio stesso (default: info)
- `PRAMAIALOG_DB_PATH`: percorso del database SQLite (default: ./logs/log_database.db)
- `PRAMAIALOG_RETENTION_DAYS`: giorni di conservazione dei log (default: 90)

### API Keys

Le API key sono configurate nel file `config/api_keys.json`. Le chiavi predefinite sono:

- **PramaIAServer**: `pramaiaserver_api_key_123456`
- **PramaIA-PDK**: `pramaiapdk_api_key_123456`
- **PramaIA-Agents**: `pramaiaagents_api_key_123456`
- **Admin**: `pramaiaadmin_api_key_123456`

Si consiglia di modificare queste chiavi in un ambiente di produzione.

## Utilizzo

### Avvio del servizio

Il servizio viene avviato automaticamente come parte dello script `start-all-clean.ps1`.
In alternativa, può essere avviato manualmente con:

```powershell
# Attivare l'ambiente virtuale
cd C:\PramaIA\PramaIA-LogService
& C:\PramaIA\PramaIAServer\PramaIA-venv\Scripts\Activate.ps1

# Avviare il servizio
python main.py
```

Il servizio sarà disponibile all'indirizzo configurato tramite `.env` o variabili d'ambiente.
Per esempio, impostando `PRAMAIALOG_HOST=http://127.0.0.1` e `PRAMAIALOG_PORT=8081` il servizio sarà raggiungibile su `http://127.0.0.1:8081`.

### Accesso alla dashboard

La dashboard web è accessibile all'indirizzo `${BACKEND_URL}/dashboard` se imposti `BACKEND_URL`, oppure `http(s)://{PRAMAIALOG_HOST}:{PRAMAIALOG_PORT}/dashboard`.

### API RESTful

Il servizio espone le seguenti API REST:

- `POST /api/logs`: crea una nuova voce di log
- `POST /api/logs/batch`: crea multiple voci di log in un'unica richiesta
- `GET /api/logs`: recupera le voci di log in base ai filtri specificati
- `GET /api/logs/stats`: recupera statistiche sui log
- `DELETE /api/logs/cleanup`: pulisce i log più vecchi di un certo numero di giorni
- `GET /api/lifecycle/document/{document_id}`: recupera il ciclo di vita di un documento specifico
- `GET /api/lifecycle/file/{file_name}`: recupera il ciclo di vita di un file specifico
- `GET /api/lifecycle/hash/{file_hash}`: recupera il ciclo di vita tramite hash del file

La documentazione completa delle API è disponibile all'indirizzo `${BACKEND_URL}/docs` o `http(s)://{PRAMAIALOG_HOST}:{PRAMAIALOG_PORT}/docs`.

## Client

### Client Python

```python
from pramaialog import PramaIALogger, LogLevel, LogProject

# Crea un'istanza del logger
logger = PramaIALogger(
    api_key="your_api_key",
    project=LogProject.SERVER,
    module="workflow_service"
)

# Invia log di diversi livelli
logger.info("Servizio avviato")
logger.warning(
    "Attenzione: file di configurazione non trovato", 
    details={"config_path": "/path/to/config"}
)
logger.error(
    "Errore durante il caricamento del workflow", 
    details={"workflow_id": "123", "error": str(e)},
    context={"user_id": "admin"}
)

# Log del ciclo di vita dei documenti
logger.lifecycle(
    "Documento PDF importato", 
    details={
        "document_id": "doc123",
        "file_name": "documento.pdf",
        "file_hash": "a1b2c3d4e5f6...",
        "lifecycle_event": "IMPORT"
    }
)

# Assicurati che tutti i log vengano inviati prima di terminare
logger.flush()
```

### Client JavaScript

```javascript
const { PramaIALogger, LogLevel, LogProject } = require('pramaialog');

// Crea un'istanza del logger
const logger = new PramaIALogger({
  apiKey: 'your_api_key',
  project: LogProject.PDK,
  module: 'workflow_editor'
});

// Invia log di diversi livelli
logger.info('Editor avviato');
logger.warning(
  'Attenzione: configurazione nodo non valida', 
  { nodeId: 'node-123', issues: ['Missing input'] }
);
logger.error(
  'Errore durante il salvataggio del workflow', 
  { workflowId: '123', error: err.message },
  { userId: 'admin' }
);

// Log del ciclo di vita dei documenti
logger.lifecycle(
  'Documento elaborato dal workflow', 
  { 
    document_id: 'doc123', 
    file_name: 'documento.pdf',
    file_hash: 'a1b2c3d4e5f6...',
    lifecycle_event: 'PROCESSED'
  },
  { workflow_id: 'workflow123' }
);

// Assicurati che tutti i log vengano inviati prima di terminare
await logger.flush();
```

## Livelli di log

Il servizio supporta i seguenti livelli di log, in ordine crescente di gravità:

- **DEBUG**: informazioni dettagliate utili per il debugging
- **INFO**: informazioni generali sul funzionamento del sistema
- **WARNING**: avvisi che indicano potenziali problemi
- **ERROR**: errori che impediscono il completamento di un'operazione
- **CRITICAL**: errori critici che potrebbero causare il malfunzionamento del sistema
- **LIFECYCLE**: speciale livello per tracciare il ciclo di vita dei documenti (importazione, elaborazione, archiviazione, ecc.)

## Best practices

- Utilizzare il livello di log appropriato per ciascun messaggio
- Utilizzare il livello LIFECYCLE per tracciare specificamente eventi relativi al ciclo di vita dei documenti
- Includere dettagli rilevanti nei log (ma evitare dati sensibili)
- Aggiungere il contesto appropriato per facilitare il debugging
- Per i log LIFECYCLE, includere sempre file_hash quando disponibile per consentire il tracciamento completo
- Utilizzare il client in modalità batch per migliorare le performance
- Consultare regolarmente la dashboard per monitorare lo stato del sistema