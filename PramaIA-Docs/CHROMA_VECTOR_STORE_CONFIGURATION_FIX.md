# Fix Configurazione ChromaDB Vector Store Node

## Problema Identificato

La configurazione attuale del nodo `chroma_vector_store` è **incompleta** e questo sta causando problemi di indicizzazione:

### Configurazione Attuale (Problematica)
```json
{
    "collection_name": "pdf_documents",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "operation": "add"
}
```

### Problemi Identificati

1. **MANCANZA SERVICE_URL**: Il nodo non sa dove connettere il VectorstoreService
2. **PARAMETRI MANCANTI**: Mancano configurazioni essenziali per il corretto funzionamento
3. **COLLECTION SCORRETTA**: Possibile mismatch tra collezione configurata e effettiva
4. **METADATI NON SPECIFICATI**: Mancano i campi metadata necessari

## Configurazione Corretta

### Configurazione Completa Raccomandata
```json
{
    "node_type": "document-semantic-complete-plugin.chroma_vector_store",
    "config": {
        "collection_name": "pdf_documents",
        "service_url": "http://localhost:8090",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "operation": "add",
        "distance_metric": "cosine",
        "metadata_fields": ["source", "page", "document_type"],
        "batch_size": 20,
        "chunk_size": 1000,
        "retry_attempts": 3,
        "timeout": 30
    }
}
```

### Parametri Critici da Aggiungere

| Parametro | Valore | Motivo |
|-----------|--------|--------|
| **service_url** | `"http://localhost:8090"` | **ESSENZIALE**: Connessione al VectorstoreService |
| **distance_metric** | `"cosine"` | **IMPORTANTE**: Tipo di similarità per la ricerca |
| **metadata_fields** | `["source", "page", "document_type"]` | **IMPORTANTE**: Metadati per filtri e ricerca |
| **batch_size** | `20` | **PERFORMANCE**: Ottimizza l'elaborazione in batch |
| **retry_attempts** | `3` | **AFFIDABILITÀ**: Gestione errori di rete |
| **timeout** | `30` | **STABILITÀ**: Timeout per chiamate al servizio |

## Verifica Collection Name

### Controllo Collection Esistenti
```bash
# Verifica collezioni nel VectorstoreService
curl -X GET "http://localhost:8090/collections" | jq
```

### Possibili Nomi Collection da Verificare
- `pdf_documents` (attuale)
- `documents` (default)
- `manuals` (se contiene manuali PDF)

## Script di Aggiornamento

