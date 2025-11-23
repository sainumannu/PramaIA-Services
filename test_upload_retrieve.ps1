# Test Automatizzato Upload e Retrieve Documenti
# test_upload_retrieve.ps1

param(
    [string]$ServiceUrl = "http://localhost:8090",
    [string]$Collection = "test_collection_$(Get-Date -Format 'yyyyMMdd_HHmmss')",
    [switch]$SkipCleanup
)

Write-Host "=== Test Suite Upload e Retrieve Documenti ===" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "Collection: $Collection" -ForegroundColor Cyan
Write-Host ""

$testResults = @()
$testDocId = $null

# Funzione helper per test HTTP
function Test-HttpRequest {
    param($Uri, $Method = "GET", $Body = $null, $Headers = @{}, $Description = "")
    
    Write-Host "  → $Description" -ForegroundColor Gray
    
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

# Funzione per registrare risultati test
function Add-TestResult {
    param($TestName, $Success, $Message = "", $Data = $null)
    
    $script:testResults += @{
        Test = $TestName
        Success = $Success
        Message = $Message
        Timestamp = Get-Date
        Data = $Data
    }
    
    $icon = if ($Success) { "✅" } else { "❌" }
    $color = if ($Success) { "Green" } else { "Red" }
    Write-Host "$icon $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "   $Message" -ForegroundColor Gray
    }
}

# Test 1: Health Check
Write-Host "`n🏥 Test 1: Health Check..." -ForegroundColor Yellow
$healthResult = Test-HttpRequest -Uri "$ServiceUrl/health" -Description "Checking service health"
if ($healthResult.Success) {
    Add-TestResult "Health Check" $true "Service status: $($healthResult.Data.status)"
} else {
    Add-TestResult "Health Check" $false "Service unreachable: $($healthResult.Error)"
    Write-Host "`n❌ Cannot proceed without active service. Exiting." -ForegroundColor Red
    exit 1
}

# Test 2: Upload Documento
Write-Host "`n📤 Test 2: Upload Documento..." -ForegroundColor Yellow
$testDocId = "test_doc_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$testDoc = @{
    id = $testDocId
    content = "Documento di test per verificare il coordinamento tra sistemi PramaIA. Questo contenuto include informazioni sulla pipeline di embedding, ricerca semantica, e gestione metadati. Il sistema deve essere in grado di processare questo testo e renderlo ricercabile tramite query vettoriali."
    collection = $Collection
    metadata = @{
        author = "Test Automation Suite"
        document_type = "integration_test"
        created_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        test_case = "automated_upload_retrieve"
        keywords = @("coordinamento", "sistemi", "embedding", "ricerca", "pipeline")
        test_id = $testDocId
        content_length = 0
    }
    embedding = @(
        0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
        0.11, 0.21, 0.31, 0.41, 0.51, 0.61, 0.71, 0.81, 0.91, 0.91,
        0.12, 0.22, 0.32, 0.42, 0.52, 0.62, 0.72, 0.82, 0.92, 0.92
    )
}
$testDoc.metadata.content_length = $testDoc.content.Length

$uploadBody = $testDoc | ConvertTo-Json -Depth 10
$uploadHeaders = @{"Content-Type" = "application/json"}
$uploadResult = Test-HttpRequest -Uri "$ServiceUrl/vectorstore/documents" -Method POST -Body $uploadBody -Headers $uploadHeaders -Description "Uploading test document"

if ($uploadResult.Success) {
    $contentLength = $testDoc.content.Length
    Add-TestResult "Document Upload" $true "Document ID: $testDocId ($contentLength chars)"
} else {
    Add-TestResult "Document Upload" $false "Upload failed: $($uploadResult.Error)"
}

# Test 3: Verifica Upload nel Database
Write-Host "`n🔍 Test 3: Verifica Upload..." -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Attendi indicizzazione

