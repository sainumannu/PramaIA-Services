# Document Monitor Event Source

Event Source PDK per il monitoraggio di cartelle documenti integrato nel sistema PramaIA PDK.

## Descrizione

Questo Event Source monitora una cartella specificata per modifiche ai file documento e emette eventi quando:
- Un nuovo documento viene aggiunto
- Un documento esistente viene modificato  
- Un documento viene eliminato

## Configurazione

```json
{
  "monitor_path": "/path/to/documents/folder",
  "recursive": true,
  "file_extensions": [".pdf", ".doc", ".docx", ".odt", ".txt", ".xls", ".xlsx", ".ods"],
  "ignore_hidden": true,
  "debounce_time": 2,
  "max_file_size": 100
}
```

### Parametri di configurazione:

- **monitor_path** (richiesto): Percorso assoluto della cartella da monitorare
- **recursive** (default: true): Se monitorare anche le sottocartelle
- **file_extensions** (default: [".pdf", ".doc", ".docx", ".odt", ".txt", ".xls", ".xlsx", ".ods"]): Estensioni file da monitorare
- **ignore_hidden** (default: true): Se ignorare i file nascosti (che iniziano con .)
- **debounce_time** (default: 2): Tempo in secondi per evitare eventi duplicati
- **max_file_size** (default: 100): Dimensione massima file in MB (0 = nessun limite)

## Eventi Emessi

### document_file_added
Emesso quando un nuovo documento viene aggiunto alla cartella monitorata.

**Outputs:**
- `file_path`: Percorso assoluto del file
- `file_name`: Nome del file
- `file_size`: Dimensione in bytes
- `detected_at`: Timestamp ISO di rilevamento
- `document_id`: ID univoco del documento

### document_file_modified  
Emesso quando un documento esistente viene modificato.

**Outputs:**
- `file_path`: Percorso assoluto del file
- `file_name`: Nome del file
- `file_size`: Nuova dimensione in bytes
- `modified_at`: Timestamp ISO di modifica
- `document_id`: ID del documento

### document_file_deleted
Emesso quando un documento viene eliminato.

**Outputs:**
- `file_path`: Percorso del file eliminato
- `file_name`: Nome del file eliminato
- `deleted_at`: Timestamp ISO di eliminazione
- `document_id`: ID del documento eliminato

## Utilizzo

Questo Event Source è progettato per essere utilizzato tramite il PDK Server API:

```bash
# Avvia l'event source
curl -X POST http://localhost:3001/api/event-sources/document-monitor-event-source/start \
  -H "Content-Type: application/json" \
  -d '{"config": {"monitor_path": "/path/to/documents/folder"}}'

# Ottieni lo status
curl http://localhost:3001/api/event-sources/document-monitor-event-source/status

# Ferma l'event source  
curl -X POST http://localhost:3001/api/event-sources/document-monitor-event-source/stop
```

## Dipendenze

- Python 3.7+
- watchdog>=3.0.0
- asyncio (built-in)
- pathlib (built-in)

## Integrazione con Workflow

Gli eventi emessi da questo Event Source possono essere utilizzati come trigger per workflow PramaIA che processano automaticamente i documenti rilevati.
