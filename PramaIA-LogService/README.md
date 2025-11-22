# PramaIA LogService

Servizio centralizzato di logging per l'ecosistema PramaIA.

## Descrizione

PramaIA LogService è un servizio dedicato alla gestione centralizzata dei log per tutti i progetti dell'ecosistema PramaIA. Fornisce API REST per la registrazione dei log, un sistema di archiviazione strutturato e un'interfaccia web per la visualizzazione e la ricerca nei log.

## Caratteristiche

- **API REST** per l'invio dei log da qualsiasi servizio
- **Categorizzazione** dei log per progetto, modulo e livello
- **Rotazione automatica** dei file di log
import os
import requests
import uuid
from datetime import datetime

# Configurazione (leggere da variabili d'ambiente o .env)
# Preferito: BACKEND_URL (es. http://127.0.0.1:8081)
# Alternativa compatibile: PRAMAIALOG_HOST + PRAMAIALOG_PORT
backend = os.getenv('BACKEND_URL') or os.getenv('PRAMAIALOG_HOST') or 'http://localhost:8081'
port = os.getenv('PRAMAIALOG_PORT')
if port and ':' not in backend.split('//')[-1]:
    backend = f"{backend.rstrip('/')}:{port}"

LOG_SERVICE_URL = f"{backend}/api/logs"
API_KEY = os.getenv('PRAMAIA_API_KEY', 'your_api_key_here')

def send_log(message, level="info", module="example", details=None, context=None):
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "project": "PramaIAServer",
        "level": level,
        "module": module,
        "message": message,
        "details": details or {},
        "context": context or {}
    }
    response = requests.post(
        LOG_SERVICE_URL,
        json=log_entry,
        headers={"X-API-Key": API_KEY}
    )
    return response.status_code == 201
```

## Integrazione

Il servizio può essere integrato con:
- PramaIAServer
- PramaIA-PDK
- PramaIA-Agents
- PramaIA-Plugins

### Esempio di integrazione

```python
import requests
import uuid
from datetime import datetime

# Configurazione
LOG_SERVICE_URL = "http://localhost:8081/api/logs"
API_KEY = "your_api_key_here"

# Funzione per inviare un log
def send_log(message, level="info", module="example", details=None, context=None):
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "project": "PramaIAServer",
        "level": level,
        "module": module,
        "message": message,
        "details": details or {},
        "context": context or {}
    }
    
    response = requests.post(
        LOG_SERVICE_URL,
        json=log_entry,
        headers={"X-API-Key": API_KEY}
    )
    
    return response.status_code == 201
```

## Requisiti

- Python 3.9+
- FastAPI
- SQLite (per la configurazione e i metadati)
- HTML/CSS/JavaScript per l'interfaccia web

## Configurazione

La configurazione del servizio è gestita tramite file di configurazione e può essere modificata tramite l'interfaccia web. Le impostazioni includono:

- Livelli di log da registrare
- Periodo di retention dei log
- Dimensione massima dei file di log
- Configurazione dell'autenticazione
- Porte e indirizzi per le API
- Impostazioni di compressione dei log vecchi

## Avvio del servizio

Per avviare il servizio:

```bash
cd PramaIA-LogService
python main.py
```

Il server sarà accessibile all'indirizzo `http://localhost:8081`.

### Opzioni di avvio

- `--port <numero>`: Specifica una porta diversa (default: 8081)
- `--host <indirizzo>`: Specifica l'indirizzo su cui ascoltare (default: 127.0.0.1)
- `--reload`: Riavvia automaticamente il server quando il codice cambia (utile durante lo sviluppo)

## Documentazione aggiuntiva

Per una documentazione più dettagliata, consultare:

- [Documentazione completa](docs/LOGSERVICE_DOCUMENTAZIONE.md)
- [Guida alla risoluzione del problema "undefined"](docs/RISOLUZIONE_PROBLEMA_UNDEFINED.md)
