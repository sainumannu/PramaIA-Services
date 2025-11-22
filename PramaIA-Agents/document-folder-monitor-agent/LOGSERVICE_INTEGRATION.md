# Integrazione di PDF Monitoring Agent con LogService

## Panoramica
Questo documento descrive l'integrazione del PDF Monitoring Agent con il sistema centralizzato di logging PramaIA LogService. Questa integrazione permette di:

1. Inviare log strutturati al servizio centralizzato
2. Mantenere la compatibilità con il logging locale esistente
3. Visualizzare i log dell'agente nella dashboard unificata di LogService

## Configurazione

### File di configurazione

Utilizza il file `.env` per configurare la connessione al LogService:

```
# Configurazione per PramaIA LogService
PRAMAIALOG_ENABLED=true
PRAMAIALOG_HOST=http://localhost:8081
PRAMAIALOG_API_KEY=pdf-monitor-agent-key
```

Parametri:
- `PRAMAIALOG_ENABLED`: Abilita/disabilita l'integrazione (true/false)
- `PRAMAIALOG_HOST`: URL del servizio LogService
- `PRAMAIALOG_API_KEY`: Chiave API per l'autenticazione con LogService

### Installazione dei prerequisiti

Aggiungi il client PramaIALogger alle dipendenze:

```bash
pip install -e ../PramaIA-LogService/clients/python/
```

Oppure utilizza il file `requirements.txt` aggiornato:

```bash
pip install -r requirements.txt
```

## Utilizzo

### API di logging

Il nuovo modulo `logger.py` fornisce le seguenti funzioni:

```python
# Importazione
from .logger import info, warning, error, debug, flush, close

# Esempi di utilizzo
info("Messaggio informativo")
warning("Messaggio di avviso")
error("Errore critico", details={"error_code": 500})
debug("Messaggio di debug", details={"context": "test"})

# Prima della chiusura dell'applicazione
flush()  # Forza l'invio di tutti i log in coda
close()  # Chiude il logger
```

### Dettagli strutturati

È possibile aggiungere dettagli strutturati ai log:

```python
info(
    "File processato con successo",
    details={
        "file_name": "documento.pdf",
        "file_size": 1024,
        "process_time": 0.5
    }
)
```

### Contesto delle operazioni

È possibile aggiungere contesto alle operazioni:

```python
error(
    "Errore durante l'elaborazione",
    details={"error": str(e)},
    context={"operation": "file_upload", "user_id": "admin"}
)
```

## Visualizzazione dei Log

I log inviati possono essere visualizzati nella dashboard web di LogService:

- URL: http://localhost:8081/dashboard/logservice
- Progetto: PramaIA-Agents
- Modulo: pdf-folder-monitor-agent

## Risoluzione dei problemi

Se i log non appaiono nel LogService:

1. Verifica che `PRAMAIALOG_ENABLED` sia impostato su `true`
2. Controlla che il servizio LogService sia in esecuzione all'URL specificato
3. Verifica che l'API key sia corretta
4. Controlla eventuali errori nel log locale dell'agente

## Note tecniche

- Il sistema mantiene anche il logging locale standard, quindi i messaggi appariranno sia nella console che nel LogService
- I log vengono bufferizzati e inviati in batch per migliorare le prestazioni
- In caso di errori di connessione, i log vengono mantenuti in memoria e ritentati automaticamente