### PowerShell Script per Verifica e Fix
```powershell
# verifica_configurazione_nodo.ps1

Write-Host "=== VERIFICA CONFIGURAZIONE CHROMA_VECTOR_STORE ===" -ForegroundColor Cyan

# 1. Verifica VectorstoreService
Write-Host "`n1. Verifico VectorstoreService..." -ForegroundColor Yellow
try {
    $service = Invoke-RestMethod -Uri "http://localhost:8090/health" -Method GET -TimeoutSec 5
    Write-Host "✓ VectorstoreService attivo: $($service.status)" -ForegroundColor Green
} catch {
    Write-Host "✗ VectorstoreService NON raggiungibile!" -ForegroundColor Red
    Write-Host "  ERRORE: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Lista collezioni esistenti
Write-Host "`n2. Collezioni esistenti:" -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "http://localhost:8090/collections" -Method GET
    if ($collections.collections.Count -eq 0) {
        Write-Host "⚠ NESSUNA collezione trovata!" -ForegroundColor Red
    } else {
        foreach ($collection in $collections.collections) {
            Write-Host "  - $($collection.name): $($collection.count) documenti" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ Errore recupero collezioni: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Verifica collezione pdf_documents specifica
Write-Host "`n3. Verifico collezione 'pdf_documents':" -ForegroundColor Yellow
try {
    $collection = Invoke-RestMethod -Uri "http://localhost:8090/collections/pdf_documents" -Method GET
    Write-Host "✓ Collezione 'pdf_documents' trovata:" -ForegroundColor Green
    Write-Host "  - Documenti: $($collection.count)" -ForegroundColor Green
    Write-Host "  - Metadati: $($collection.metadata | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "✗ Collezione 'pdf_documents' NON trovata!" -ForegroundColor Red
    Write-Host "  Potrebbe essere necessario usare collection_name: 'documents' o 'manuals'" -ForegroundColor Yellow
}

# 4. Test upload di verifica
Write-Host "`n4. Test configurazione corretta..." -ForegroundColor Yellow
$correctConfig = @{
    collection_name = "pdf_documents"
    service_url = "http://localhost:8090"
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    operation = "add"
    distance_metric = "cosine"
    metadata_fields = @("source", "page", "document_type")
    batch_size = 20
    retry_attempts = 3
    timeout = 30
} | ConvertTo-Json -Depth 5

Write-Host "`nCONFIGURAZIONE CORRETTA da utilizzare:" -ForegroundColor Green
Write-Host $correctConfig -ForegroundColor White

Write-Host "`n=== RIEPILOGO AZIONI RICHIESTE ===" -ForegroundColor Cyan
Write-Host "1. Aggiornare la configurazione del nodo con i parametri mancanti" -ForegroundColor Yellow
Write-Host "2. Specificare service_url = 'http://localhost:8090'" -ForegroundColor Yellow
Write-Host "3. Aggiungere metadata_fields per migliorare la ricerca" -ForegroundColor Yellow
Write-Host "4. Verificare che la collezione 'pdf_documents' contenga effettivamente i documenti" -ForegroundColor Yellow
```

## Passi per la Risoluzione

### 1. Aggiornamento Immediato del Workflow

Nel file del workflow, sostituire la configurazione del nodo `chroma_vector_store`:

```yaml
# PRIMA (problematica)
- node: chroma_vector_store
  config:
    collection_name: "pdf_documents"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    operation: "add"

# DOPO (corretta)
- node: chroma_vector_store
  config:
    collection_name: "pdf_documents"
    service_url: "http://localhost:8090"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    operation: "add"
    distance_metric: "cosine"
    metadata_fields: ["source", "page", "document_type"]
    batch_size: 20
    retry_attempts: 3
    timeout: 30
```

### 2. Verifica Collection Name

Se dopo l'aggiornamento non funziona ancora:

```bash
# Verifica collezioni esistenti
curl "http://localhost:8090/collections"

# Se pdf_documents è vuota, prova con:
# collection_name: "documents"
# oppure
# collection_name: "manuals"
```

### 3. Test della Configurazione Aggiornata

Dopo l'aggiornamento, eseguire:

```bash
# Test del pipeline completo
./test_upload_retrieve.ps1

# Oppure test rapido
./quick_test.ps1
```

## Validation Checklist

- [ ] **service_url** configurato su "http://localhost:8090"
- [ ] **metadata_fields** specificati per il contesto
- [ ] **distance_metric** impostato su "cosine"
- [ ] **batch_size** configurato per performance
- [ ] **retry_attempts** e **timeout** per affidabilità
- [ ] **Collection esistente** e popolata nel VectorstoreService
- [ ] **Test pipeline** funzionante con la nuova configurazione

## Diagnostica Avanzata

### Se il problema persiste:

1. **Verifica Logging del Nodo**:
   ```bash
   # Cerca nei log gli errori del nodo
   grep -n "chroma_vector_store" /path/to/logs/*.log
   ```

2. **Test Manuale VectorstoreService**:
   ```bash
   # Test diretto dell'API
   curl -X POST "http://localhost:8090/collections/pdf_documents/add" \
        -H "Content-Type: application/json" \
        -d '{"documents": ["test"], "embeddings": [[0.1, 0.2, 0.3]], "metadatas": [{"source": "test"}]}'
   ```

3. **Verifica Sincronizzazione Database**:
   ```bash
   # Controlla se SQLite e ChromaDB sono sincronizzati
   curl "http://localhost:8090/collections/pdf_documents/query" \
        -H "Content-Type: application/json" \
        -d '{"query_embeddings": [[0.1, 0.2, 0.3]], "n_results": 5}'
   ```

---

## Conclusioni

La configurazione minima attuale **non è sufficiente** per il corretto funzionamento del nodo. I parametri mancanti, in particolare `service_url`, sono la causa principale del problema di indicizzazione segnalato nell'altro workspace.

**Azione immediata richiesta**: Aggiornare la configurazione del nodo con tutti i parametri necessari come specificato sopra.