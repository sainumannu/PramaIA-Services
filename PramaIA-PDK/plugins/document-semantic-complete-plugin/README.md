# PDF Semantic Complete Plugin

Plugin completo per ricerca semantica in documenti PDF usando embeddings vettoriali e Large Language Models.

## Descrizione

Questo plugin implementa una pipeline completa di elaborazione semantica di documenti PDF che include:

1. **PDF Input** - Caricamento file PDF
2. **PDF Text Extractor** - Estrazione testo da PDF
3. **Text Chunker** - Suddivisione intelligente del testo
4. **Text Embedder** - Generazione embeddings vettoriali
5. **ChromaDB Writer** - Salvataggio nel database vettoriale
6. **Query Input** - Elaborazione query utente
7. **Query Embedder** - Generazione embeddings per la query
8. **ChromaDB Retriever** - Recupero documenti simili
9. **LLM Processor** - Elaborazione con AI
10. **Response Formatter** - Formattazione risposta finale

## Caratteristiche

- ✅ **Supporto PDF completo** - Estrazione testo da file PDF multi-pagina
- ✅ **Chunking intelligente** - Suddivisione testo con overlap configurabile
- ✅ **Embeddings avanzati** - Supporto per modelli sentence-transformers
- ✅ **Database vettoriale** - Integrazione ChromaDB con persistenza
- ✅ **Multi-LLM** - Supporto OpenAI, Anthropic e modalità mock
- ✅ **Configurazione UI** - Parametri modificabili tramite interfaccia
- ✅ **Gestione errori** - Fallback robusti per ogni componente
- ✅ **Formati output** - Simple, JSON, Markdown, Detailed

## Installazione

1. Copia il plugin nella directory `examples/` del PramaIA-PDK
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura le API keys nei nodi LLM se necessario

## Configurazione

### PDF Text Extractor
- `preserve_layout`: Mantieni layout originale
- `clean_text`: Pulisci caratteri speciali
- `max_pages`: Numero massimo pagine da processare

### Text Chunker  
- `chunk_size`: Dimensione chunk in caratteri
- `overlap_size`: Overlap tra chunk consecutivi
- `separator`: Separatore per suddivisione

### Text Embedder
- `model_name`: Modello sentence-transformers
- `normalize_embeddings`: Normalizza vettori
- `batch_size`: Dimensione batch per processing

### ChromaDB Writer/Retriever
- `collection_name`: Nome collezione ChromaDB
- `persist_directory`: Directory persistenza database
- `distance_metric`: Metrica distanza (cosine, euclidean, manhattan)

### LLM Processor
- `provider`: Provider LLM (openai, anthropic, mock)
- `model`: Nome modello specifico
- `max_tokens`: Token massimi risposta
- `temperature`: Creatività risposta
- `openai_api_key`/`anthropic_api_key`: Chiavi API

### Response Formatter
- `output_format`: Formato output (simple, json, markdown, detailed)
- `include_metadata`: Includi metadati tecnici
- `include_sources`: Includi informazioni fonti
- `max_response_length`: Lunghezza massima risposta

## Workflow di Esempio

```json
{
  "name": "PDF Semantic Search Complete",
  "nodes": [
    {
      "id": "pdf_input",
      "type": "pdf_input_node",
      "config": { "file_path": "document.pdf" }
    },
    {
      "id": "pdf_extractor", 
      "type": "pdf_text_extractor_node",
      "config": {
        "preserve_layout": true,
        "clean_text": true,
        "max_pages": 50
      }
    },
    {
      "id": "text_chunker",
      "type": "text_chunker_node", 
      "config": {
        "chunk_size": 1000,
        "overlap_size": 200
      }
    },
    {
      "id": "text_embedder",
      "type": "text_embedder_node",
      "config": {
        "model_name": "all-MiniLM-L6-v2",
        "normalize_embeddings": true
      }
    },
    {
      "id": "chroma_writer",
      "type": "chroma_writer_node",
      "config": {
        "collection_name": "my_pdfs",
        "persist_directory": "./vector_db"
      }
    }
  ],
  "connections": [
    {"from": "pdf_input", "to": "pdf_extractor"},
    {"from": "pdf_extractor", "to": "text_chunker"},
    {"from": "text_chunker", "to": "text_embedder"},
    {"from": "text_embedder", "to": "chroma_writer"}
  ]
}
```

## API

Ogni nodo espone la funzione `process_node(context)` che:
- Riceve un context con `inputs` e `config`
- Restituisce un dizionario con `status` e risultati
- Gestisce errori con fallback appropriati

## Testing

Il plugin include modalità mock per ogni componente:
- **Text Embedder**: Genera embeddings casuali
- **ChromaDB**: Storage in memoria 
- **LLM**: Risposte generate localmente

## Troubleshooting

### Errori comuni

1. **Import Error librerie**: Installa requirements.txt
2. **API Key mancanti**: Configura chiavi nei nodi LLM
3. **ChromaDB errori**: Verifica permessi directory persistenza
4. **Memory errors**: Riduci batch_size e chunk_size

### Log

Tutti i processori includono logging dettagliato:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Licenza

Parte del progetto PramaIA-PDK.