$documentsResult = Test-HttpRequest -Uri "$ServiceUrl/vectorstore/documents" -Description "Checking uploaded documents"
if ($documentsResult.Success) {
    $foundDoc = $documentsResult.Data.documents | Where-Object { $_.id -eq $testDocId }
    if ($foundDoc) {
        Add-TestResult "Upload Verification" $true "Found in database - Collection: $($foundDoc.collection)"
        Write-Host "   Content preview: $($foundDoc.content.Substring(0, [Math]::Min(80, $foundDoc.content.Length)))..." -ForegroundColor Gray
    } else {
        Add-TestResult "Upload Verification" $false "Document not found in database"
        Write-Host "   Available documents: $($documentsResult.Data.documents.Count)" -ForegroundColor Gray
    }
} else {
    Add-TestResult "Upload Verification" $false "Error accessing documents: $($documentsResult.Error)"
}

# Test 4: Verifica Collezione
Write-Host "`n📁 Test 4: Verifica Collezione..." -ForegroundColor Yellow
$collectionsResult = Test-HttpRequest -Uri "$ServiceUrl/collections/" -Description "Checking collections"
if ($collectionsResult.Success) {
    $foundCollection = $collectionsResult.Data.collections | Where-Object { $_ -eq $Collection }
    if ($foundCollection) {
        Add-TestResult "Collection Verification" $true "Collection exists: $Collection"
    } else {
        Add-TestResult "Collection Verification" $false "Collection not found (may indicate indexing issue)"
        Write-Host "   Available collections: $($collectionsResult.Data.collections -join ', ')" -ForegroundColor Gray
    }
} else {
    Add-TestResult "Collection Verification" $false "Error accessing collections: $($collectionsResult.Error)"
}

# Test 5: Query Semantica - Match Keywords
Write-Host "`n🔎 Test 5: Query Semantica - Keywords..." -ForegroundColor Yellow
$query1 = @{
    query_text = "coordinamento sistemi PramaIA"
    limit = 5
} | ConvertTo-Json

$queryResult1 = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $query1 -Headers $uploadHeaders -Description "Querying with keywords"

if ($queryResult1.Success) {
    $matches1 = $queryResult1.Data.matches
    if ($matches1.Count -gt 0) {
        Add-TestResult "Semantic Query (Keywords)" $true "Found $($matches1.Count) matches"
        foreach ($match in $matches1[0..2]) {  # Show first 3
            if ($match.id -eq $testDocId) {
                Write-Host "   ✓ Test document found (similarity: $($match.similarity))" -ForegroundColor Green
            } else {
                Write-Host "   • Other match: $($match.id) (similarity: $($match.similarity))" -ForegroundColor Gray
            }
        }
    } else {
        Add-TestResult "Semantic Query (Keywords)" $false "No results found - possible indexing issue"
    }
} else {
    Add-TestResult "Semantic Query (Keywords)" $false "Query failed: $($queryResult1.Error)"
}

# Test 6: Query Semantica - Concetti Correlati
Write-Host "`n🧠 Test 6: Query Semantica - Concetti..." -ForegroundColor Yellow
$query2 = @{
    query_text = "pipeline embedding ricerca"
    limit = 3
} | ConvertTo-Json

$queryResult2 = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $query2 -Headers $uploadHeaders -Description "Querying with semantic concepts"

if ($queryResult2.Success) {
    $matches2 = $queryResult2.Data.matches
    if ($matches2.Count -gt 0) {
        Add-TestResult "Semantic Query (Concepts)" $true "Found $($matches2.Count) semantic matches"
        foreach ($match in $matches2) {
            if ($match.id -eq $testDocId) {
                Write-Host "   ✓ Test document matched semantically (similarity: $($match.similarity))" -ForegroundColor Green
            }
        }
    } else {
        Add-TestResult "Semantic Query (Concepts)" $false "No semantic matches found"
    }
} else {
    Add-TestResult "Semantic Query (Concepts)" $false "Semantic query failed: $($queryResult2.Error)"
}

# Test 7: Query con Soglia di Similarità 
Write-Host "`n📊 Test 7: Query con Soglia..." -ForegroundColor Yellow
$query3 = @{
    query_text = "gestione metadati"
    limit = 5
    similarity_threshold = 0.3
} | ConvertTo-Json

$queryResult3 = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $query3 -Headers $uploadHeaders -Description "Testing similarity threshold"

