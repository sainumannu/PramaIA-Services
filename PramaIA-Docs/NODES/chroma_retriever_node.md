# Documentazione Nodo: ChromaDB Retriever (chroma_retriever)

## Panoramica Funzionale

Il nodo **ChromaDB Retriever** (`chroma_retriever`) è un nodo di elaborazione specializzato nella ricerca semantica di documenti simili nel database vettoriale ChromaDB tramite il servizio VectorstoreService. Questo nodo è il complemento del nodo `chroma_vector_store` e rappresenta il punto di interrogazione per il recupero di informazioni rilevanti basate su similarità vettoriali.

### Funzionalità Principali
- **Ricerca Semantica**: Trova documenti simili usando embeddings vettoriali
- **Filtri di Similarità**: Soglie configurabili per controllo qualità risultati
- **Gestione Metadati**: Include metadati contestuali nei risultati
- **Fallback Mode**: Modalità mock per testing e sviluppo
- **Service Integration**: Integrazione completa con VectorstoreService

## Configurazione Dettagliata

### Schema di Configurazione

```json
{
  "node_type": "document-semantic-complete-plugin.chroma_retriever",
  "config": {
    "collection_name": "documents",
    "service_url": "http://localhost:8090",
    "top_k": 5,
    "score_threshold": 0.7,
    "search_k": 10,
    "similarity_threshold": 0.7,
    "include_metadata": true
  }
}
```

### Parametri di Configurazione

| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `collection_name` | string | "documents" | Nome della collezione ChromaDB da interrogare |
| `service_url` | string | "http://localhost:8090" | URL del VectorstoreService |
| `top_k` | integer | 5 | Numero di risultati da restituire (alias per max_results) |
| `score_threshold` | number | 0.7 | Soglia minima di similarità (alias per similarity_threshold) |
| `search_k` | number | 10 | Parametro interno per ottimizzazione ricerca |
| `similarity_threshold` | number | 0.7 | Soglia minima di similarità per filtrare risultati |
| `include_metadata` | boolean | true | Se includere metadati nei risultati |

### Configurazioni Avanzate

```json
{
  "config": {
    "collection_name": "technical_documents",
    "service_url": "http://vectorstore-service:8090",
    "top_k": 10,
    "similarity_threshold": 0.8,
    "include_metadata": true,
    "max_results": 10,
    "distance_metric": "cosine",
    "rerank_results": true,
    "context_window": 512
  }
}
```

## Input/Output Specifications

### Input

**Nome**: `query_input`  
**Tipo**: `text` o `json`  
**Richiesto**: `true`

**Formato Testo Semplice**:
```
"Come funziona il coordinamento tra sistemi?"
```

**Formato JSON Avanzato** (se disponibile `query_embeddings`):
```json
{
  "query": "Come funziona il coordinamento tra sistemi?",
  "embeddings": [
    [0.1, 0.2, 0.3, ...]  // Embedding pre-calcolato della query
  ],
  "filters": {  // Filtri opzionali sui metadati
    "document_type": "manual",
    "language": "italian"
  }
}
```

**Validazioni Input**:
- Se fornito `query_embeddings`, deve contenere almeno un embedding
- Ogni embedding deve essere un array di numeri float
- La query testuale è sempre richiesta per logging e riferimento

### Output

**Nome**: `documents_output`  
**Tipo**: `json`

**Struttura Output Successo**:
```json
{
  "status": "success",
  "retrieved_documents": [
    {
      "document": "Manuale di coordinamento tra sistemi PramaIA...",
      "similarity_score": 0.8542,
      "distance": 0.1458,
      "document_id": "coordinated_doc_001",
      "metadata": {
        "author": "PramaIA Team",
        "document_type": "manual",
        "page_count": 25,
        "created_at": "2025-11-15T23:40:04.570294"
      }
    },
    {
      "document": "Test contenuto per verificare coordinamento...",
      "similarity_score": 0.7234,
      "distance": 0.2766,
      "document_id": "test_coordination_001",
      "metadata": {
        "document_type": "test",
        "source": "coordination_test"
      }
    }
  ],
  "retrieval_metadata": {
    "query_text": "Come funziona il coordinamento tra sistemi?",
    "collection_name": "documents",
    "max_results": 5,
    "similarity_threshold": 0.7,
    "documents_found": 2
  }
}
```

**Struttura Output Errore**:
```json
{
  "status": "error",
  "error": "Collezione 'unknown_collection' non trovata",
  "retrieved_documents": [],
  "retrieval_metadata": {
    "query_text": "",
    "collection_name": "",
    "documents_found": 0
  }
}
```

## Implementazione Tecnica

### Classe Principale: ChromaRetrieverProcessor

```python
class ChromaRetrieverProcessor:
    """Processore per recuperare documenti simili tramite VectorstoreService."""
    
    def __init__(self):
        self.client = None
        self.service_url = None
    
    async def process(self, context) -> Dict[str, Any]:
        """Recupera documenti simili dalla query."""
```

### Flusso di Elaborazione

