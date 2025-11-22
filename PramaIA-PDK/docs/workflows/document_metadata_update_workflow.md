# Aggiornamento Metadati Documenti PDF

**workflow_id:** `pdf_metadata_update_workflow`

Aggiorna i metadati dei documenti PDF senza modificare il contenuto

## Metadata

- **id**: `20`
- **created_by**: `system`
- **created_at**: `2025-08-17T22:45:10.754031`
- **updated_at**: `2025-08-17T22:45:10.754035`
- **is_active**: `1`
- **is_public**: `1`
- **category**: `pdf_monitoring`
- **tags**: `["pdf", "document", "metadata", "monitoring"]`

## Triggers / Event sources

- Trigger:
  - **id**: `105d9b86-7fb9-431e-840b-314e72412740`
  - **name**: `Trigger Aggiornamento Metadati`
  - **event_type**: `record_updated`
  - **source**: `database-triggers-event-source`
  - **workflow_id**: `pdf_metadata_update_workflow`
  - **conditions**: `{"table": {"operator": "equals", "value": "pdf_documents_metadata"}}`
  - **active**: `1`
  - **created_at**: `2025-08-17T22:49:20.348371`
  - **updated_at**: `2025-08-17T22:49:20.348377`
  - **target_node_id**: `metadata_event_input`

## Nodes

### Input Evento Metadati — `metadata_event_input`
- **type**: `event_input_node`
- Riceve l'evento di aggiornamento metadati

```json
{
  "requiresInput": false,
  "outputPorts": [
    "event_data"
  ]
}
```

### Estrai ID Documento — `extract_document_id`
- **type**: `json_processor`
- Estrae l'ID del documento dall'evento

```json
{
  "operation": "extract",
  "extraction_path": "document_id",
  "default_value": ""
}
```

### Estrai Aggiornamenti — `extract_metadata_updates`
- **type**: `json_processor`
- Estrae gli aggiornamenti ai metadati dall'evento

```json
{
  "operation": "extract",
  "extraction_path": "metadata_updates",
  "default_value": "{}"
}
```

### Recupera Documento — `get_document`
- **type**: `vector_store_operations`
- Recupera il documento dal vector store usando l'ID

```json
{
  "operation": "get",
  "collection_name": "pdf_documents",
  "query_by": "id"
}
```

### Unisci Metadati — `metadata_merge`
- **type**: `metadata_manager`
- Unisce i metadati esistenti con gli aggiornamenti

```json
{
  "operation": "merge",
  "preserve_id": true,
  "conflict_strategy": "override",
  "validate_schema": true,
  "update_timestamps": true
}
```

### Valida Metadati — `validate_metadata`
- **type**: `metadata_manager`
- Verifica che i metadati siano validi

```json
{
  "operation": "validate",
  "validation_level": "strict",
  "required_fields": [
    "document_id",
    "file_path"
  ],
  "sanitize_values": true
}
```

### Aggiorna Vector Store — `vector_store_update`
- **type**: `vector_store_operations`
- Aggiorna solo i metadati nel vector store

```json
{
  "operation": "update_metadata",
  "collection_name": "pdf_documents",
  "update_by_id": true,
  "reindex": false
}
```

### Logger Eventi — `event_logger`
- **type**: `event_logger`
- Registra l'evento di aggiornamento metadati

```json
{
  "event_type": "metadata_updated",
  "log_level": "INFO",
  "include_metadata": true,
  "track_changes": true
}
```

## Connections (edges)

- `metadata_event_input`:event_data -> `extract_document_id`:data
- `metadata_event_input`:event_data -> `extract_metadata_updates`:data
- `extract_document_id`:result -> `get_document`:query_params
- `get_document`:metadata -> `metadata_merge`:existing_metadata
- `extract_metadata_updates`:result -> `metadata_merge`:new_metadata
- `metadata_merge`:merged_metadata -> `validate_metadata`:metadata
- `validate_metadata`:validated_metadata -> `vector_store_update`:metadata
- `extract_document_id`:result -> `vector_store_update`:id
- `vector_store_update`:result -> `event_logger`:event_data
- `metadata_merge`:changes -> `event_logger`:changes

## Operational notes

- Source events: typically produced by the PDF monitor event-source (see event-sources/pdf-monitor-event-source).
- Vector store collection: `pdf_documents` is used by these workflows for storage and retrieval.

---
_Generated on 2025-09-01T14:27:47.534869Z_
