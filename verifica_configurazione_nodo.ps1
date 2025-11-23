# verifica_configurazione_nodo.ps1
# Script per verificare e diagnosticare problemi di configurazione del nodo chroma_vector_store

Write-Host "=== VERIFICA CONFIGURAZIONE CHROMA_VECTOR_STORE ===" -ForegroundColor Cyan

# 1. Verifica VectorstoreService
Write-Host "`n1. Verifico VectorstoreService..." -ForegroundColor Yellow
try {
    $service = Invoke-RestMethod -Uri "http://localhost:8090/health" -Method GET -TimeoutSec 5
    Write-Host "✓ VectorstoreService attivo: $($service.status)" -ForegroundColor Green
} catch {
    Write-Host "✗ VectorstoreService NON raggiungibile!" -ForegroundColor Red
    Write-Host "  ERRORE: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  SOLUZIONE: Avviare il VectorstoreService con './start-vectorstore.ps1'" -ForegroundColor Yellow
    exit 1
}

# 2. Lista collezioni esistenti
Write-Host "`n2. Collezioni esistenti:" -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "http://localhost:8090/collections" -Method GET
    if ($collections.collections.Count -eq 0) {
        Write-Host "⚠ NESSUNA collezione trovata!" -ForegroundColor Red
        Write-Host "  Questo spiega perché la ricerca non funziona!" -ForegroundColor Yellow
    } else {
        foreach ($collection in $collections.collections) {
            $count = if ($collection.count) { $collection.count } else { "N/A" }
            Write-Host "  - $($collection.name): $count documenti" -ForegroundColor Green
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
    if ($collection.metadata) {
        Write-Host "  - Metadati: $($collection.metadata | ConvertTo-Json -Compress)" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Collezione 'pdf_documents' NON trovata!" -ForegroundColor Red
    Write-Host "  Verifica se esistono altre collezioni con nomi diversi..." -ForegroundColor Yellow
    
    # Proviamo con collection names alternativi
    $altNames = @("documents", "manuals", "default")
    foreach ($altName in $altNames) {
        try {
            $altCollection = Invoke-RestMethod -Uri "http://localhost:8090/collections/$altName" -Method GET -ErrorAction Stop
            Write-Host "  ✓ Trovata collezione alternativa '$altName': $($altCollection.count) documenti" -ForegroundColor Cyan
        } catch {
            # Collezione non esistente, ignora
        }
    }
}

# 4. Verifica endpoint di ricerca
Write-Host "`n4. Test endpoint di ricerca:" -ForegroundColor Yellow
try {
    $queryBody = @{
        query_text = "test"
        limit = 3
    } | ConvertTo-Json
    
    $searchResult = Invoke-RestMethod -Uri "http://localhost:8090/documents/pdf_documents/query" -Method POST -Body $queryBody -ContentType "application/json"
    
    if ($searchResult.documents -and $searchResult.documents.Count -gt 0) {
        Write-Host "✓ Endpoint di ricerca funzionante: $($searchResult.documents.Count) risultati" -ForegroundColor Green
    } else {
        Write-Host "⚠ Endpoint raggiungibile ma NESSUN risultato trovato!" -ForegroundColor Yellow
        Write-Host "  Possibili cause:" -ForegroundColor Yellow
        Write-Host "    - Collection vuota (documenti non indicizzati)" -ForegroundColor Yellow
        Write-Host "    - Soglia di similarità troppo alta" -ForegroundColor Yellow
        Write-Host "    - Mismatch nella configurazione embeddings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Errore test ricerca: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== ANALISI CONFIGURAZIONE NODO ===" -ForegroundColor Cyan

# 5. Analisi configurazione attuale vs raccomandata
Write-Host "`nCONFIGURAZIONE ATTUALE (problematica):" -ForegroundColor Red
$currentConfig = @'
{
    "collection_name": "pdf_documents",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "operation": "add"
}
'@
Write-Host $currentConfig -ForegroundColor White

Write-Host "`nCONFIGURAZIONE CORRETTA raccomandata:" -ForegroundColor Green
$correctConfig = @{
    node_type = "document-semantic-complete-plugin.chroma_vector_store"
    config = @{
        collection_name = "pdf_documents"
        service_url = "http://localhost:8090"
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        operation = "add"
        distance_metric = "cosine"
        metadata_fields = @("source", "page", "document_type")
        batch_size = 20
        retry_attempts = 3
        timeout = 30
    }
} | ConvertTo-Json -Depth 5
Write-Host $correctConfig -ForegroundColor White

Write-Host "`n=== PARAMETRI CRITICI MANCANTI ===" -ForegroundColor Cyan
$missingParams = @(
    "✗ service_url - ESSENZIALE per connessione VectorstoreService",
    "✗ metadata_fields - IMPORTANTE per metadati e filtri",
    "✗ distance_metric - IMPORTANTE per tipo di similarità",
    "✗ batch_size - PERFORMANCE per elaborazione efficiente", 
    "✗ retry_attempts - AFFIDABILITÀ per gestione errori",
    "✗ timeout - STABILITÀ per timeout chiamate"
)

foreach ($param in $missingParams) {
    Write-Host "  $param" -ForegroundColor Red
}

Write-Host "`n=== AZIONI IMMEDIATE RICHIESTE ===" -ForegroundColor Cyan
Write-Host "1. Aggiornare configurazione nodo con parametri mancanti" -ForegroundColor Yellow
Write-Host "2. Aggiungere service_url = 'http://localhost:8090'" -ForegroundColor Yellow  
Write-Host "3. Specificare metadata_fields per migliorare ricerca" -ForegroundColor Yellow
Write-Host "4. Verificare che documenti siano effettivamente indicizzati" -ForegroundColor Yellow
Write-Host "5. Testare pipeline completo dopo aggiornamento" -ForegroundColor Yellow

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. Aggiornare file di configurazione workflow" -ForegroundColor Green
Write-Host "2. Riavviare il servizio con nuova configurazione" -ForegroundColor Green
Write-Host "3. Eseguire test: ./test_upload_retrieve.ps1" -ForegroundColor Green
Write-Host "4. Verificare indicizzazione e ricerca funzionanti" -ForegroundColor Green

Write-Host "`n=== FINE DIAGNOSTICA ===" -ForegroundColor Cyan