1. **Validazione Input**: Verifica presenza query e/o embeddings
2. **Inizializzazione Client**: Connessione al VectorstoreService
3. **Controllo Collezione**: Verifica esistenza e contenuto collezione via API
4. **Query Vettoriale**: Ricerca similarità usando VectorstoreService API
5. **Filtro Risultati**: Applicazione soglie di similarità
6. **Post-processing**: Ordinamento e formattazione risultati
7. **Return Results**: Restituzione documenti con metadati

### Calcolo Similarità

```python
def calculate_similarity(distance):
    """Converte distanza ChromaDB in similarity score."""
    # ChromaDB restituisce distanze (più basso = più simile)
    # Convertiamo in similarity score (più alto = più simile)
    similarity_score = max(0, 1 - distance)
    return round(similarity_score, 4)
```

### Gestione Collezioni

Il nodo accede al database ChromaDB tramite VectorstoreService:

- **HTTP Client**: Connessione al VectorstoreService via API REST
- **Collection Management**: Verifica automatica esistenza collezioni via endpoint
- **Error Recovery**: Fallback a modalità mock se VectorstoreService non disponibile
- **Performance Optimization**: Riutilizzo connessioni HTTP

## Esempi di Utilizzo

### Workflow RAG Completo

```yaml
workflow:
  # 1. Input query utente
  - node: query_input_node
    config:
      placeholder: "Inserisci la tua domanda..."
  
  # 2. Genera embedding per la query
  - node: text_embedder
    config:
      model: "text-embedding-ada-002"
      input_from: "query_input_node.query_output"
  
  # 3. Ricerca documenti simili
  - node: chroma_retriever  # <- Questo nodo
    config:
      collection_name: "knowledge_base"
      similarity_threshold: 0.75
      top_k: 8
    input_from: "text_embedder.embeddings_output"
  
  # 4. Genera risposta con contesto
  - node: llm_processor
    config:
      model: "gpt-4"
      system_prompt: "Rispondi basandoti sui documenti forniti"
    inputs:
      context_input: "chroma_retriever.documents_output"
      question_input: "query_input_node.query_output"
```

### Configurazione Multi-Collezione

```json
{
  "workflows": [
    {
      "name": "search_manuals",
      "nodes": {
        "manual_search": {
          "type": "chroma_retriever",
          "config": {
            "collection_name": "technical_manuals",
            "similarity_threshold": 0.8,
            "top_k": 5,
            "include_metadata": true
          }
        }
      }
    },
    {
      "name": "search_faqs", 
      "nodes": {
        "faq_search": {
          "type": "chroma_retriever",
          "config": {
            "collection_name": "frequently_asked",
            "similarity_threshold": 0.7,
            "top_k": 3,
            "include_metadata": true
          }
        }
      }
    }
  ]
}
```

## Error Handling

### Tipi di Errori Gestiti

1. **ChromaDB Connection Errors**
   ```
   - Database ChromaDB non disponibile
   - Directory non accessibile
   - Errori di lettura database
   ```

2. **Collection Errors**
   ```
   - Collezione non esistente
   - Collezione vuota
   - Formato collezione incompatibile
   ```

3. **Query Errors**
   ```
   - Query embeddings mancanti o malformati
   - Dimensioni embedding non compatibili
   - Query vuote o invalide
   ```

### Strategie di Recovery

```python
# Fallback automatico a modalità mock
if not CHROMADB_AVAILABLE or self.client == "mock":
    return self._mock_retrieve_documents(max_results)

# Gestione collezioni mancanti
try:
    collection = self.client.get_collection(name=collection_name)
except Exception:
    logger.warning(f"Collezione {collection_name} non trovata")
    return []

# Validazione risultati
if not results['documents'] or len(results['documents']) == 0:
    logger.info("Nessun documento trovato per la query")
    return []
```

### Logging degli Errori

```python
# Log dettagliato per debugging
logger.error(f"[ChromaRetriever] ERRORE query: {str(e)}")
logger.error(f"  - Collezione: {collection_name}")
logger.error(f"  - Directory: {persist_directory}")
logger.error(f"  - Query embedding size: {len(query_embeddings[0]) if query_embeddings else 0}")
```

## Performance Considerations

### Ottimizzazioni Implementate

1. **Client Caching**: Riutilizzo connessioni ChromaDB esistenti
2. **Query Optimization**: Parametro `search_k` per controllo performance
3. **Result Filtering**: Filtro pre-emptivo su soglie similarità
4. **Memory Management**: Gestione efficiente risultati di ricerca

### Metriche Performance Tipiche

- **Latency**: 10-50ms per query su 1K documenti
- **Throughput**: ~100 query/secondo (dipende dalla dimensione collezione)
- **Memory Usage**: ~50MB per collezione da 10K documenti
- **Disk I/O**: Lettura ottimizzata con caching ChromaDB

### Configurazioni per Performance

```json
{
  "config": {
    "top_k": 20,                    // Più risultati ma maggiore latenza
    "similarity_threshold": 0.8,    // Soglia alta per meno risultati
    "include_metadata": false,      // Riduce trasferimento dati
    "search_k": 50,                // Ottimizzazione interna ChromaDB
    "cache_embeddings": true       // Caching query frequenti
  }
}
```

