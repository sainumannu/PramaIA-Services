# Guida all'integrazione con PramaIAServer

## Introduzione

Questa guida descrive come integrare il client Python di PramaIA-LogService con PramaIAServer.

## Prerequisiti

- PramaIAServer installato e configurato
- PramaIA-LogService avviato e funzionante
- API key valida per PramaIAServer

## Installazione del client

1. Copia la directory `clients/python` dal repository PramaIA-LogService nella directory `utils` di PramaIAServer:

```powershell
Copy-Item -Path "C:\PramaIA\PramaIA-LogService\clients\python" -Destination "C:\PramaIA\PramaIAServer\backend\utils\pramaialog" -Recurse
```

2. Crea un file `__init__.py` nella directory `backend/utils/pramaialog`:

```python
from .pramaialog import PramaIALogger, LogLevel, LogProject, setup_logger
```

# Configurazione

Configura il logger nel file `backend/config/config.py` di PramaIAServer.
Si raccomanda di leggere l'URL del LogService da variabili d'ambiente o dal file `.env`.

Esempio:

```python
# Configurazione logging centralizzato
import os

backend = os.getenv('BACKEND_URL') or os.getenv('PRAMAIALOG_HOST') or 'http://localhost:8081'
port = os.getenv('PRAMAIALOG_PORT')
if port and ':' not in backend.split('//')[-1]:
    backend = f"{backend.rstrip('/')}:{port}"

LOGGING_SERVICE_HOST = backend
LOGGING_API_KEY = os.getenv('PRAMAIA_API_KEY', 'pramaiaserver_api_key_123456')
```

## Utilizzo

### Inizializzazione del logger

Crea un file `backend/utils/logging.py` per inizializzare il logger centralizzato:

```python
from backend.utils.pramaialog import PramaIALogger, LogLevel, LogProject
from backend.config.config import LOGGING_SERVICE_HOST, LOGGING_API_KEY

# Crea un'istanza globale del logger
pramaialog = PramaIALogger(
    api_key=LOGGING_API_KEY,
    project=LogProject.SERVER,
    module="pramaiaserver",
    host=LOGGING_SERVICE_HOST
)

# Funzione di convenienza per ottenere un logger per un modulo specifico
def get_logger(module_name):
    return PramaIALogger(
        api_key=LOGGING_API_KEY,
        project=LogProject.SERVER,
        module=module_name,
        host=LOGGING_SERVICE_HOST
    )
```

### Utilizzo nei vari moduli

Esempio di utilizzo nel file `backend/routers/workflow_triggers_router.py`:

```python
from backend.utils.logging import get_logger

# Crea un logger specifico per questo modulo
logger = get_logger("workflow_triggers_router")

@router.get("/workflow-inputs/{workflow_id}")
async def get_workflow_input_nodes(workflow_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Richiesta input nodes per workflow {workflow_id}")
        
        # Logica esistente...
        
        return input_nodes
    except Exception as e:
        logger.error(
            f"Errore durante il recupero degli input nodes per workflow {workflow_id}",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            context={
                "workflow_id": workflow_id
            }
        )
        raise HTTPException(status_code=500, detail=str(e))
```

## Conversione dei log esistenti

Per convertire i log esistenti che utilizzano il modulo `logging` standard di Python:

```python
import logging
from backend.utils.logging import get_logger

# Logger standard di Python
std_logger = logging.getLogger(__name__)

# Logger PramaIA
pramaia_logger = get_logger(__name__)

# Invece di:
std_logger.info("Messaggio informativo")
std_logger.error("Errore durante l'operazione", exc_info=True)

# Utilizzare:
pramaia_logger.info("Messaggio informativo")
pramaia_logger.error(
    "Errore durante l'operazione",
    details={"error_type": type(e).__name__, "error_message": str(e)},
    context={"operation": "nome_operazione"}
)
```

## Middleware di logging per FastAPI

Per registrare automaticamente le richieste HTTP, è possibile creare un middleware di logging:

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from backend.utils.logging import get_logger

logger = get_logger("http_middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Genera un ID univoco per la richiesta
        request_id = str(uuid.uuid4())
        
        # Log di inizio richiesta
        logger.info(
            f"Inizio richiesta {request.method} {request.url.path}",
            context={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None
            }
        )
        
        try:
            # Processa la richiesta
            response = await call_next(request)
            
            # Calcola il tempo di risposta
            process_time = time.time() - start_time
            
            # Log di fine richiesta
            logger.info(
                f"Fine richiesta {request.method} {request.url.path}",
                details={
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000)
                },
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            
            return response
        except Exception as e:
            # Log dell'errore
            logger.error(
                f"Errore durante la richiesta {request.method} {request.url.path}",
                details={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            raise
        
# Aggiungi il middleware all'app FastAPI
app = FastAPI()
app.add_middleware(LoggingMiddleware)
```

## Best practices

1. **Struttura dei log**: utilizzare campi `details` e `context` in modo coerente
2. **Livelli appropriati**: usare il livello di log corretto per ogni messaggio
3. **Informazioni utili**: includere informazioni rilevanti ma evitare dati sensibili
4. **Performance**: utilizzare il buffer del logger per ridurre le chiamate API
5. **Flush esplicito**: chiamare `logger.flush()` prima di terminare il processo per assicurarsi che tutti i log vengano inviati
