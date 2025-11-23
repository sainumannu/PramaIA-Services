# Test rapido per verificare funzionamento vectorstore
Write-Host "=== TEST VECTORSTORE RAPIDO ===" -ForegroundColor Cyan

$VectorstoreUrl = "http://localhost:8090"

# Test 1: Health check
Write-Host "`n1. Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$VectorstoreUrl/health" -Method GET -TimeoutSec 10
    Write-Host "   OK: VectorstoreService attivo" -ForegroundColor Green
} catch {
    Write-Host "   ERRORE: VectorstoreService non raggiungibile - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Verifica collezioni esistenti
Write-Host "`n2. Verifica collezioni..." -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "$VectorstoreUrl/collections" -Method GET
    Write-Host "   Collezioni trovate: $($collections.collections.Count)" -ForegroundColor Green
    foreach ($col in $collections.collections) {
        Write-Host "     - $($col.name): $($col.count) documenti" -ForegroundColor White
    }
} catch {
    Write-Host "   ERRORE: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Upload di un documento test
Write-Host "`n3. Test upload documento..." -ForegroundColor Yellow
$testDoc = @{
    content = "Test contenuto per verificare il coordinamento tra sistemi PramaIA"
    metadata = @{
        source = "test_vectorstore"
        document_type = "test"
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    }
    embeddings = @(
        @(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    )
}

try {
    $uploadBody = $testDoc | ConvertTo-Json -Depth 10
    $uploadResult = Invoke-RestMethod -Uri "$VectorstoreUrl/vectorstore/documents" -Method POST -Body $uploadBody -ContentType "application/json"
    Write-Host "   OK: Documento caricato con successo" -ForegroundColor Green
    Write-Host "     ID: $($uploadResult.document_id)" -ForegroundColor White
} catch {
    Write-Host "   ERRORE upload: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Verifica collezioni dopo upload
Write-Host "`n4. Verifica dopo upload..." -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "$VectorstoreUrl/collections" -Method GET
    foreach ($col in $collections.collections) {
        Write-Host "   - $($col.name): $($col.count) documenti" -ForegroundColor Green
    }
} catch {
    Write-Host "   ERRORE: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Query di ricerca
Write-Host "`n5. Test query..." -ForegroundColor Yellow
$queryBody = @{
    query_text = "coordinamento sistemi"
    limit = 3
} | ConvertTo-Json

try {
    $queryResult = Invoke-RestMethod -Uri "$VectorstoreUrl/documents/pdf_documents/query" -Method POST -Body $queryBody -ContentType "application/json"
    Write-Host "   OK: Query eseguita - $($queryResult.documents.Count) risultati" -ForegroundColor Green
} catch {
    Write-Host "   Query su pdf_documents fallita, provo con documents..." -ForegroundColor Yellow
    try {
        $queryResult = Invoke-RestMethod -Uri "$VectorstoreUrl/documents/documents/query" -Method POST -Body $queryBody -ContentType "application/json"
        Write-Host "   OK: Query su 'documents' - $($queryResult.documents.Count) risultati" -ForegroundColor Green
    } catch {
        Write-Host "   ERRORE query: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== FINE TEST ===" -ForegroundColor Cyan