## Integration Notes

### Nodi Correlati

⚠️ **IMPORTANTE**: Questo nodo (`chroma_retriever`) gestisce solo la **ricerca/lettura**. Per il **salvataggio** di embeddings, utilizzare il nodo correlato:

- **[chroma_vector_store](chroma_vector_store_node.md)** - Salvataggio embeddings nel database vettoriale

**Flusso completo**: `text_embedder` → `chroma_vector_store` (salvataggio) → `chroma_retriever` (ricerca)

### Differenze Architetturali

| Aspetto | chroma_vector_store | chroma_retriever |
|---------|-------------------|-----------------|
| **Accesso Database** | Via VectorstoreService (API) | Via VectorstoreService (API) |
| **Operazione** | Scrittura/Salvataggio | Lettura/Ricerca |
| **Dipendenze** | VectorstoreService attivo | VectorstoreService attivo |
| **Fallback** | Mock salvataggio | Mock risultati |
| **Performance** | Ottimizzato per batch | Ottimizzato per query singole |

### Environment Variables

```bash
# Configurazione VectorstoreService
VECTORSTORE_SERVICE_URL=http://localhost:8090
VECTORSTORE_TIMEOUT=30
VECTORSTORE_RETRY_ATTEMPTS=3

# Performance tuning
VECTORSTORE_DEFAULT_K=5
VECTORSTORE_SIMILARITY_THRESHOLD=0.7
VECTORSTORE_INCLUDE_METADATA=true
```

## Testing e Debugging

### Modalità Mock

Il nodo supporta modalità mock quando ChromaDB non è disponibile:

```python
# Attivazione automatica se ChromaDB non disponibile
if not CHROMADB_AVAILABLE:
    logger.warning("ChromaDB non disponibile, usando retrieval mock")
    return self._mock_retrieve_documents(max_results)
```

### Debug delle Query

```python
# Logging dettagliato per debugging
logger.debug(f"Query embedding dimensions: {len(query_embeddings[0])}")
logger.debug(f"Collection document count: {collection.count()}")
logger.debug(f"Similarity threshold: {similarity_threshold}")
logger.debug(f"Raw ChromaDB results: {results}")
```

### Test di Integrazione

```python
# Test completo con ChromaDB reale
async def test_retrieval_integration():
    processor = ChromaRetrieverProcessor()
    context = {
        'config': {
            'collection_name': 'test_collection',
            'similarity_threshold': 0.5
        },
        'inputs': {
            'query_input': 'test query',
            'query_embeddings': {
                'embeddings': [[0.1, 0.2, 0.3, 0.4]]
            }
        }
    }
    result = await processor.process(context)
    assert result['status'] == 'success'
    assert 'retrieved_documents' in result
```

### Verifica Collezioni

```python
# Script per verificare stato collezioni
def check_collection_status():
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        collections = client.list_collections()
        for collection in collections:
            print(f"Collection: {collection.name}")
            print(f"  - Documents: {collection.count()}")
            print(f"  - Metadata: {collection.metadata}")
    except Exception as e:
        print(f"Error: {e}")
```

## Changelog e Versioni

### Versione 1.0.0 (Corrente)
- Implementazione base con ChromaDB diretto
- Supporto query vettoriali con similarità
- Modalità fallback mock
- Logging strutturato
- Gestione metadati completa

### Roadmap Future
- **v1.1.0**: Supporto filtri avanzati sui metadati
- **v1.2.0**: Caching intelligente query frequenti
- **v1.3.0**: Integrazione con VectorstoreService per unificazione
- **v2.0.0**: Supporto database vettoriali multipli (Pinecone, Weaviate)

## Note Tecniche e Troubleshooting

### Verifica Database ChromaDB

Per verificare che ChromaDB sia configurato correttamente:

```bash
# Controlla directory database
ls -la ./chroma_db/

# Verifica collezioni esistenti (via Python)
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
print('Collections:', [c.name for c in client.list_collections()])
"
```

### Problemi Comuni

1. **ChromaDB non trovato**:
   ```bash
   pip install chromadb
   # oppure
   conda install -c conda-forge chromadb
   ```

2. **Collezione vuota ma documenti esistono nel VectorstoreService**:
   - I due sistemi (VectorstoreService e ChromaDB locale) sono separati
   - Verificare che i documenti siano stati salvati anche localmente
   - Usare il nodo `chroma_vector_store` per popolare ChromaDB locale

3. **Risultati di ricerca inconsistenti**:
   - Verificare che gli embedding siano stati generati con lo stesso modello
   - Controllare la soglia di similarità (può essere troppo alta)
   - Verificare dimensioni embedding compatibili

4. **Performance lente**:
   - Ridurre `top_k` per meno risultati
   - Aumentare `similarity_threshold` per filtrare meglio
   - Ottimizzare `search_k` per collezioni grandi

---

*Per ulteriori informazioni o supporto, consultare la documentazione PramaIA o contattare il team di sviluppo.*