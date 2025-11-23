# Documentazione Nodo: ChromaDB Writer (chroma_vector_store)

## Panoramica Funzionale

Il nodo **ChromaDB Writer** (`chroma_vector_store`) è un nodo di elaborazione specializzato nel salvataggio di embeddings vettoriali nel database ChromaDB tramite il servizio VectorstoreService. Questo nodo è parte integrante della pipeline semantica di documenti e rappresenta il punto di archiviazione persistente per gli embeddings generati.

### Funzionalità Principali
- **Archiviazione Embeddings**: Salva embeddings vettoriali con metadati associati
- **Gestione Collezioni**: Crea e gestisce collezioni ChromaDB automaticamente
- **Batch Processing**: Elaborazione efficiente in batch per migliori performance
- **Fallback Mode**: Modalità mock per testing e sviluppo
- **Service Integration**: Integrazione completa con VectorstoreService

## Configurazione Dettagliata

### Schema di Configurazione

```json
{
  "node_type": "document-semantic-complete-plugin.chroma_vector_store",
  "config": {
    "collection_name": "documents",
    "persist_directory": "./chroma_db",
    "distance_metric": "cosine",
    "embedding_model": "text-embedding-ada-002",
    "chunk_size": 1000,
    "metadata_fields": ["source", "page"],
    "service_url": "http://localhost:8090"
  }
}
```

### Parametri di Configurazione

| Parametro | Tipo | Default | Descrizione | Criticità |
|-----------|------|---------|-------------|-----------|
| `collection_name` | string | "documents" | Nome della collezione ChromaDB dove salvare gli embeddings | **REQUIRED** |
| `service_url` | string | "http://localhost:8090" | URL del VectorstoreService | **🔴 CRITICAL** |
| `metadata_fields` | array | ["source", "page"] | Campi metadati da includere nei documenti | **🟡 IMPORTANT** |
| `distance_metric` | string | "cosine" | Metrica di distanza: `cosine`, `euclidean`, `manhattan` | **🟡 IMPORTANT** |
| `embedding_model` | string | "text-embedding-ada-002" | Nome del modello embedding utilizzato (per metadati) | OPTIONAL |
| `batch_size` | number | 20 | Numero di documenti da processare per batch | PERFORMANCE |
| `retry_attempts` | number | 3 | Numero di tentativi in caso di errore | RELIABILITY |
| `timeout` | number | 30 | Timeout in secondi per chiamate al servizio | RELIABILITY |
| `chunk_size` | number | 1000 | Dimensione dei chunk di testo in caratteri | OPTIONAL |
| `persist_directory` | string | "./chroma_db" | Directory di persistenza per database locali (non usato con service) | LEGACY |

> **⚠️ ATTENZIONE**: La mancanza di `service_url` è la **causa più comune** di problemi di indicizzazione. Senza questo parametro, il nodo non può connettersi al VectorstoreService.

### Configurazioni Avanzate

```json
{
  "config": {
    "collection_name": "pdf_documents_v2",
    "service_url": "http://vectorstore-service:8090",
    "distance_metric": "cosine",
    "embedding_model": "all-MiniLM-L6-v2",
    "batch_size": 50,
    "retry_attempts": 3,
    "timeout": 30,
    "metadata_fields": ["source", "page", "chapter", "document_type"]
  }
}
```

## Input/Output Specifications

### Input

**Nome**: `embeddings_input`  
**Tipo**: `json`  
**Richiesto**: `true`

**Struttura Attesa**:
```json
{
  "embeddings": [
    [0.1, 0.2, 0.3, ...],  // Array di float (vettore embedding)
    [0.4, 0.5, 0.6, ...],  // Secondo embedding
    // ... altri embeddings
  ],
  "chunks": [
    "Primo chunk di testo...",
    "Secondo chunk di testo...",
    // ... altri chunk
  ],
  "model": "text-embedding-ada-002",  // Modello utilizzato
  "metadata": {  // Metadati opzionali
    "source": "document.pdf",
    "total_pages": 10,
    "created_at": "2023-11-23T10:00:00Z"
  }
}
```

**Validazioni Input**:
- `embeddings` e `chunks` devono avere la stessa lunghezza
- Ogni embedding deve essere un array di numeri float
- `chunks` deve contenere stringhe non vuote

### Output

**Nome**: `storage_result`  
**Tipo**: `json`

**Struttura Output Successo**:
```json
{
  "status": "success",
  "storage_result": {
    "collection_name": "documents",
    "document_ids": [
      "doc_20231123_abc12345_0001",
      "doc_20231123_def67890_0002"
    ],
    "documents_saved": 15,
    "model_used": "text-embedding-ada-002",
    "service_url": "http://localhost:8090"
  },
  "documents_saved": 15
}
```

