# Script di gestione workflow PramaIA

Questa cartella contiene tutti gli strumenti Python utili per la gestione, verifica, esportazione e documentazione dei workflow nel sistema PramaIA.


## Elenco script disponibili

- **import_vectorstore_workflow.py**: importa un workflow (in formato JSON) nel database PramaIA
- **verify_vectorstore_workflow.py**: verifica che il workflow sia stato importato correttamente (conta nodi, connessioni, tipi)
- **inspect_db_workflows.py**: ispeziona la struttura del database e mostra i workflow presenti
- **export_workflows_json.py**: esporta tutti i workflow attivi in formato JSON
- **generate_workflow_docs.py**: genera documentazione Markdown per i workflow attivi
- **check_table_structure.py**: mostra la struttura delle tabelle principali e correlate del database
- **check_vectorstore_workflow.py**: verifica la presenza e la struttura del workflow vectorstore nel database PDK
- **insert_workflows_simple.py**: importa tutti i workflow dalla directory in modo semplice
- **insert_optimized_workflows.py**: importa i workflow con verifica hash e aggiornamento intelligente
- **list_workflows.py**: elenca tutti i workflow presenti nel database e mostra i trigger associati


## Utilizzo rapido

- Importa un workflow: `python scripts/import_vectorstore_workflow.py`
- Verifica importazione: `python scripts/verify_vectorstore_workflow.py`
- Ispeziona database: `python scripts/inspect_db_workflows.py`
- Esporta workflow: `python scripts/export_workflows_json.py`
- Genera documentazione: `python scripts/generate_workflow_docs.py`
- Mostra struttura tabelle: `python scripts/check_table_structure.py`
- Verifica workflow vectorstore: `python scripts/check_vectorstore_workflow.py`
- Importazione semplice: `python scripts/insert_workflows_simple.py`
- Importazione ottimizzata: `python scripts/insert_optimized_workflows.py`
- Elenco workflow e trigger: `python scripts/list_workflows.py`

## Note
- Gli script sono già pronti all'uso e non vanno duplicati.
- Aggiorna questo README se aggiungi nuovi strumenti.
- La posizione del database viene rilevata automaticamente dagli script.

---
Ultimo aggiornamento: 03/09/2025
