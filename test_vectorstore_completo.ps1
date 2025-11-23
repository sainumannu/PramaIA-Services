# TEST COMPLETO VECTORSTORE CON SUCCESSO
Write-Host "=== TEST COMPLETO VECTORSTORE ===" -ForegroundColor Cyan

# Test 1: Upload documento direttamente nella collezione esistente "manuals"
Write-Host "`n1. Test Upload in collezione esistente 'manuals'..." -ForegroundColor Yellow

$testDoc = @{
    id = "test_success_$(Get-Date -Format 'HHmmss')"
    content = "Documento di test per verificare coordinamento e funzionamento della ricerca semantica"
    collection = "manuals"  # Uso collezione che già esiste
    metadata = @{
        source = "test_success"
        document_type = "test"
        created_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        test_marker = "success_test"
    }
}

try {
    $uploadBody = $testDoc | ConvertTo-Json -Depth 10
    $uploadResult = Invoke-RestMethod -Uri "http://localhost:8090/documents" -Method POST -Body $uploadBody -ContentType "application/json"
    Write-Host "   ✅ Upload riuscito: $($uploadResult.id)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Upload fallito: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Verifica documenti nella collezione manuals
Write-Host "`n2. Verifica documenti in collezione 'manuals'..." -ForegroundColor Yellow
try {
    $docs = Invoke-RestMethod -Uri "http://localhost:8090/vectorstore/documents?collection=manuals"
    Write-Host "   📂 Documenti in 'manuals': $($docs.documents.Count)" -ForegroundColor Green
    $docs.documents | ForEach-Object {
        $content = if ($_.content.Length -gt 60) { $_.content.Substring(0, 60) + "..." } else { $_.content }
        Write-Host "     - $($_.id): $content" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ Errore: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Query con parametri che DOVREBBERO funzionare
Write-Host "`n3. Test Query semantica..." -ForegroundColor Yellow

$queryParams = @{
    query_text = "coordinamento"
    limit = 10
    top_k = 10
}

try {
    $queryBody = $queryParams | ConvertTo-Json
    $queryResult = Invoke-RestMethod -Uri "http://localhost:8090/documents/manuals/query" -Method POST -Body $queryBody -ContentType "application/json"
    
    Write-Host "   ✅ Query eseguita con successo!" -ForegroundColor Green
    Write-Host "     Status: $($queryResult.status)" -ForegroundColor White
    Write-Host "     Documenti trovati: $($queryResult.documents.Count)" -ForegroundColor White
    
    if ($queryResult.documents -and $queryResult.documents.Count -gt 0) {
        Write-Host "     📋 Risultati:" -ForegroundColor Cyan
        $queryResult.documents | ForEach-Object {
            $content = if ($_.document.Length -gt 80) { $_.document.Substring(0, 80) + "..." } else { $_.document }
            Write-Host "       - Score: $($_.similarity_score) | ID: $($_.document_id)" -ForegroundColor Yellow
            Write-Host "       - Content: $content" -ForegroundColor Gray
        }
    } else {
        Write-Host "     ⚠️ Query riuscita ma NESSUN risultato trovato!" -ForegroundColor Yellow
        Write-Host "     Possibili cause:" -ForegroundColor Yellow
        Write-Host "       - Documenti senza embeddings nel vectorstore" -ForegroundColor Gray
        Write-Host "       - Soglia di similarità troppo alta" -ForegroundColor Gray
        Write-Host "       - Problema nell'indicizzazione vettoriale" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "   ❌ Query fallita: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Prova query con soglia più bassa
Write-Host "`n4. Test Query con parametri più permissivi..." -ForegroundColor Yellow

$relaxedQuery = @{
    query_text = "test"
    limit = 50
    similarity_threshold = 0.0  # Soglia molto bassa
}

try {
    $queryBody = $relaxedQuery | ConvertTo-Json
    $queryResult = Invoke-RestMethod -Uri "http://localhost:8090/documents/manuals/query" -Method POST -Body $queryBody -ContentType "application/json"
    
    Write-Host "   🔍 Query permissiva - Risultati: $($queryResult.documents.Count)" -ForegroundColor Green
    
    if ($queryResult.documents -and $queryResult.documents.Count -gt 0) {
        Write-Host "     ✅ SUCCESSO! Trovati risultati con soglia bassa" -ForegroundColor Green
        $queryResult.documents | Select-Object -First 3 | ForEach-Object {
            Write-Host "       - Score: $($_.similarity_score) | $($_.document.Substring(0, 50))..." -ForegroundColor White
        }
    } else {
        Write-Host "     ❌ Ancora nessun risultato - problema negli embeddings" -ForegroundColor Red
    }
    
} catch {
    Write-Host "   ❌ Query permissiva fallita: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== CONCLUSIONI ===" -ForegroundColor Cyan
Write-Host "Se le query restituiscono 0 risultati anche con soglia bassa," -ForegroundColor Yellow
Write-Host "il problema è che i documenti nel SQLite NON hanno embeddings" -ForegroundColor Yellow
Write-Host "nel vectorstore ChromaDB. Il nodo chroma_vector_store NON sta" -ForegroundColor Yellow  
Write-Host "salvando gli embeddings perché manca service_url nella config!" -ForegroundColor Yellow
Write-Host "`nSOLUZIONE: Usare la configurazione corretta con service_url" -ForegroundColor Green