if ($queryResult3.Success) {
    $matches3 = $queryResult3.Data.matches
    Add-TestResult "Similarity Threshold Query" $true "Query executed with threshold (found: $($matches3.Count))"
} else {
    Add-TestResult "Similarity Threshold Query" $false "Threshold query failed: $($queryResult3.Error)"
}

# Test 8: Statistiche Sistema
Write-Host "`n📈 Test 8: Statistiche Sistema..." -ForegroundColor Yellow
$statsResult = Test-HttpRequest -Uri "$ServiceUrl/api/database-management/vectorstore/statistics" -Description "Getting system statistics"
if ($statsResult.Success) {
    $stats = $statsResult.Data
    Add-TestResult "System Statistics" $true "Retrieved successfully"
    Write-Host "   • Total documents: $($stats.total_documents)" -ForegroundColor Cyan
    Write-Host "   • Collections: $($stats.collections_count)" -ForegroundColor Cyan
    Write-Host "   • Database size: $([Math]::Round($stats.database_size_mb, 2)) MB" -ForegroundColor Cyan
} else {
    Add-TestResult "System Statistics" $false "Stats unavailable: $($statsResult.Error)"
}

# Test 9: Performance Test
Write-Host "`n⚡ Test 9: Performance Test..." -ForegroundColor Yellow
$startTime = Get-Date
$perfQuery = @{
    query_text = "test performance"
    limit = 1
} | ConvertTo-Json

$perfResult = Test-HttpRequest -Uri "$ServiceUrl/documents/$Collection/query" -Method POST -Body $perfQuery -Headers $uploadHeaders -Description "Measuring query performance"
$endTime = Get-Date
$queryTime = ($endTime - $startTime).TotalMilliseconds

if ($perfResult.Success) {
    $performanceGood = $queryTime -lt 1000  # Under 1 second
    Add-TestResult "Query Performance" $performanceGood "Query time: ${queryTime} ms"
} else {
    Add-TestResult "Query Performance" $false "Performance test failed"
}

# Cleanup (se non skippato)
if (-not $SkipCleanup) {
    Write-Host "`n🧹 Cleanup: Rimozione dati di test..." -ForegroundColor Yellow
    Write-Host "Per mantenere i dati di test, usa il flag -SkipCleanup" -ForegroundColor Gray
    
    # Note: API di deletion specifica da implementare se disponibile
    Write-Host "   Manual cleanup command:" -ForegroundColor Gray
    Write-Host "   curl -X DELETE '$ServiceUrl/vectorstore/document/$testDocId'" -ForegroundColor Gray
}

# Report finale
Write-Host "`n📋 === REPORT FINALE ===" -ForegroundColor Green
$successCount = ($testResults | Where-Object { $_.Success }).Count
$totalTests = $testResults.Count
$successRate = [Math]::Round(($successCount / $totalTests) * 100, 1)

$successRate = [math]::Round(($successCount / $totalTests) * 100, 1)
Write-Host "Risultati: $successCount/$totalTests test passed ($successRate%)" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $testResults) {
    $icon = if ($result.Success) { "✅" } else { "❌" }
    $color = if ($result.Success) { "Green" } else { "Red" }
    Write-Host "$icon $($result.Test)" -ForegroundColor $color
    if ($result.Message) {
        Write-Host "   $($result.Message)" -ForegroundColor Gray
    }
}

# Raccomandazioni
Write-Host "`nRaccomandazioni:" -ForegroundColor Yellow
if ($successRate -lt 80) {
    Write-Host "   • Verificare che tutti i servizi siano attivi" -ForegroundColor Red
    Write-Host "   • Controllare i log del VectorstoreService" -ForegroundColor Red
    Write-Host "   • Verificare la configurazione della pipeline" -ForegroundColor Red
} elseif ($successRate -lt 100) {
    Write-Host "   • Alcuni test sono falliti - controllare i log per dettagli" -ForegroundColor Yellow
} else {
    Write-Host "   • Tutti i test sono passati! Sistema funziona correttamente ✨" -ForegroundColor Green
}

Write-Host "`nTest Document ID: $testDocId" -ForegroundColor Cyan
Write-Host "Test Collection: $Collection" -ForegroundColor Cyan

if ($successRate -ge 80) {
    exit 0
} else {
    exit 1
}