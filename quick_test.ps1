# Test Rapido VectorstoreService
# quick_test.ps1

param(
    [string]$ServiceUrl = "http://localhost:8090"
)

Write-Host "🚀 Test Rapido VectorstoreService" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param($Uri, $Description)
    
    try {
        $result = Invoke-RestMethod -Uri $Uri -ErrorAction Stop
        Write-Host "✅ $Description" -ForegroundColor Green
        return $result
    } catch {
        Write-Host "❌ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Test-PostEndpoint {
    param($Uri, $Body, $Description)
    
    try {
        $result = Invoke-RestMethod -Uri $Uri -Method POST -Body $Body -ContentType "application/json" -ErrorAction Stop
        Write-Host "✅ $Description" -ForegroundColor Green
        return $result
    } catch {
        Write-Host "❌ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 1. Health Check
Write-Host "1. Health Check..." -ForegroundColor Yellow
$health = Test-Endpoint -Uri "$ServiceUrl/health" -Description "Service Health"
if ($health) {
    Write-Host "   Status: $($health.status)" -ForegroundColor Cyan
}

# 2. Documents Count
Write-Host "`n2. Documenti Esistenti..." -ForegroundColor Yellow
$docs = Test-Endpoint -Uri "$ServiceUrl/vectorstore/documents" -Description "Documents List"
if ($docs) {
    Write-Host "   Documenti totali: $($docs.total)" -ForegroundColor Cyan
    if ($docs.total -gt 0) {
        Write-Host "   Primo documento: $($docs.documents[0].id) (Collection: $($docs.documents[0].collection))" -ForegroundColor Gray
    }
}

# 3. Collections
Write-Host "`n3. Collezioni..." -ForegroundColor Yellow
$collections = Test-Endpoint -Uri "$ServiceUrl/collections/" -Description "Collections List"
if ($collections) {
    Write-Host "   Collezioni totali: $($collections.collections.Count)" -ForegroundColor Cyan
    if ($collections.collections.Count -gt 0) {
        Write-Host "   Collezioni: $($collections.collections -join ', ')" -ForegroundColor Gray
    }
}

# 4. Test Query (solo se ci sono documenti)
if ($docs -and $docs.total -gt 0) {
    Write-Host "`n4. Test Query..." -ForegroundColor Yellow
    $sampleDoc = $docs.documents[0]
    Write-Host "   Testando query su collezione: $($sampleDoc.collection)" -ForegroundColor Gray
    
    $query = @{ 
        query_text = "test sample query"
        limit = 2 
    } | ConvertTo-Json
    
    $queryResult = Test-PostEndpoint -Uri "$ServiceUrl/documents/$($sampleDoc.collection)/query" -Body $query -Description "Sample Query"
    if ($queryResult) {
        Write-Host "   Risultati trovati: $($queryResult.total)" -ForegroundColor Cyan
        if ($queryResult.matches -and $queryResult.matches.Count -gt 0) {
            Write-Host "   Primo risultato: $($queryResult.matches[0].id) (Score: $($queryResult.matches[0].similarity))" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "`n4. Test Query..." -ForegroundColor Yellow  
    Write-Host "   ⏭️  Nessun documento disponibile per test query" -ForegroundColor Gray
}

# 5. Statistics
Write-Host "`n5. Statistiche Sistema..." -ForegroundColor Yellow
$stats = Test-Endpoint -Uri "$ServiceUrl/api/database-management/vectorstore/statistics" -Description "System Statistics"
if ($stats) {
    Write-Host "   Total documents: $($stats.total_documents)" -ForegroundColor Cyan
    Write-Host "   Collections count: $($stats.collections_count)" -ForegroundColor Cyan
    if ($stats.database_size_mb) {
        Write-Host "   Database size: $([Math]::Round($stats.database_size_mb, 2)) MB" -ForegroundColor Cyan
    }
}

# 6. Dependencies Health
Write-Host "`n6. Dipendenze..." -ForegroundColor Yellow  
$deps = Test-Endpoint -Uri "$ServiceUrl/health/dependencies" -Description "Dependencies Health"
if ($deps) {
    foreach ($dep in $deps.PSObject.Properties) {
        $status = if ($dep.Value -eq "ok") { "✅" } else { "❌" }
        Write-Host "   $status $($dep.Name): $($dep.Value)" -ForegroundColor Cyan
    }
}

Write-Host "`n🏁 Test rapido completato!" -ForegroundColor Green

# Summary
$servicesOk = $health -and $health.status -eq "ok"
$hasData = $docs -and $docs.total -gt 0
$collectionsOk = $collections -ne $null

Write-Host "`n📊 Riassunto:" -ForegroundColor Yellow
Write-Host "   • Service Health: $(if ($servicesOk) { '✅ OK' } else { '❌ FAIL' })" -ForegroundColor $(if ($servicesOk) { 'Green' } else { 'Red' })
Write-Host "   • Ha Dati: $(if ($hasData) { '✅ SI' } else { '⚠️  NO' })" -ForegroundColor $(if ($hasData) { 'Green' } else { 'Yellow' })
Write-Host "   • Collections API: $(if ($collectionsOk) { '✅ OK' } else { '❌ FAIL' })" -ForegroundColor $(if ($collectionsOk) { 'Green' } else { 'Red' })

if ($servicesOk -and $collectionsOk) {
    Write-Host "`n💡 Il sistema è operativo!" -ForegroundColor Green
    if (-not $hasData) {
        Write-Host "   Per testare completamente, aggiungi alcuni documenti." -ForegroundColor Yellow
        Write-Host "   Esegui: ./test_upload_retrieve.ps1" -ForegroundColor Cyan
    }
} else {
    Write-Host "`n⚠️  Alcuni componenti hanno problemi. Verifica i log dei servizi." -ForegroundColor Red
}