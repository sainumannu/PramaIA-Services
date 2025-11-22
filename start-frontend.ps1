#!/usr/bin/env pwsh
# Script di avvio per Frontend React

param(
    [string]$Port = "3000",
    [switch]$Debug,
    [switch]$NoBrowser
)

Write-Host "🚀 Avvio Frontend React..." -ForegroundColor Green
Write-Host "   Porta: $Port" -ForegroundColor Gray

# Verifica che la directory frontend esista
if (-not (Test-Path "C:\PramaIA\PramaIAServer\frontend\client")) {
    Write-Host "❌ Directory frontend non trovata: C:\PramaIA\PramaIAServer\frontend\client" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

# Verifica che package.json esista
if (-not (Test-Path "C:\PramaIA\PramaIAServer\frontend\client\package.json")) {
    Write-Host "❌ File package.json non trovato" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

Set-Location "C:\PramaIA\PramaIAServer\frontend\client"

# Imposta variabili d'ambiente
$env:PORT = $Port
$env:REACT_APP_FRONTEND_PORT = $Port

if ($NoBrowser) {
    $env:BROWSER = "none"
    Write-Host "   Browser automatico: Disabilitato" -ForegroundColor Yellow
}

if ($Debug) {
    $env:REACT_APP_LOG_LEVEL = "DEBUG"
    Write-Host "   Debug: Abilitato" -ForegroundColor Yellow
}

# Verifica che node_modules sia presente
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Directory node_modules non trovata. Installazione dipendenze..." -ForegroundColor Yellow
    try {
        npm install
        Write-Host "✅ Dipendenze installate con successo" -ForegroundColor Green
    } catch {
        Write-Host "❌ Errore nell'installazione delle dipendenze" -ForegroundColor Red
        Read-Host "Premi Enter per uscire"
        exit 1
    }
}

try {
    Write-Host "Comando: npm start" -ForegroundColor Yellow
    npm start
} catch {
    Write-Host "❌ Errore avvio frontend: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
    Write-Host "   - Verifica che Node.js e npm siano installati e nel PATH" -ForegroundColor Gray
    Write-Host "   - Controlla che le dipendenze siano installate: npm install" -ForegroundColor Gray
    Write-Host "   - Assicurati che la porta $Port non sia già in uso" -ForegroundColor Gray
    Write-Host "   - Verifica che non ci siano errori di sintassi nel codice React" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
}