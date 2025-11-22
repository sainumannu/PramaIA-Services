# Gestione Nuovi Documenti PDF

**workflow_id:** `pdf_document_add_workflow`

Elabora nuovi documenti PDF aggiunti alle cartelle monitorate

## Metadata

- **id**: `17`
- **created_by**: `system`
- **created_at**: `2025-08-17T22:45:10.745290`
- **updated_at**: `2025-08-17T22:45:10.745315`
- **is_active**: `1`
- **is_public**: `1`
- **category**: `pdf_monitoring`
- **tags**: `["pdf", "document", "ingest", "monitoring"]`

## Triggers / Event sources

- Trigger:
  - **id**: `4aa1b60c-19ab-4adf-a057-5525f9ed0587`
  - **name**: `Trigger Aggiunta Documenti PDF`
  - **event_type**: `pdf_file_added`
  - **source**: `pdf-monitor-source`
  - **workflow_id**: `pdf_document_add_workflow`
  - **conditions**: `{"fileSize": {"operator": "greaterThan", "value": 0}}`
  - **active**: `1`
  - **created_at**: `2025-08-17T22:49:20.346987`
  - **updated_at**: `2025-08-17T22:49:20.347015`
  - **target_node_id**: `pdf_event_input`

## Nodes

### Input Evento PDF — `pdf_event_input`
- **type**: `event_input_node`
- Riceve l'evento di un nuovo documento PDF

```json
{
  "requiresInput": false,
  "outputPorts": [
    "event_data"
  ]
}
```

### Estrai Percorso File — `extract_file_path`
- **type**: `json_processor`
- Estrae il percorso del file dall'evento

```json
{
  "operation": "extract",
  "extraction_path": "file_path",
  "default_value": ""
}
```

### Parser PDF — `file_parser`
- **type**: `file_parsing`
- Estrae testo e metadati dal documento PDF

```json
{
  "extract_text": true,
  "extract_metadata": true,
  "extract_images": false,
  "ocr_enabled": false
}
```

### Processor Metadati — `metadata_processor`
- **type**: `metadata_manager`
- Processa e normalizza i metadati

```json
{
  "operation": "process",
  "extract_standard_fields": true,
  "normalize_dates": true,
  "generate_id": true
}
```

### Processor Documento — `document_processor`
- **type**: `document_processor`
- Elabora il testo del documento

```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "extract_headings": true,
  "normalize_text": true
}
```

### Aggiungi a Vector Store — `vector_store_add`
- **type**: `vector_store_operations`
- Salva documento e metadati nel vector store

```json
{
  "operation": "add",
  "collection_name": "pdf_documents",
  "index_metadata": true,
  "batch_size": 10
}
```

### Logger Eventi — `event_logger`
- **type**: `event_logger`
- Registra l'evento di aggiunta documento

```json
{
  "event_type": "document_added",
  "log_level": "INFO",
  "include_metadata": true
}
```

## Connections (edges)

- `pdf_event_input`:event_data -> `extract_file_path`:data
- `extract_file_path`:result -> `file_parser`:file_path
- `file_parser`:metadata -> `metadata_processor`:metadata
- `file_parser`:text -> `document_processor`:text
- `metadata_processor`:processed_metadata -> `vector_store_add`:metadata
- `document_processor`:processed_text -> `vector_store_add`:document
- `pdf_event_input`:event_data -> `vector_store_add`:source_event
- `vector_store_add`:result -> `event_logger`:event_data

## Operational notes

- Source events: typically produced by the PDF monitor event-source (see event-sources/pdf-monitor-event-source).
- Vector store collection: `pdf_documents` is used by these workflows for storage and retrieval.

---
_Generated on 2025-09-01T14:27:47.532305Z_
