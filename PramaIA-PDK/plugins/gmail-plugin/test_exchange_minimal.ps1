# Exchange Plugin Test - Versione Base
Write-Host "Exchange/Office 365 Plugin Test" -ForegroundColor Cyan
Write-Host "===============================" 

Write-Host "`nVerifica dipendenze..." -ForegroundColor Yellow

# Test Python
try {
    $pythonVer = & python --version 2>&1
    Write-Host "Python: $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "Python non trovato" -ForegroundColor Red
}

# Test MSAL
try {
    $msalTest = & python -c "import msal; print(msal.__version__)" 2>&1
    Write-Host "MSAL: $msalTest" -ForegroundColor Green
} catch {
    Write-Host "MSAL non installato - pip install msal" -ForegroundColor Red
}

# Files disponibili
Write-Host "`nFiles configurazione:" -ForegroundColor Cyan
if (Test-Path "config_exchange_template.json") {
    Write-Host "- config_exchange_template.json (disponibile)" -ForegroundColor Green
} else {
    Write-Host "- config_exchange_template.json (mancante)" -ForegroundColor Red
}

if (Test-Path "EXCHANGE_SETUP_GUIDE.md") {
    Write-Host "- EXCHANGE_SETUP_GUIDE.md (disponibile)" -ForegroundColor Green
} else {
    Write-Host "- EXCHANGE_SETUP_GUIDE.md (mancante)" -ForegroundColor Red
}

if (Test-Path "test_exchange_oauth.py") {
    Write-Host "- test_exchange_oauth.py (disponibile)" -ForegroundColor Green
} else {
    Write-Host "- test_exchange_oauth.py (mancante)" -ForegroundColor Red
}

Write-Host "`nProssimi passi:" -ForegroundColor Yellow
Write-Host "1. Leggi EXCHANGE_SETUP_GUIDE.md per setup Azure AD"
Write-Host "2. Configura app in Azure Portal" 
Write-Host "3. Esegui: python test_exchange_oauth.py"
Write-Host "4. Per test reali, modifica credenziali nel file"