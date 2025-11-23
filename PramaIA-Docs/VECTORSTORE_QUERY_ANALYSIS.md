# Analisi Endpoint VectorstoreService: Verifica Funzionalità Query

## Background

Sulla base del feedback di un'altra sessione di chat, è emerso il bisogno di verificare e documentare completamente gli endpoint disponibili per le query vettoriali nel VectorstoreService, considerando che:

1. Il salvataggio di embeddings sembra funzionare (via `chroma_vector_store` node)
2. Le query di ricerca potrebbero essere bloccate o mal configurate
3. È necessario elencare collezioni e documenti per verificare l'indicizzazione

## Endpoint Analizzati

### 🔍 Endpoint di Ricerca Principali

#### 1. Query Vettoriali per Collezione
```http
POST /documents/{collection_name}/query
Content-Type: application/json

{
  "query_text": "testo da cercare",
  "limit": 5
}
```

**Status**: ✅ **OPERATIVO**  
**Test Effettuato**: Query su collezione "manuals" - endpoint risponde correttamente
**Risultato Test**: 0 risultati trovati (possibile problema di indicizzazione)

#### 2. Gestione Collezioni
```http
GET /collections/
```

**Status**: ✅ **OPERATIVO**  
**Risultato**: Lista collezioni vuota `{"message": "Collections endpoint operational", "collections": []}`

#### 3. Lista Documenti Vectorstore
```http
GET /vectorstore/documents
```

**Status**: ✅ **OPERATIVO**  
**Risultati**: 2 documenti trovati:
- `coordinated_doc_001` (collezione: "manuals")
- `test_coordination_001` (collezione: "test_collection")

### 📊 Endpoint di Gestione Database

#### 4. Statistiche Database
```http
GET /api/database-management/vectorstore/statistics
```

#### 5. Stato Servizi
```http
GET /api/database-management/vectorstore/service-status
```

#### 6. Reset Database
```http
POST /api/database-management/vectorstore/reset
```

### 🔧 Endpoint di Amministrazione

#### 7. Backup Vectorstore
```http
POST /api/database-management/vectorstore/backup
```

#### 8. Health Check Dependencies
```http
GET /health/dependencies
```

## Diagnosi Problemi

### ❌ Problema Identificato: Discrepanza Indicizzazione

**Situazione Attuale**:
- ✅ Documenti esistono nel database relazionale (SQLite)
- ❌ Query vettoriali restituiscono 0 risultati
- ❓ Collezioni risultano vuote nonostante documenti presenti

**Possibili Cause**:

1. **Indicizzazione Embeddings Mancante**:
   ```
   I documenti sono salvati come testo ma gli embeddings vettoriali
   non sono stati generati o indicizzati correttamente
   ```

3. **Sincronizzazione Database Multipli**:
   ```
   - SQLite contiene metadati e testo
   - ChromaDB (via VectorstoreService) dovrebbe contenere embeddings
   - Possibile disallineamento tra i due sistemi
   ```

3. **Configurazione Collection Name**:
   ```
   - Query cerca in collezione "manuals" 
   - Documenti potrebbero essere indicizzati con nome diverso
   ```

## Raccomandazioni Immediate

### 1. 🔍 Verifica Completa Stato Sistema

```bash
# Test collezioni
curl http://localhost:8090/collections/

# Test documenti completi  
curl http://localhost:8090/vectorstore/documents | jq .

# Test query su collezioni specifiche
curl -X POST http://localhost:8090/documents/manuals/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "coordinamento", "limit": 5}'

curl -X POST http://localhost:8090/documents/test_collection/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test", "limit": 5}'
```

### 2. 📋 Audit Completo Indicizzazione

```bash
# Verifica statistiche database
curl http://localhost:8090/api/database-management/vectorstore/statistics | jq .

# Verifica stato servizi
curl http://localhost:8090/api/database-management/vectorstore/service-status | jq .

# Verifica dipendenze
curl http://localhost:8090/health/dependencies | jq .
```

### 3. 🔄 Test Pipeline Completa

Eseguire test end-to-end con workflow documentato:
1. `document_input_node` - Caricamento documento
2. `pdf_text_extractor` - Estrazione testo
3. `text_chunker` - Divisione chunks
4. `text_embedder` - Generazione embeddings
5. `chroma_vector_store` - **Salvataggio** embeddings
6. `chroma_retriever` - **Ricerca** embeddings

### 4. 📝 Controllo Configurazioni Nodi

Verificare che i nodi writer e retriever siano configurati correttamente:

**Writer Node** (`chroma_vector_store`):
```json
{
  "config": {
    "collection_name": "test_documents",
    "service_url": "http://localhost:8090"
  }
}
```

**Retriever Node** (`chroma_retriever`):
```json
{
  "config": {
    "collection_name": "test_documents",
    "service_url": "http://localhost:8090",
    "similarity_threshold": 0.5
  }
}
```

## Struttura Corrente Database

### Database SQLite (Metadati)
```
- Contiene: metadati documenti, testo completo, informazioni file
- Documenti presenti: 2 
- Status: ✅ Operativo
```

### Database ChromaDB (Embeddings)
```
- Contiene: embeddings vettoriali, collezioni indicizzate
- Accesso: Tramite VectorstoreService API
- Collezioni presenti: 0 (vuote)
- Status: ❌ Problema indicizzazione
```

## Next Steps

### Priorità Alta
1. **Eseguire workflow completo** di indicizzazione documento
2. **Verificare generazione embeddings** nel nodo `text_embedder`
3. **Testare salvataggio** nel nodo `chroma_vector_store`
4. **Validare ricerca** nel nodo `chroma_retriever`

### Priorità Media
1. Implementare logging dettagliato per debug pipeline
2. Creare script di verifica stato sistema
3. Documentare procedura di troubleshooting

### Priorità Bassa
1. Ottimizzare performance query
2. Implementare backup/restore automatico
3. Aggiungere metriche monitoring

## Documentazione Correlata

- **[chroma_vector_store_node.md](NODES/chroma_vector_store_node.md)** - Documentazione nodo salvataggio
- **[chroma_retriever_node.md](NODES/chroma_retriever_node.md)** - Documentazione nodo ricerca
- **[NODES_AND_PLUGINS_OVERVIEW.md](NODES_AND_PLUGINS_OVERVIEW.md)** - Panoramica sistema nodi

---

*Documento creato in risposta al feedback dell'altra chat session per garantire un'analisi completa degli endpoint di query del VectorstoreService.*