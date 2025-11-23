# Quick Start: Upload Documento con Metadati

## Endpoint
```
POST /api/document-monitor/upload/
```

## Content-Type
Multipart form-data (come file upload standard)

## Parametri

### 1. File (multipart)
```
file: <binary PDF content>
```

### 2. Metadata (JSON form-data)
```
metadata: {
  "client_id": string (optional, default: "system"),
  "original_path": string (optional, default: ""),
  "source": string (optional, default: "agent"),
  "metadata": {
    "filename_original": string,
    "file_size_original": integer,
    "date_created": string (ISO 8601),
    "date_modified": string (ISO 8601),
    "author": string,
    "title": string,
    "subject": string,
    "keywords": array of strings,
    "language": string (e.g., "en", "it"),
    "creation_tool": string,
    "tags": array of strings,
    "custom_fields": object
  }
}
```

## Esempi

### Con cURL
```bash
curl -X POST http://localhost:8000/api/document-monitor/upload/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F 'metadata={"client_id":"agent-1","original_path":"/docs/file.pdf","source":"agent","metadata":{"author":"John Doe","title":"Report Q4","keywords":["finance","report"]}}'
```

### Con Python Requests
```python
import requests
import json

url = "http://localhost:8000/api/document-monitor/upload/"
token = "YOUR_JWT_TOKEN"

metadata = {
    "client_id": "folder-monitor-1",
    "original_path": "/mnt/documents/report.pdf",
    "source": "agent",
    "metadata": {
        "filename_original": "report.pdf",
        "file_size_original": 512000,
        "date_created": "2025-01-15T09:30:00Z",
        "date_modified": "2025-01-16T14:45:30Z",
        "author": "John Doe",
        "title": "Q4 2025 Financial Report",
        "keywords": ["finance", "q4", "2025"],
        "tags": ["important", "client"],
        "custom_fields": {"department": "Finance"}
    }
}

with open("document.pdf", "rb") as f:
    files = {"file": ("document.pdf", f, "application/pdf")}
    data = {"metadata": json.dumps(metadata)}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(url, files=files, data=data, headers=headers)
    print(response.json())
```

## Risposta di Successo (Status 200)

```json
{
  "status": "success",
  "message": "Documento 'report.pdf' ricevuto e processato dal workflow PDK.",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_result": {
    "status": "completed",
    "result": {...}
  },
  "is_duplicate": false,
  "client_id": "folder-monitor-1",
  "original_path": "/mnt/documents/report.pdf",
  "document_metadata": {
    "source": "document-monitor-plugin",
    "user_id": "folder-monitor-1",
    "filename": "report.pdf",
    "original_path": "/mnt/documents/report.pdf",
    "upload_timestamp": "2025-01-17T10:30:45.123456Z",
    "author": "John Doe",
    "title": "Q4 2025 Financial Report",
    "keywords": ["finance", "q4", "2025"],
    "tags": ["important", "client"],
    "custom_fields": {"department": "Finance"},
    "filename_original": "report.pdf",
    "file_size_original": 512000,
    "date_created": "2025-01-15T09:30:00Z",
    "date_modified": "2025-01-16T14:45:30Z"
  }
}
```

### Campi nella Risposta

| Campo | Descrizione |
|-------|-------------|
| `status` | "success" se ok, "error" o "duplicate" altrimenti |
| `message` | Messaggio descrittivo |
| `document_id` | UUID del documento processato |
| `workflow_result` | Risultato del workflow PDK |
| `is_duplicate` | true se documento è duplicato |
| `client_id` | ID del client che ha inviato il file |
| `original_path` | Percorso originale nel filesystem del client |
| `document_metadata` | **NUOVO** - Metadati completi che il PDK ha ricevuto |

## Risposta Duplicato (Status 200)

