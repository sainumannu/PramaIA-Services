# Gestione Documenti PDF Eliminati

**workflow_id:** `pdf_document_delete_workflow`

Gestisce la rimozione di documenti PDF dalle cartelle monitorate

## Metadata

- **id**: `19`
- **created_by**: `system`
- **created_at**: `2025-08-17T22:45:10.751777`
- **updated_at**: `2025-08-17T22:45:10.751785`
- **is_active**: `1`
- **is_public**: `1`
- **category**: `pdf_monitoring`
- **tags**: `["pdf", "document", "delete", "monitoring"]`

## Triggers / Event sources

- Trigger:
  - **id**: `a6248077-9391-48cf-a3d0-68e55c3f0867`
  - **name**: `Trigger Eliminazione Documenti PDF`
  - **event_type**: `pdf_file_deleted`
  - **source**: `pdf-monitor-source`
  - **workflow_id**: `pdf_document_delete_workflow`
  - **conditions**: `{}`
  - **active**: `1`
  - **created_at**: `2025-08-17T22:49:20.348173`
  - **updated_at**: `2025-08-17T22:49:20.348181`
  - **target_node_id**: `pdf_event_input`

## Nodes

### Input Evento PDF — `pdf_event_input`
- **type**: `event_input_node`
- Riceve l'evento di un documento PDF eliminato

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

### Verifica Esistenza — `check_existing`
- **type**: `vector_store_operations`
- Verifica se il documento esiste nel vector store

```json
{
  "operation": "get",
  "collection_name": "pdf_documents",
  "query_by": "file_path"
}
```

### Backup Metadati — `metadata_backup`
- **type**: `metadata_manager`
- Salva i metadati prima della rimozione

```json
{
  "operation": "export",
  "include_timestamps": true,
  "add_deletion_marker": true
}
```

### Rimuovi da Vector Store — `vector_store_delete`
- **type**: `vector_store_operations`
- Rimuove il documento dal vector store

```json
{
  "operation": "delete",
  "collection_name": "pdf_documents",
  "delete_by_id": true,
  "cascade_delete": true
}
```

### Logger Eventi — `event_logger`
- **type**: `event_logger`
- Registra l'evento di rimozione documento

```json
{
  "event_type": "document_deleted",
  "log_level": "INFO",
  "include_metadata": true
}
```

### Notifica Rimozione — `deletion_notifier`
- **type**: `http_request`
- Invia notifica della rimozione del documento

```json
{
  "method": "POST",
  "timeout": 30,
  "content_type": "application/json",
  "error_on_failure": false
}
```

## Connections (edges)

- `pdf_event_input`:event_data -> `extract_file_path`:data
- `extract_file_path`:result -> `check_existing`:query_params
- `check_existing`:result -> `metadata_backup`:metadata
- `metadata_backup`:exported_metadata -> `vector_store_delete`:metadata_backup
- `check_existing`:document_id -> `vector_store_delete`:id
- `vector_store_delete`:result -> `event_logger`:event_data
- `metadata_backup`:exported_metadata -> `event_logger`:metadata
- `event_logger`:logged_event -> `deletion_notifier`:body
- `pdf_event_input`:event_data -> `deletion_notifier`:url_params

## Operational notes

- Source events: typically produced by the PDF monitor event-source (see event-sources/pdf-monitor-event-source).
- Vector store collection: `pdf_documents` is used by these workflows for storage and retrieval.

---
_Generated on 2025-09-01T14:27:47.534124Z_
