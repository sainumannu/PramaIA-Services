# PDF Monitor Plugin per PramaIA-PDK

Plugin per il monitoraggio e la gestione dei documenti PDF all'interno del sistema PramaIA-PDK.

## Nodi disponibili

### MetadataManager

Gestisce i metadati dei documenti con funzionalità di aggiornamento, unione, validazione ed estrazione.

### EventLogger

Registra eventi e attività del sistema di monitoraggio PDF nel database eventi.

### FileParsing

Esegue il parsing di file PDF e ne estrae testo, metadati e altre informazioni.

### DocumentProcessor

Estrae e processa testo da documenti PDF, con supporto per chunking e arricchimento metadati.

### VectorStoreOperations

Esegue operazioni CRUD sul vectorstore (add, get, update, delete, query).

## Installazione

Per installare il plugin, assicurarsi che i file siano nella directory `plugins/pdf-monitor-plugin` del PDK.

Installare le dipendenze richieste:

```bash
pip install -r requirements.txt
```

## Requisiti

- PyMuPDF (fitz)
- langchain
- pytesseract
- Pillow
- tabula-py
- jsonschema

## Utilizzo

I nodi possono essere utilizzati nei workflow PDK per elaborare documenti PDF, gestire metadati, tracciare eventi e interagire con il vectorstore.

### Esempio di workflow

```json
{
  "nodes": [
    {
      "id": "file_parser",
      "type": "file_parsing",
      "plugin": "pdf-monitor-plugin",
      "config": {
        "extract_text": true,
        "extract_metadata": true
      },
      "inputs": {
        "file_path": "/path/to/document.pdf"
      }
    },
    {
      "id": "event_logger",
      "type": "event_logger",
      "plugin": "pdf-monitor-plugin",
      "config": {},
      "inputs": {
        "event_type": "file_processed",
        "file_name": "document.pdf",
        "status": "success"
      }
    }
  ]
}
```
