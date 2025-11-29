#!/usr/bin/env pwsh
# 🔧 SCRIPT CONFIGURAZIONE AUTOMATICA EMAIL PLUGIN

Write-Host "📧 CONFIGURAZIONE EMAIL PLUGIN" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow
Write-Host ""

# Funzione per richiedere input sicuro
function Read-SecureInput {
    param(
        [string]$Prompt,
        [switch]$IsPassword
    )
    
    Write-Host $Prompt -ForegroundColor Cyan -NoNewline
    if ($IsPassword) {
        $secureString = Read-Host -AsSecureString
        $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($secureString)
        $password = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($ptr)
        return $password
    } else {
        return Read-Host
    }
}

# Controllo directory corrente
$currentDir = Get-Location
if (-not $currentDir.Path.EndsWith("email-reader-plugin")) {
    Write-Host "⚠️  Cambio directory..." -ForegroundColor Yellow
    Set-Location "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin"
    Write-Host "✅ Directory: $(Get-Location)" -ForegroundColor Green
}

Write-Host "🔐 CONFIGURAZIONE CREDENZIALI" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Menu scelta provider
Write-Host "Quale provider vuoi configurare?" -ForegroundColor Cyan
Write-Host "1. Gmail (consigliato per iniziare)" -ForegroundColor White
Write-Host "2. Outlook/Exchange" -ForegroundColor White
Write-Host "3. IMAP Generico" -ForegroundColor White
Write-Host "4. Tutti" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Scelta (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "📧 CONFIGURAZIONE GMAIL" -ForegroundColor Blue
        Write-Host "=======================" -ForegroundColor Blue
        
        Write-Host ""
        Write-Host "📋 ISTRUZIONI:" -ForegroundColor Yellow
        Write-Host "1. Vai su myaccount.google.com" -ForegroundColor White
        Write-Host "2. Sicurezza → Verifica in due passaggi (abilita)" -ForegroundColor White
        Write-Host "3. Sicurezza → Password per le app" -ForegroundColor White
        Write-Host "4. Seleziona 'Posta' e 'Computer Windows'" -ForegroundColor White
        Write-Host "5. Copia la password generata (16 caratteri)" -ForegroundColor White
        Write-Host ""
        
        $gmailUser = Read-SecureInput "📧 Email Gmail: "
        $gmailPass = Read-SecureInput "🔑 App Password (16 caratteri): " -IsPassword
        
        # Configura variabili ambiente
        $env:GMAIL_USERNAME = $gmailUser
        $env:GMAIL_APP_PASSWORD = $gmailPass
        
        Write-Host ""
        Write-Host "✅ Variabili ambiente configurate!" -ForegroundColor Green
        Write-Host "   GMAIL_USERNAME: $env:GMAIL_USERNAME" -ForegroundColor Gray
        Write-Host "   GMAIL_APP_PASSWORD: [CONFIGURATA]" -ForegroundColor Gray
    }
    
    "2" {
        Write-Host ""
        Write-Host "📧 CONFIGURAZIONE OUTLOOK" -ForegroundColor Blue
        Write-Host "=========================" -ForegroundColor Blue
        
        $outlookUser = Read-SecureInput "📧 Email Outlook: "
        $outlookPass = Read-SecureInput "🔑 Password: " -IsPassword
        
        # Crea file credenziali Outlook
        $outlookCreds = @{
            username = $outlookUser
            password = $outlookPass
            server = "outlook.office365.com"
        } | ConvertTo-Json -Depth 2
        
        if (-not (Test-Path "credentials")) {
            New-Item -ItemType Directory -Name "credentials" -Force | Out-Null
        }
        
        $outlookCreds | Out-File "credentials\outlook_credentials.json" -Encoding UTF8
        Write-Host "✅ File outlook_credentials.json creato!" -ForegroundColor Green
    }
    
    "3" {
        Write-Host ""
        Write-Host "📧 CONFIGURAZIONE IMAP GENERICO" -ForegroundColor Blue
        Write-Host "===============================" -ForegroundColor Blue
        
        $imapServer = Read-SecureInput "🌐 Server IMAP: "
        $imapPort = Read-SecureInput "🔌 Porta (di solito 993): "
        $imapUser = Read-SecureInput "👤 Username: "
        $imapPass = Read-SecureInput "🔑 Password: " -IsPassword
        
        # Configura variabili ambiente IMAP
        $env:IMAP_SERVER = $imapServer
        $env:IMAP_PORT = $imapPort
        $env:IMAP_USERNAME = $imapUser
        $env:IMAP_PASSWORD = $imapPass
        
        Write-Host "✅ Configurazione IMAP completata!" -ForegroundColor Green
    }
    
    "4" {
        Write-Host "🔄 Configurazione completa..." -ForegroundColor Yellow
        # Implementa configurazione completa
    }
    
    default {
        Write-Host "❌ Scelta non valida!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🧪 TEST CONFIGURAZIONE" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""

$testChoice = Read-Host "Vuoi testare la configurazione ora? (s/n)"

if ($testChoice -eq "s" -or $testChoice -eq "S") {
    Write-Host ""
    Write-Host "🚀 Avvio test..." -ForegroundColor Yellow
    
    switch ($choice) {
        "1" {
            Write-Host "Testing Gmail..." -ForegroundColor Cyan
            python debug_email.py --gmail-test
        }
        "2" {
            Write-Host "Testing Outlook..." -ForegroundColor Cyan
            python debug_email.py --outlook-test
        }
        "3" {
            Write-Host "Testing IMAP..." -ForegroundColor Cyan
            python debug_email.py --imap-test
        }
    }
}

Write-Host ""
Write-Host "✅ CONFIGURAZIONE COMPLETATA!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 COMANDI UTILI:" -ForegroundColor Yellow
Write-Host "  Test completo:     python real_email_tests.py" -ForegroundColor White
Write-Host "  Benchmark:         python benchmark_email.py" -ForegroundColor White
Write-Host "  Debug interattivo: python debug_email.py --interactive" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentazione:   GUIDA_CONFIGURAZIONE.md" -ForegroundColor Gray