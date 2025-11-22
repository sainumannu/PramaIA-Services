#!/usr/bin/env pwsh
# Script di avvio per VectorStore Service

param(
    [string]$Port = "8090",
    [string]$Host = "127.0.0.1",
    [switch]$Debug
)

Write-Host "🚀 Avvio VectorStore Service..." -ForegroundColor Green
Write-Host "   Porta: $Port" -ForegroundColor Gray
Write-Host "   Host: $Host" -ForegroundColor Gray

# Verifica che la directory VectorStore esista
if (-not (Test-Path "C:\PramaIA\PramaIA-VectorstoreService")) {
    Write-Host "❌ Directory VectorStore Service non trovata: C:\PramaIA\PramaIA-VectorstoreService" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

# Verifica che main.py esista
if (-not (Test-Path "C:\PramaIA\PramaIA-VectorstoreService\main.py")) {
    Write-Host "❌ File main.py non trovato" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

Set-Location "C:\PramaIA\PramaIA-VectorstoreService"

# Imposta variabili d'ambiente
$env:VECTORSTORE_SERVICE_PORT = $Port
$env:VECTORSTORE_SERVICE_HOST = $Host

if ($Debug) {
    $env:LOG_LEVEL = "DEBUG"
    Write-Host "   Debug: Abilitato" -ForegroundColor Yellow
}

try {
    Write-Host "Comando: python main.py" -ForegroundColor Yellow
    python main.py
} catch {
    Write-Host "❌ Errore avvio VectorStore Service: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
    Write-Host "   - Verifica che Python sia installato e nel PATH" -ForegroundColor Gray
    Write-Host "   - Controlla che le dipendenze siano installate: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "   - Assicurati che la porta $Port non sia già in uso" -ForegroundColor Gray
    Write-Host "   - Verifica configurazioni ChromaDB e variabili d'ambiente" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
}