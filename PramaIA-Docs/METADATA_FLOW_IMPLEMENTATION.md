# Flusso di Metadati nel Sistema PramaIA

## Panoramica
La modifica implementa un flusso completo di metadati dai sorgenti (agent/monitor) attraverso il backend fino ai nodi PDK per l'elaborazione consapevole del contesto.

## Architettura del Flusso

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. AGENT/FOLDER MONITOR                                          │
│    - Rileva file nel filesystem                                  │
│    - Estrae metadati originali (author, title, dates, etc.)      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. ENDPOINT: POST /api/document-monitor/upload/                  │
│    - Riceve file come multipart/form-data                        │
│    - Riceve metadati come JSON: UploadFileMetadata               │
│      {                                                            │
│        "client_id": "folder-monitor-agent-1",                    │
│        "original_path": "/mnt/documents/reports/Q4_2025.pdf",    │
│        "source": "agent",                                        │
│        "metadata": {                                             │
│          "filename_original": "Q4_2025.pdf",                     │
│          "file_size_original": 2048000,                          │
│          "date_created": "2025-01-15T09:30:00Z",               │
│          "date_modified": "2025-01-16T14:45:30Z",              │
│          "author": "John Doe",                                   │
│          "title": "Q4 2025 Financial Report",                    │
│          "subject": "Financial Analysis",                        │
│          "keywords": ["finance", "report", "q4", "2025"],       │
│          "language": "en",                                       │
│          "creation_tool": "MS Office 365",                       │
│          "tags": ["important", "financial"],                     │
│          "custom_fields": {                                      │
│            "department": "Finance",                              │
│            "project_code": "FIN-2025-Q4"                         │
│          }                                                        │
│        }                                                          │
│      }                                                            │
│                                                                  │
│ - Estrae DocumentMetadata dall'oggetto JSON                      │
│ - Log: "Metadati documento: author=..., title=..."              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ROUTER: backend/routers/document_monitor_router.py            │
│    - Classe DocumentMetadata (Pydantic model)                    │
│      • filename_original, file_size_original                     │
│      • date_created, date_modified                               │
│      • author, title, subject, keywords, language                │
│      • creation_tool, tags, custom_fields                        │
│                                                                  │
│    - Classe UploadFileMetadata (Pydantic model)                  │
│      • client_id: str                                            │
│      • original_path: str                                        │
│      • metadata: Optional[DocumentMetadata]                      │
│      • source: str                                               │
│                                                                  │
│    - Endpoint receive_document_from_plugin():                    │
│      • Decodifica JSON metadata                                  │
│      • Estrae DocumentMetadata object                            │
│      • Passa a process_document_with_pdk()                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. SERVICE: backend/services/document_monitor_service.py         │
│    Funzione: async def process_document_with_pdk()               │
│                                                                  │
│    Firma aggiornata:                                             │
│    async def process_document_with_pdk(                          │
│        file_bytes: bytes,                                        │
│        filename: str,                                            │
│        client_id: str = "system",                                │
│        original_path: str = "",                                  │
│        document_metadata: dict = None  ← NUOVO                   │
│    )                                                             │
│                                                                  │
│    Logica:                                                       │
│    1. Log metadati ricevuti se disponibili                       │
│       logger.info("Metadati documento ricevuti:", {              │
│         "author", "title", "keywords", "tags", ...              │
│       })                                                         │
│                                                                  │
│    2. Costruisci metadata_payload di base:                       │
│       {                                                          │
│         "source": "document-monitor-plugin",                     │
│         "user_id": client_id,                                    │
│         "filename": filename,                                    │
│         "original_path": original_path,                          │
│         "upload_timestamp": datetime.now()                       │
│       }                                                          │
│                                                                  │
│    3. Unisci con document_metadata se disponibile:              │
│       metadata_payload.update({                                  │
│         "author": document_metadata["author"],                   │
│         "title": document_metadata["title"],                     │
│         "subject": document_metadata["subject"],                 │
│         "keywords": document_metadata["keywords"],               │
│         "language": document_metadata["language"],               │
│         "creation_tool": document_metadata["creation_tool"],     │
│         "tags": document_metadata["tags"],                       │
│         "custom_fields": document_metadata["custom_fields"],     │
│         "date_created": document_metadata["date_created"],       │
│         "date_modified": document_metadata["date_modified"]      │
│       })                                                         │
│                                                                  │
│    4. Costruisci payload PDK con metadati:                       │
│       payload = {                                                │
│         "nodeId": "document_input_node",                         │
│         "inputs": {},                                            │
│         "config": {                                              │
│           "file_path": normalized_path,                          │
│           "extract_text": True,                                  │
│           "extract_images": False,                               │
│           "pages": "all",                                        │
│           "metadata": metadata_payload  ← METADATI COMPLETI      │
│         }                                                        │
│       }                                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. PDK SERVER: POST /plugins/document-semantic-complete/execute  │
│    - Riceve payload con config.metadata pieno di dati            │
│    - document_input_node accede ai metadati via config.metadata  │
│    - Passa metadati ai nodi successivi (pdf_text_extractor,     │
│      text_chunker, vector_store_operations)                      │
│    - I nodi possono usare metadata per:                          │
│      • Enrichment dei chunk (aggiungere author, title ai chunk)  │
│      • Filtering (processare solo doc specifici)                 │
│      • Prioritization (prioritizzare doc importanti)             │
│      • Tagging (applicare tag al vectorstore)                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE BACK TO ROUTER                                       │
│    - Ritorna risultato dal PDK con document_id                   │
│    - Service enrichisce risposta con metadati originali          │
│                                                                  │
│    Risposta di successo:                                         │
│    {                                                             │
│      "status": "success",                                        │
│      "document_id": "uuid-...",                                  │
│      "workflow_result": {...},                                   │
│      "document_metadata": {                                      │
│        "author": "John Doe",                                     │
│        "title": "Q4 2025 Financial Report",                      │
│        "tags": ["important", "financial"],                       │
│        ...metadati completi...                                   │
│      }                                                           │
│    }                                                             │
│                                                                  │
│    Risposta duplicato:                                           │
│    {                                                             │
│      "status": "duplicate",                                      │
│      "document_id": "uuid-original",                             │
│      "duplicate_type": "content_duplicate",                      │
│      "document_metadata": {...}                                  │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. CLIENT RESPONSE                                               │
│    - Client/Agent riceve confirmation di upload                  │
│    - Contiene document_id e metadati riconfermati                │
│    - Può usare document_id per query/recupero successivo         │
└─────────────────────────────────────────────────────────────────┘
```

## Componenti Modificati

### 1. backend/routers/document_monitor_router.py
**Nuove classi Pydantic:**

```python
class DocumentMetadata(BaseModel):
    # File system metadata
    filename_original: Optional[str] = None
    file_size_original: Optional[int] = None
    date_created: Optional[str] = None  # ISO format
    date_modified: Optional[str] = None  # ISO format
    
    # Document metadata
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[list] = None
    language: Optional[str] = None
    creation_tool: Optional[str] = None
    
    # Custom metadata
    tags: Optional[list] = None
    custom_fields: Optional[dict] = None

class UploadFileMetadata(BaseModel):
    client_id: Optional[str] = "system"
    original_path: Optional[str] = ""
    metadata: Optional[DocumentMetadata] = None
    source: Optional[str] = "agent"
```

**Endpoint modificato:**
- `/api/document-monitor/upload/` (POST)
- Accetta `metadata: UploadFileMetadata` come parametro JSON
- Estrae `document_metadata` e passa a `process_document_with_pdk()`

### 2. backend/services/document_monitor_service.py
**Firma della funzione aggiornata:**

```python
async def process_document_with_pdk(
    file_bytes: bytes, 
    filename: str, 
    client_id: str = "system", 
    original_path: str = "",
    document_metadata: dict = None  # ← NUOVO PARAMETRO
)
```

**Modifiche alla logica:**

1. **Logging metadati ricevuti** (riga ~350):
   ```python
   if document_metadata:
       logger.info("Metadati documento ricevuti:", {
           "author": document_metadata.get("author"),
           "title": document_metadata.get("title"),
           # ... altri campi
       })
   ```

2. **Costruzione payload arricchito** (riga ~430):
   ```python
   metadata_payload = {
       "source": "document-monitor-plugin",
       "user_id": client_id,
       "filename": filename,
       "original_path": original_path,
       "upload_timestamp": datetime.now().isoformat()
   }
   
   if document_metadata:
       metadata_payload.update({
           "author": document_metadata.get("author"),
           "title": document_metadata.get("title"),
           "subject": document_metadata.get("subject"),
           "keywords": document_metadata.get("keywords"),
           "language": document_metadata.get("language"),
           "creation_tool": document_metadata.get("creation_tool"),
           "tags": document_metadata.get("tags"),
           "custom_fields": document_metadata.get("custom_fields"),
           "filename_original": document_metadata.get("filename_original"),
           "file_size_original": document_metadata.get("file_size_original"),
           "date_created": document_metadata.get("date_created"),
           "date_modified": document_metadata.get("date_modified")
       })
   ```

3. **Inclusione nel payload PDK** (riga ~460):
   ```python
   payload = {
       "nodeId": "document_input_node",
       "inputs": {},
       "config": {
           "file_path": normalized_path,
           "extract_text": True,
           "extract_images": False,
           "pages": "all",
           "metadata": metadata_payload  # ← Metadati pieno di dati
       }
   }
   ```

4. **Enrichment della risposta** (riga ~590):
   ```python
   return {
       "status": "success",
       "message": f"Documento '{filename}' ricevuto e processato dal workflow PDK.",
       "document_id": document_id,
       "workflow_result": result,
       "is_duplicate": False,
       "client_id": client_id,
       "original_path": original_path,
       "document_metadata": metadata_payload if document_metadata else None  # ← NUOVO
   }
   ```

## Test Script
**File:** `scripts/testing/test_agent_upload_with_metadata.py`

Simula il flusso completo:
1. Crea PDF di test
2. Costruisce `UploadFileMetadata` con metadati completi
3. Carica via `/api/document-monitor/upload/`
4. Verifica che metadati siano nella risposta
5. Log tutto in `logs/test_agent_upload_metadata.log`

**Uso:**
```bash
cd c:\PramaIA
python scripts/testing/test_agent_upload_with_metadata.py
```

## Vantaggi di questa Implementazione

### 1. **Preservazione dei Metadati**
- I metadati originali non vengono persi quando il file viene salvato su disco
- Disponibili per il PDK e per interrogazioni future

### 2. **Consapevolezza del Contesto nei PDK Nodes**
- I nodi PDK ricevono metadati completi nel `config.metadata`
- Possono prendere decisioni basate su author, title, tags, etc.
- Esempio: un nodo potrebbe applicare processing diverso per documenti "confidenziali"

### 3. **Tracciabilità**
- Source agent identificato (`client_id`)
- Percorso originale nel filesystem remoto (`original_path`)
- Data di creazione e modifica originali

### 4. **Extensibilità**
- Custom fields permettono di aggiungere metadati specifici per dominio
- I nodi PDK possono consumare questi campi custom

### 5. **Debugging Facilitato**
- Log espliciti di metadati ricevuti
- Risposta include metadati per conferma

## Prossimi Passi (Opzionali)

### 1. Persistenza nel Database
- Aggiungere tabella `document_metadata` per archiviare metadati
- Permettere query/search per author, title, tags, etc.

### 2. Estrazione Automatica Metadati
- Integrare PyPDF2 per estrarre metadati da PDF
- Integrare python-docx per DOCX
- Merge con metadati forniti (client fornito > estratto da file)

### 3. Nodi PDK Consapevoli dei Metadati
- Modificare `pdf_text_extractor` per includere metadata nei chunk
- Modificare `vector_store_operations` per indicizzare metadati
- Creare nodo "metadata_enrichment" dedicato

### 4. API Query per Metadati
- `GET /api/documents/{id}/metadata` - Recupera metadati documento
- `GET /api/documents/search?author=...&tags=...` - Search per metadati

## Conclusione

Questo flusso implementa una **catena di preservazione dei metadati** che:
1. Cattura metadati dal sorgente (agent)
2. Li preserva durante il trasporto
3. Li passa al workflow PDK
4. Li rende disponibili per elaborazione consapevole del contesto
5. Li ritorna al client come conferma

Questo è il fondamento per future implementazioni di RAG consapevole dei metadati, search avanzato, e orchestrazione intelligente dei workflow.
