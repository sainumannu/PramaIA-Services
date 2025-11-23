# TEST_FIX_RAPIDO.ps1 - Test per verificare se il fix funziona

Write-Host "=== TEST FIX CONFIGURAZIONE NODO ===" -ForegroundColor Cyan

# 1. Controllo stato iniziale
Write-Host "`n1. Stato PRIMA del fix:" -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "http://localhost:8090/collections"
    Write-Host "  Collezioni esistenti: $($collections.collections.Count)" -ForegroundColor White
} catch {
    Write-Host "  ERRORE: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n2. CONFIGURAZIONE DA APPLICARE:" -ForegroundColor Yellow
Write-Host @"
{
    "node_type": "document-semantic-complete-plugin.chroma_vector_store",
    "config": {
        "collection_name": "pdf_documents",
        "service_url": "`${VECTORSTORE_SERVICE_URL}",           <-- USA VARIABILE ENV!
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "operation": "add",
        "distance_metric": "cosine",
        "metadata_fields": ["source", "page", "document_type"],
        "batch_size": "`${VECTORSTORE_BATCH_SIZE}",
        "retry_attempts": "`${VECTORSTORE_RETRY_ATTEMPTS}",
        "timeout": "`${VECTORSTORE_TIMEOUT}"
    }
}

AGGIUNTO IN PramaIA-PDK/.env:
VECTORSTORE_SERVICE_URL=http://localhost:8090
VECTORSTORE_TIMEOUT=30
VECTORSTORE_RETRY_ATTEMPTS=3
VECTORSTORE_BATCH_SIZE=20
"@ -ForegroundColor Green

Write-Host "`n3. ISTRUZIONI:" -ForegroundColor Yellow
Write-Host "  a. Copia la configurazione sopra" -ForegroundColor White
Write-Host "  b. Sostituiscila nel file di workflow dell'altro workspace" -ForegroundColor White  
Write-Host "  c. Riavvia il workflow/servizio" -ForegroundColor White
Write-Host "  d. Rilancia il test di upload" -ForegroundColor White

Write-Host "`n4. VERIFICA POST-FIX:" -ForegroundColor Yellow
Write-Host "  Dopo il fix, dovrebbe creare automaticamente la collezione 'pdf_documents'" -ForegroundColor White
Write-Host "  Esegui: ./test_upload_retrieve.ps1 per verificare" -ForegroundColor White

Write-Host "`n=== FINE TEST ===" -ForegroundColor Cyan