**Struttura Output Errore**:
```json
{
  "status": "error",
  "error": "Descrizione dell'errore",
  "storage_result": {
    "collection_name": "",
    "document_ids": [],
    "documents_saved": 0
  }
}
```

## Implementazione Tecnica

### Classe Principale: VectorstoreWriterProcessor

```python
class VectorstoreWriterProcessor:
    """Processore per salvare embeddings usando VectorstoreService."""
    
    def __init__(self):
        self.client = None
        self.service_url = None
    
    async def process(self, context) -> Dict[str, Any]:
        """Elabora e salva embeddings nel database vettoriale."""
```

### Flusso di Elaborazione

1. **Validazione Input**: Verifica presenza e correttezza degli embeddings
2. **Inizializzazione Client**: Connessione al VectorstoreService
3. **Gestione Collezione**: Verifica/creazione collezione target
4. **Generazione ID**: Creazione ID univoci per documenti
5. **Preparazione Metadati**: Arricchimento metadati documenti
6. **Salvataggio Batch**: Invio dati in batch al servizio
7. **Verifica Risultato**: Controllo stato operazione

### Generazione ID Documenti

```python
def generate_document_id(doc_text, index):
    timestamp = datetime.now().strftime('%Y%m%d')
    content_hash = hashlib.md5(doc_text.encode('utf-8')).hexdigest()
    return f"doc_{timestamp}_{content_hash[:8]}_{index:04d}"
```

### Batch Processing

Il nodo elabora i documenti in batch per ottimizzare le performance:

- **Batch Size**: 50 documenti per batch (configurabile)
- **Parallel Processing**: Invio asincrono dei batch
- **Error Recovery**: Gestione errori per singoli batch
- **Progress Tracking**: Monitoring del progresso di salvataggio

## Esempi di Utilizzo

### Workflow Standard PDF

```yaml
workflow:
  - node: pdf_text_extractor
    config:
      extraction_method: "hybrid"
  - node: text_chunker
    config:
      chunk_size: 1000
      chunk_overlap: 200
  - node: text_embedder
    config:
      model: "text-embedding-ada-002"
  - node: chroma_vector_store  # <- Questo nodo
    config:
      collection_name: "pdf_documents"
      service_url: "http://vectorstore:8090"
```

### Configurazione Multi-Collezione

```json
{
  "workflows": [
    {
      "name": "documents_general",
      "nodes": {
        "storage": {
          "type": "chroma_vector_store",
          "config": {
            "collection_name": "general_docs",
            "metadata_fields": ["source", "type"]
          }
        }
      }
    },
    {
      "name": "documents_technical", 
      "nodes": {
        "storage": {
          "type": "chroma_vector_store",
          "config": {
            "collection_name": "technical_docs",
            "metadata_fields": ["source", "complexity", "domain"]
          }
        }
      }
    }
  ]
}
```

## Error Handling

### Tipi di Errori Gestiti

1. **Input Validation Errors**
   ```
   - Embeddings mancanti o vuoti
   - Mismatch lunghezza embeddings/chunks
   - Formato dati non valido
   ```

2. **Service Connection Errors**
   ```
   - VectorstoreService non raggiungibile
   - Timeout connessione
   - Errori autenticazione
   ```

3. **Database Errors**
   ```
   - Collezione non accessibile
   - Spazio insufficiente
   - Errori persistenza
   ```

### Strategie di Recovery

```python
# Fallback a modalità mock
if self.client == "mock":
    return self._mock_save_embeddings(documents)

# Retry automatico con backoff
for attempt in range(self.retry_attempts):
    try:
        return await self._save_to_service(data)
    except Exception as e:
        if attempt < self.retry_attempts - 1:
            await asyncio.sleep(2 ** attempt)
        else:
            raise e
```

### Logging degli Errori

```python
# Log errore con contesto
logger.error(f"[VectorstoreWriter] ERRORE salvataggio: {str(e)}")
logger.error(f"  - Collezione: {collection_name}")
logger.error(f"  - Documenti: {len(documents)}")
logger.error(f"  - Service URL: {self.service_url}")
```

## Performance Considerations

### Ottimizzazioni Implementate

1. **Batch Processing**: Riduce overhead network
2. **Connection Pooling**: Riutilizzo connessioni HTTP
3. **Async Operations**: Elaborazione non bloccante
4. **Memory Management**: Gestione memoria per grandi dataset

### Metriche Performance Tipiche

