# Workflow documentation

This folder contains generated documentation for workflows active in the runtime database. Files are generated from `workflows/exported_workflows.json` and the `workflow_triggers` table in the server DB.

To regenerate:
```
python scripts/generate_workflow_docs.py
```

- [Gestione Nuovi Documenti PDF](./pdf_document_add_workflow.md) — `pdf_document_add_workflow`
- [Gestione Documenti PDF Modificati](./pdf_document_modify_workflow.md) — `pdf_document_modify_workflow`
- [Gestione Documenti PDF Eliminati](./pdf_document_delete_workflow.md) — `pdf_document_delete_workflow`
- [Aggiornamento Metadati Documenti PDF](./pdf_metadata_update_workflow.md) — `pdf_metadata_update_workflow`