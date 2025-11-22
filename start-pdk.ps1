#!/usr/bin/env pwsh
# Script di avvio per PDK Server

param(
    [string]$Port = "3001",
    [string]$LogLevel = "INFO",
    [switch]$Debug
)

Write-Host "🚀 Avvio PDK Server..." -ForegroundColor Green
Write-Host "   Porta: $Port" -ForegroundColor Gray
Write-Host "   Log Level: $LogLevel" -ForegroundColor Gray

# Verifica che la directory PDK esista
if (-not (Test-Path "C:\PramaIA\PramaIA-PDK\server")) {
    Write-Host "❌ Directory PDK server non trovata: C:\PramaIA\PramaIA-PDK\server" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

# Verifica che plugin-api-server.js esista
if (-not (Test-Path "C:\PramaIA\PramaIA-PDK\server\plugin-api-server.js")) {
    Write-Host "❌ File plugin-api-server.js non trovato" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

Set-Location "C:\PramaIA\PramaIA-PDK\server"

# Imposta variabili d'ambiente
$env:PDK_SERVER_PORT = $Port
$env:PDK_LOG_LEVEL = $LogLevel

if ($Debug) {
    $env:PDK_LOG_LEVEL = "DEBUG"
    Write-Host "   Debug: Abilitato" -ForegroundColor Yellow
}

try {
    Write-Host "Comando: node plugin-api-server.js" -ForegroundColor Yellow
    node plugin-api-server.js
} catch {
    Write-Host "❌ Errore avvio PDK server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
    Write-Host "   - Verifica che Node.js sia installato e nel PATH" -ForegroundColor Gray
    Write-Host "   - Controlla che le dipendenze Node.js siano installate: npm install" -ForegroundColor Gray
    Write-Host "   - Assicurati che la porta $Port non sia già in uso" -ForegroundColor Gray
    Write-Host "   - Verifica che i plugin nella directory plugins/ siano validi" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
}