- **Throughput**: ~1000 documenti/minuto (dipende da dimensione embedding)
- **Latency**: 50-200ms per batch (50 documenti)
- **Memory Usage**: ~10MB per 1000 documenti da 1KB
- **Network**: ~1MB/s per embeddings 1536-dimensional

### Configurazioni per Performance

```json
{
  "config": {
    "batch_size": 100,           // Batch più grandi per alta velocità
    "connection_timeout": 60,    // Timeout più alto per batch grandi
    "max_retries": 5,           // Più retry per stabilità
    "compression": true         // Compressione dati network
  }
}
```

## Integration Notes

### Nodi Correlati

⚠️ **IMPORTANTE**: Questo nodo (`chroma_vector_store`) gestisce solo la **scrittura** di embeddings. Per la **ricerca/retrieval**, utilizzare il nodo correlato:

- **[chroma_retriever](chroma_retriever_node.md)** - Ricerca semantica nel database vettoriale

**Flusso completo**: `text_embedder` → `chroma_vector_store` (salvataggio) → `chroma_retriever` (ricerca)

### Dipendenze di Servizio

- **VectorstoreService**: Servizio principale per persistenza
- **LogService**: Logging centralizzato e monitoring
- **MetadataService**: Gestione metadati documenti (opzionale)

### API Endpoints Utilizzate

```http
# Health check
GET {service_url}/health

# Gestione collezioni
GET {service_url}/collections/
POST {service_url}/collections/

# Gestione documenti
GET {service_url}/vectorstore/documents
POST {service_url}/vectorstore/documents

# Query vettoriali (per retrieval)
POST {service_url}/documents/{collection_name}/query

# Statistiche
GET {service_url}/stats/
GET {service_url}/api/database-management/vectorstore/statistics
```

### Environment Variables

```bash
# Configurazione servizio
VECTORSTORE_SERVICE_URL=http://localhost:8090
VECTORSTORE_TIMEOUT=30
VECTORSTORE_RETRY_ATTEMPTS=3

# Configurazione batch
VECTORSTORE_BATCH_SIZE=50
VECTORSTORE_MAX_MEMORY=512MB
```

## Testing e Debugging

### Mock Mode

Il nodo supporta modalità mock per testing:

```python
# Attivazione automatica se servizio non raggiungibile
if service_unreachable:
    self.client = "mock"
    return self._mock_save_embeddings(documents)
```

### Debug Logging

```python
# Abilitazione debug dettagliato
logger.setLevel(logging.DEBUG)
logger.debug(f"Batch {batch_num}: {len(batch_documents)} documenti")
logger.debug(f"Embedding dimensions: {len(embeddings[0])}")
logger.debug(f"Collection stats: {collection_stats}")
```

### Test di Integrazione

```python
# Test con VectorstoreService
async def test_integration():
    processor = VectorstoreWriterProcessor()
    context = {
        'config': {'collection_name': 'test_collection'},
        'inputs': {
            'embeddings_input': {
                'embeddings': [[0.1, 0.2, 0.3]],
                'chunks': ['test document'],
                'model': 'test-model'
            }
        }
    }
    result = await processor.process(context)
    assert result['status'] == 'success'
```

## Changelog e Versioni

### Versione 1.0.0 (Corrente)
- Implementazione base con VectorstoreService
- Supporto batch processing
- Modalità fallback mock
- Logging strutturato

### Roadmap Future
- **v1.1.0**: Supporto collezioni multiple simultanee
- **v1.2.0**: Compressione embeddings
- **v1.3.0**: Streaming per dataset molto grandi
- **v2.0.0**: Supporto database vettoriali multipli

## Note Tecniche e Troubleshooting

### Verifica Salvataggio

Per verificare che i documenti siano stati salvati correttamente:

```bash
# Verifica collezioni esistenti
curl http://localhost:8090/collections/

# Verifica documenti nel vectorstore
curl http://localhost:8090/vectorstore/documents

# Test query (richiede il nodo chroma_retriever)
curl -X POST http://localhost:8090/documents/COLLECTION_NAME/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test query", "limit": 5}'
```

### Problemi Comuni

1. **Documenti salvati ma query non trova risultati**:
   - Verificare che gli embeddings siano stati generati correttamente
   - Controllare che la collezione sia stata creata nel VectorstoreService
   - Utilizzare il nodo `chroma_retriever` per ricerche semantiche

2. **Errori di connessione al VectorstoreService**:
   - Verificare che il servizio sia attivo: `curl http://localhost:8090/health`
   - Controllare le configurazioni di rete e firewall
   - Il nodo passa automaticamente in modalità mock se il servizio non è disponibile

---

*Per ulteriori informazioni o supporto, consultare la documentazione PramaIA o contattare il team di sviluppo.*