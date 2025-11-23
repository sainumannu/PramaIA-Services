# Test Suite: Upload e Retrieve Documenti PramaIA

Questa suite di test verifica il funzionamento completo della pipeline di upload e retrieve dei documenti, dalla scrittura alla ricerca semantica.

## Test Manuali Endpoint VectorstoreService

### 1. Test Health Check

```bash
# Verifica che il VectorstoreService sia attivo
curl -X GET "http://localhost:8090/health"
# Risultato atteso: {"status":"ok"}
```

### 2. Test Upload Documento

```bash
# Simula upload di un documento (normalmente fatto dal nodo chroma_vector_store)
curl -X POST "http://localhost:8090/vectorstore/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test_doc_001",
    "content": "Questo è un documento di test per verificare il funzionamento del sistema PramaIA. Il coordinamento tra i servizi è fondamentale per una corretta elaborazione semantica.",
    "collection": "test_collection",
    "metadata": {
      "author": "Test Suite",
      "document_type": "test",
      "created_at": "2025-11-23T14:00:00Z",
      "test_case": "upload_retrieve_validation"
    },
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.2, 0.3, 0.4, 0.5]
  }'
```

### 3. Test Verifica Upload

```bash
# Verifica che il documento sia stato salvato
curl -X GET "http://localhost:8090/vectorstore/documents"
# Cerca "test_doc_001" nei risultati

# Verifica collezioni
curl -X GET "http://localhost:8090/collections/"
# Dovrebbe mostrare "test_collection"
```

### 4. Test Query Semantica

```bash
# Test query con testo simile
curl -X POST "http://localhost:8090/documents/test_collection/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "coordinamento servizi",
    "limit": 5
  }'

# Test query con concetto correlato
curl -X POST "http://localhost:8090/documents/test_collection/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "elaborazione semantica",
    "limit": 3
  }'
```

### 5. Test Cleanup

```bash
# Rimuovi il documento di test
curl -X DELETE "http://localhost:8090/vectorstore/document/test_doc_001"

# Verifica rimozione
curl -X GET "http://localhost:8090/vectorstore/documents"
```

## Test Automatizzati PowerShell

### Script Test Completo

