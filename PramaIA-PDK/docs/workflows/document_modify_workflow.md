# Gestione Documenti PDF Modificati

**workflow_id:** `pdf_document_modify_workflow`

Aggiorna documenti PDF modificati nelle cartelle monitorate

## Metadata

- **id**: `18`
- **created_by**: `system`
- **created_at**: `2025-08-17T22:45:10.748672`
- **updated_at**: `2025-08-17T22:45:10.748677`
- **is_active**: `1`
- **is_public**: `1`
- **category**: `pdf_monitoring`
- **tags**: `["pdf", "document", "update", "monitoring"]`

## Triggers / Event sources

- Trigger:
  - **id**: `40e3634e-b2a9-4cab-83d7-3e7d00b9fc5b`
  - **name**: `Trigger Modifica Documenti PDF`
  - **event_type**: `pdf_file_modified`
  - **source**: `pdf-monitor-source`
  - **workflow_id**: `pdf_document_modify_workflow`
  - **conditions**: `{"fileSize": {"operator": "greaterThan", "value": 0}}`
  - **active**: `1`
  - **created_at**: `2025-08-17T22:49:20.347984`
  - **updated_at**: `2025-08-17T22:49:20.347990`
  - **target_node_id**: `pdf_event_input`

## Nodes

### Input Evento PDF — `pdf_event_input`
- **type**: `event_input_node`
- Riceve l'evento di un documento PDF modificato

```json
{
  "requiresInput": false,
  "outputPorts": [
    "event_data"
  ]
}
```

### Estrai Info File — `extract_file_info`
- **type**: `json_processor`
- Estrae informazioni del file dall'evento

```json
{
  "operation": "transform",
  "transform_template": "{ \"file_path\": {{data.file_path}}, \"file_name\": {{data.file_name}}, \"file_size\": {{data.file_size}} }"
}
```

### Verifica Esistenza — `check_existing`
- **type**: `vector_store_operations`
- Verifica se il documento esiste già nel vector store

```json
{
  "operation": "get",
  "collection_name": "pdf_documents",
  "query_by": "file_path"
}
```

### Parser PDF — `file_parser`
- **type**: `file_parsing`
- Estrae testo e metadati dal documento PDF modificato

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
- Processa e aggiorna i metadati

```json
{
  "operation": "update",
  "preserve_id": true,
  "normalize_dates": true,
  "update_timestamps": true
}
```

### Processor Documento — `document_processor`
- **type**: `document_processor`
- Elabora il testo del documento aggiornato

```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "extract_headings": true,
  "normalize_text": true
}
```

### Aggiorna Vector Store — `vector_store_update`
- **type**: `vector_store_operations`
- Aggiorna documento e metadati nel vector store

```json
{
  "operation": "update",
  "collection_name": "pdf_documents",
  "update_by_id": true,
  "reindex": true
}
```

### Logger Eventi — `event_logger`
- **type**: `event_logger`
- Registra l'evento di aggiornamento documento

```json
{
  "event_type": "document_updated",
  "log_level": "INFO",
  "include_metadata": true,
  "track_changes": true
}
```

## Connections (edges)

- `pdf_event_input`:event_data -> `extract_file_info`:data
- `extract_file_info`:result -> `check_existing`:query_params
- `check_existing`:exists -> `file_parser`:continue_if_true
- `extract_file_info`:result -> `file_parser`:file_info
- `file_parser`:metadata -> `metadata_processor`:new_metadata
- `check_existing`:result -> `metadata_processor`:existing_metadata
- `file_parser`:text -> `document_processor`:text
- `metadata_processor`:processed_metadata -> `vector_store_update`:metadata
- `document_processor`:processed_text -> `vector_store_update`:document
- `check_existing`:document_id -> `vector_store_update`:id
- `vector_store_update`:result -> `event_logger`:event_data
- `metadata_processor`:changes -> `event_logger`:changes

## Operational notes

- Source events: typically produced by the PDF monitor event-source (see event-sources/pdf-monitor-event-source).
- Vector store collection: `pdf_documents` is used by these workflows for storage and retrieval.

---
_Generated on 2025-09-01T14:27:47.533265Z_