```json
{
  "status": "duplicate",
  "message": "Il documento 'report.pdf' è un duplicato di un file esistente.",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_duplicate": true,
  "duplicate_type": "content_duplicate",
  "duplicate_detection_method": "md5_hash",
  "client_id": "folder-monitor-1",
  "original_path": "/mnt/documents/report.pdf",
  "document_metadata": {
    "author": "John Doe",
    "title": "Q4 2025 Financial Report",
    ...
  }
}
```

## Errore (Status 200 o 400)

```json
{
  "status": "error",
  "message": "Errore durante l'elaborazione del documento: ...",
  "is_duplicate": false,
  "client_id": "folder-monitor-1",
  "original_path": "/mnt/documents/report.pdf"
}
```

## Campi Metadati Spiegati

### File System
- **filename_original**: Nome originale del file ("report.pdf")
- **file_size_original**: Dimensione originale in byte (512000)
- **date_created**: ISO 8601 timestamp di creazione ("2025-01-15T09:30:00Z")
- **date_modified**: ISO 8601 timestamp ultima modifica ("2025-01-16T14:45:30Z")

### Documento
- **author**: Autore del documento ("John Doe")
- **title**: Titolo ("Q4 2025 Financial Report")
- **subject**: Soggetto/argomento ("Financial Analysis")
- **keywords**: Array di parole chiave ["finance", "report", "q4"]
- **language**: Codice lingua ISO 639-1 ("en", "it", "fr")
- **creation_tool**: Software che ha creato il documento ("MS Office 365")

### Custom
- **tags**: Array di tag custom per categorizzazione ["important", "client"]
- **custom_fields**: Object con campi specifici per dominio
  ```json
  {
    "department": "Finance",
    "project_code": "FIN-2025-Q4",
    "review_status": "pending"
  }
  ```

## Flusso dei Dati

```
1. Client POST con metadata JSON
   ↓
2. Pydantic validation (DocumentMetadata parsing)
   ↓
3. Router estrae document_metadata
   ↓
4. Service riceve e loga: "Metadati documento ricevuti: author=..., title=..."
   ↓
5. Service merge in metadata_payload
   ↓
6. PDK riceve config.metadata pieno di dati
   ↓
7. Nodi PDK possono accedere ai metadati
   ↓
8. Risposta al client include document_metadata per conferma
```

## Note Importanti

### Validazione
- Tutti i campi metadata sono **opzionali**
- Se metadata non fornito, service usa defaults
- Pydantic validate tipo di ogni campo

### Logging
- Service loga che ha ricevuto metadati: "Metadati ricevuti: author=..., title=..."
- Log level INFO per tracking
- Utile per debug e audit trail

### Preservazione
- Metadati **NON** vanno persi durante il salvataggio del file
- Sono archiviati separatamente dal file binario
- Disponibili per query successive

### PDK Node Access
- I nodi PDK ricevono metadati in `config.metadata`
- Possono usarli per prendere decisioni (filtrare, arricchire, prioritizzare)
- Esempio: `pdf_text_extractor` potrebbe aggiungere author ai chunk

### Duplicati
- Se documento è duplicato, i metadati vengono comunque ritornati
- Document ID ritornato è quello dell'originale
- Flag `duplicate_type` specifica se "exact_duplicate" o "content_duplicate"

## Test Script

Esegui il test completo:
```bash
cd c:\PramaIA
python scripts/testing/test_agent_upload_with_metadata.py
```

Verifica flusso:
```bash
python scripts/testing/verify_metadata_flow.py
```

## Autenticazione

L'endpoint richiede autenticazione JWT:
```
Authorization: Bearer <JWT_TOKEN>
```

Per ottenere token:
```bash
curl -X POST http://localhost:8000/auth/token/local \
  -d "username=admin&password=admin"
```

## Supporto

Per problemi, controllare:
1. Backend log: `Backend FastAPI.txt`
2. Test log: `logs/test_agent_upload_metadata.log`
3. Verificare che backend sia online: `GET /health`
