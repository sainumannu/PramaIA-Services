#!/usr/bin/env pwsh
# Script di avvio per Document Monitor Agent

param(
    [string]$Port = "8001",
    [string]$Host = "127.0.0.1",
    [switch]$Debug
)

Write-Host "🚀 Avvio Document Monitor Agent..." -ForegroundColor Green
Write-Host "   Porta: $Port" -ForegroundColor Gray
Write-Host "   Host: $Host" -ForegroundColor Gray

# Verifica che la directory document-folder-monitor-agent esista
if (-not (Test-Path "C:\PramaIA\PramaIA-Agents\document-folder-monitor-agent")) {
    Write-Host "❌ Directory document-folder-monitor-agent non trovata" -ForegroundColor Red
    Write-Host "   Percorso atteso: C:\PramaIA\PramaIA-Agents\document-folder-monitor-agent" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
    exit 1
}

# Verifica che src/main.py esista
if (-not (Test-Path "C:\PramaIA\PramaIA-Agents\document-folder-monitor-agent\src\main.py")) {
    Write-Host "❌ File main.py non trovato in src/" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

Set-Location "C:\PramaIA\PramaIA-Agents\document-folder-monitor-agent"

# Imposta variabili d'ambiente
$env:PLUGIN_PDF_MONITOR_PORT = $Port
$env:PLUGIN_PDF_MONITOR_HOST = $Host

if ($Debug) {
    $env:LOG_LEVEL = "DEBUG"
    Write-Host "   Debug: Abilitato" -ForegroundColor Yellow
}

try {
    Write-Host "Comando: uvicorn src.main:app --host $Host --port $Port" -ForegroundColor Yellow
    uvicorn src.main:app --host $Host --port $Port
} catch {
    Write-Host "❌ Errore avvio document monitor: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
    Write-Host "   - Verifica che Python sia installato e nel PATH" -ForegroundColor Gray
    Write-Host "   - Controlla che le dipendenze siano installate" -ForegroundColor Gray
    Write-Host "   - Verifica che la porta $Port non sia già in uso" -ForegroundColor Gray
    Write-Host "   - Controlla che il file di configurazione folder_monitor.py sia corretto" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
}