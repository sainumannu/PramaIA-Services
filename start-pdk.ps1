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
if (-not (Test-Path "PramaIA-PDK\server")) {
    Write-Host "❌ Directory PDK server non trovata: PramaIA-PDK\server" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}


# Verifica che index.js esista
if (-not (Test-Path "PramaIA-PDK\server\index.js")) {
    Write-Host "❌ File index.js non trovato" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

# Avvia in una nuova finestra di terminale
Write-Host "Avvio PDK Server in nuova finestra..." -ForegroundColor Green

$Command = "cd PramaIA-PDK\server; `$env:PDK_SERVER_PORT = '$Port'; `$env:PDK_LOG_LEVEL = '$LogLevel'"
if ($Debug) {
    $Command += "; `$env:PDK_LOG_LEVEL = 'DEBUG'"
}
$Command += "; node index.js; Read-Host 'Premi Enter per chiudere'"

Start-Process powershell -ArgumentList '-NoExit', '-Command', $Command