```powershell
# test_upload_retrieve.ps1
# Test automatizzato per upload e retrieve documenti

param(
    [string]$ServiceUrl = "http://localhost:8090",
    [string]$Collection = "test_collection_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

Write-Host "=== Test Suite Upload e Retrieve Documenti ===" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl"
Write-Host "Collection: $Collection"
Write-Host ""

# Funzione helper per test HTTP
function Test-HttpRequest {
    param($Uri, $Method = "GET", $Body = $null, $Headers = @{})
    
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -Body $Body -Headers $Headers
        } else {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        return @{ Success = $true; Data = $response }
    } catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

# Test 1: Health Check
Write-Host "Test 1: Health Check..." -ForegroundColor Yellow
$healthResult = Test-HttpRequest -Uri "$ServiceUrl/health"
if ($healthResult.Success) {
    Write-Host "✅ Service attivo: $($healthResult.Data.status)" -ForegroundColor Green
} else {
    Write-Host "❌ Service non raggiungibile: $($healthResult.Error)" -ForegroundColor Red
    exit 1
}

# Test 2: Upload Documento
Write-Host "`nTest 2: Upload Documento..." -ForegroundColor Yellow
$testDoc = @{
    id = "test_doc_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    content = "Documento di test per verificare il coordinamento tra sistemi PramaIA. Questo contenuto testa la pipeline di embedding e ricerca semantica."
    collection = $Collection
    metadata = @{
        author = "Test Automation"
        document_type = "test"
        created_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        test_case = "automated_upload_retrieve"
        keywords = @("coordinamento", "sistemi", "test", "embedding")
    }
    embedding = @(0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
}

$uploadBody = $testDoc | ConvertTo-Json -Depth 10
$uploadHeaders = @{"Content-Type" = "application/json"}
$uploadResult = Test-HttpRequest -Uri "$ServiceUrl/vectorstore/documents" -Method POST -Body $uploadBody -Headers $uploadHeaders

if ($uploadResult.Success) {
    Write-Host "✅ Documento caricato: $($testDoc.id)" -ForegroundColor Green
    $testDocId = $testDoc.id
} else {
    Write-Host "❌ Errore upload: $($uploadResult.Error)" -ForegroundColor Red
    exit 1
}

# Test 3: Verifica Upload
Write-Host "`nTest 3: Verifica Upload..." -ForegroundColor Yellow
$documentsResult = Test-HttpRequest -Uri "$ServiceUrl/vectorstore/documents"
if ($documentsResult.Success) {
    $foundDoc = $documentsResult.Data.documents | Where-Object { $_.id -eq $testDocId }
    if ($foundDoc) {
        Write-Host "✅ Documento trovato nel database" -ForegroundColor Green
        Write-Host "   - ID: $($foundDoc.id)"
        Write-Host "   - Collection: $($foundDoc.collection)"
        Write-Host "   - Content Length: $($foundDoc.content.Length) chars"
    } else {
        Write-Host "❌ Documento non trovato nel database" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Errore verifica documents: $($documentsResult.Error)" -ForegroundColor Red
}

# Test 4: Verifica Collezione
Write-Host "`nTest 4: Verifica Collezione..." -ForegroundColor Yellow
$collectionsResult = Test-HttpRequest -Uri "$ServiceUrl/collections/"
if ($collectionsResult.Success) {
    $foundCollection = $collectionsResult.Data.collections | Where-Object { $_ -eq $Collection }
    if ($foundCollection) {
        Write-Host "✅ Collezione trovata: $Collection" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Collezione non trovata (potrebbe essere normale se vuota)" -ForegroundColor Yellow
        Write-Host "   Collezioni esistenti: $($collectionsResult.Data.collections -join ', ')"
    }
} else {
    Write-Host "❌ Errore verifica collections: $($collectionsResult.Error)" -ForegroundColor Red
}

# Test 5: Query Semantica - Match Esatto
Write-Host "`nTest 5: Query Semantica - Match Esatto..." -ForegroundColor Yellow
$query1 = @{
    query_text = "coordinamento sistemi"
    limit = 5
}
$queryBody1 = $query1 | ConvertTo-Json
$queryResult1 = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $queryBody1 -Headers $uploadHeaders

if ($queryResult1.Success) {
    $matches1 = $queryResult1.Data.matches
    Write-Host "✅ Query eseguita: trovati $($matches1.Count) risultati" -ForegroundColor Green
    
    if ($matches1.Count -gt 0) {
        foreach ($match in $matches1) {
            Write-Host "   - Doc: $($match.id) (Score: $($match.similarity))" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠️  Nessun risultato trovato per query semantica" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Errore query semantica: $($queryResult1.Error)" -ForegroundColor Red
}

# Test 6: Query Semantica - Concetto Correlato
Write-Host "`nTest 6: Query Semantica - Concetto Correlato..." -ForegroundColor Yellow
$query2 = @{
    query_text = "pipeline elaborazione"
    limit = 3
}
$queryBody2 = $query2 | ConvertTo-Json
$queryResult2 = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $queryBody2 -Headers $uploadHeaders

if ($queryResult2.Success) {
    $matches2 = $queryResult2.Data.matches
    Write-Host "✅ Query correlata eseguita: trovati $($matches2.Count) risultati" -ForegroundColor Green
    
    if ($matches2.Count -gt 0) {
        foreach ($match in $matches2) {
            Write-Host "   - Doc: $($match.id) (Score: $($match.similarity))" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "❌ Errore query correlata: $($queryResult2.Error)" -ForegroundColor Red
}

# Test 7: Statistiche Sistema
Write-Host "`nTest 7: Statistiche Sistema..." -ForegroundColor Yellow
$statsResult = Test-HttpRequest -Uri "$ServiceUrl/api/database-management/vectorstore/statistics"
if ($statsResult.Success) {
    Write-Host "✅ Statistiche recuperate:" -ForegroundColor Green
    Write-Host "   - Total documents: $($statsResult.Data.total_documents)"
    Write-Host "   - Collections: $($statsResult.Data.collections_count)"
} else {
    Write-Host "⚠️  Statistiche non disponibili: $($statsResult.Error)" -ForegroundColor Yellow
}

# Cleanup opzionale (commenta se vuoi mantenere i dati di test)
Write-Host "`nCleanup: Rimozione dati di test..." -ForegroundColor Yellow
Write-Host "Per rimuovere il documento di test, esegui:"
Write-Host "curl -X DELETE '$ServiceUrl/vectorstore/document/$testDocId'" -ForegroundColor Gray

Write-Host "`n=== Test Suite Completata ===" -ForegroundColor Green
```

### Script di Test Rapido

```powershell
# quick_test.ps1 - Test rapido funzionalità base

$ServiceUrl = "http://localhost:8090"

Write-Host "Test Rapido VectorstoreService" -ForegroundColor Green

# 1. Health
$health = Invoke-RestMethod -Uri "$ServiceUrl/health"
Write-Host "Health: $($health.status)" -ForegroundColor Cyan

# 2. Documents count
$docs = Invoke-RestMethod -Uri "$ServiceUrl/vectorstore/documents"
Write-Host "Documenti esistenti: $($docs.total)" -ForegroundColor Cyan

# 3. Collections
$collections = Invoke-RestMethod -Uri "$ServiceUrl/collections/"
Write-Host "Collezioni: $($collections.collections.Count)" -ForegroundColor Cyan

# 4. Test query se ci sono documenti
if ($docs.total -gt 0) {
    $sampleDoc = $docs.documents[0]
    Write-Host "Test query su collezione: $($sampleDoc.collection)" -ForegroundColor Yellow
    
    try {
        $query = @{ query_text = "test"; limit = 2 } | ConvertTo-Json
        $result = Invoke-RestMethod -Uri "$ServiceUrl/documents/$($sampleDoc.collection)/query" -Method POST -Body $query -ContentType "application/json"
        Write-Host "Query result: $($result.total) matches" -ForegroundColor Cyan
    } catch {
        Write-Host "Query failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

## Test Nodi PDK

### Test Upload tramite Nodo chroma_vector_store

```json
{
  "test_name": "chroma_vector_store_node_test",
  "node_config": {
    "node_type": "document-semantic-complete-plugin.chroma_vector_store",
    "config": {
      "collection_name": "test_uploads",
      "service_url": "http://localhost:8090"
    }
  },
  "test_input": {
    "embeddings_input": {
      "embeddings": [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.2, 0.3, 0.4, 0.5, 0.6],
        [0.3, 0.4, 0.5, 0.6, 0.7]
      ],
      "chunks": [
        "Primo chunk di test per verificare upload",
        "Secondo chunk con contenuto semantico",
        "Terzo chunk per completare il test"
      ],
      "model": "test-embedding-model",
      "metadata": {
        "source": "test_suite",
        "test_case": "node_upload"
      }
    }
  },
  "expected_output": {
    "status": "success",
    "storage_result": {
      "documents_saved": 3,
      "collection_name": "test_uploads"
    }
  }
}
```

### Test Retrieve tramite Nodo chroma_retriever

```json
{
  "test_name": "chroma_retriever_node_test",
  "node_config": {
    "node_type": "document-semantic-complete-plugin.chroma_retriever",
    "config": {
      "collection_name": "test_uploads",
      "service_url": "http://localhost:8090",
      "similarity_threshold": 0.5,
      "top_k": 3
    }
  },
  "test_input": {
    "query_input": "contenuto semantico test",
    "query_embeddings": {
      "embeddings": [[0.25, 0.35, 0.45, 0.55, 0.65]]
    }
  },
  "expected_output": {
    "status": "success",
    "retrieved_documents": {
      "length_greater_than": 0
    }
  }
}
```

## Test Workflow Completo

### Pipeline End-to-End Test

```yaml
workflow_test:
  name: "complete_upload_retrieve_pipeline"
  nodes:
    - id: "document_input"
      type: "document_input_node"
      config:
        file_path: "./test_files/sample_document.pdf"
    
    - id: "pdf_extractor"
      type: "pdf_text_extractor"
      config:
        extraction_method: "text"
      inputs:
        pdf_file: "document_input.file_output"
    
    - id: "text_chunker"
      type: "text_chunker" 
      config:
        chunk_size: 500
        chunk_overlap: 100
      inputs:
        text_input: "pdf_extractor.text_output"
    
    - id: "embedder"
      type: "text_embedder"
      config:
        model: "sentence-transformers/all-MiniLM-L6-v2"
        batch_size: 16
      inputs:
        text_chunks: "text_chunker.chunks_output"
    
    - id: "vector_store"
      type: "chroma_vector_store"
      config:
        collection_name: "test_pipeline_collection"
        service_url: "http://localhost:8090"
      inputs:
        embeddings_input: "embedder.embeddings_output"
    
    - id: "test_query"
      type: "query_input_node"
      config:
        default_query: "contenuto del documento"
    
    - id: "retriever"
      type: "chroma_retriever"
      config:
        collection_name: "test_pipeline_collection"
        service_url: "http://localhost:8090"
        top_k: 5
      inputs:
        query_input: "test_query.query_output"

validation:
  - check: "vector_store.storage_result.status == 'success'"
  - check: "vector_store.storage_result.documents_saved > 0"
  - check: "retriever.retrieved_documents.length > 0"
  - check: "retriever.status == 'success'"
```

## Esecuzione Test

### Test Manuali
```bash
# 1. Avvia tutti i servizi
./start-all.ps1

# 2. Esegui test endpoint
bash test_endpoints.sh

# 3. Esegui test PowerShell
./test_upload_retrieve.ps1
```

### Test Automatizzati
```bash
# Test completo con cleanup
./test_upload_retrieve.ps1 -ServiceUrl "http://localhost:8090"

# Test rapido senza cleanup
./quick_test.ps1
```

### Validazione Risultati
```bash
# Controlla log del VectorstoreService
tail -f PramaIA-VectorstoreService/logs/service.log

# Controlla status dei servizi
curl http://localhost:8090/health
curl http://localhost:3001/health
curl http://localhost:8081/health
```

---

*Questi test verificano l'intera pipeline di upload e retrieve, dalla persistenza alla ricerca semantica, garantendo il corretto funzionamento del sistema PramaIA.*