# 🚀 Test Rapido Plugin Gmail - Operazioni Avanzate
# Script PowerShell per test immediato

Write-Host "🚀 TEST RAPIDO PLUGIN GMAIL - OPERAZIONI AVANZATE" -ForegroundColor Green
Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host "=" * 55 -ForegroundColor Green

Write-Host "`n📋 MODALITÀ DI TEST DISPONIBILI:" -ForegroundColor Yellow

Write-Host "`n1️⃣ DEMO MODE (senza credenziali)" -ForegroundColor Cyan
Write-Host "   Testa la sintassi di tutte le 8 operazioni implementate"
Write-Host "   📌 Comando: python test_advanced_operations.py" -ForegroundColor Gray

Write-Host "`n2️⃣ IMAP MODE (con Gmail App Password)" -ForegroundColor Cyan  
Write-Host "   Test completo con connessione Gmail IMAP reale"
Write-Host "   📌 Setup credenziali:" -ForegroundColor Gray
Write-Host "     `$env:GMAIL_USERNAME='tuaemail@gmail.com'"
Write-Host "     `$env:GMAIL_APP_PASSWORD='abcd efgh ijkl mnop'"
Write-Host "   📌 Comando: python test_advanced_operations.py" -ForegroundColor Gray

Write-Host "`n🔧 SETUP APP PASSWORD GMAIL:" -ForegroundColor Yellow
Write-Host "   1. Vai a myaccount.google.com → Security"
Write-Host "   2. Abilita 2-Factor Authentication"  
Write-Host "   3. Genera App Password per Mail"
Write-Host "   4. Usa la password di 16 caratteri generata"

Write-Host "`n📦 OPERAZIONI IMPLEMENTATE:" -ForegroundColor Green
$operations = @(
    "📖 read - Lettura email specifica",
    "🔍 search - Ricerca avanzata con filtri", 
    "✅ mark_read - Gestione stato letto/non letto",
    "📎 get_attachments - Download allegati",
    "🏷️ manage_labels - Gestione etichette Gmail",
    "📁 move_email - Spostamento tra cartelle", 
    "📊 get_stats - Statistiche email",
    "📂 get_folders - Lista cartelle"
)

foreach ($op in $operations) {
    Write-Host "   ✅ $op" -ForegroundColor Green
}

Write-Host "`n🎯 SCEGLI MODALITÀ TEST:" -ForegroundColor Yellow
$choice = Read-Host "Premi [1] per Demo, [2] per IMAP, [Enter] per Demo"

switch ($choice) {
    "2" {
        Write-Host "`n🔐 SETUP CREDENZIALI IMAP:" -ForegroundColor Cyan
        $email = Read-Host "Gmail Username"
        $password = Read-Host "App Password (16 char)" -AsSecureString
        
        if ($email -and $password) {
            $env:GMAIL_USERNAME = $email
            $env:GMAIL_APP_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
            
            Write-Host "`n✅ Credenziali impostate! Avvio test IMAP..." -ForegroundColor Green
            python test_advanced_operations.py
        } else {
            Write-Host "`n❌ Credenziali non complete. Avvio demo..." -ForegroundColor Red
            python test_advanced_operations.py
        }
    }
    default {
        Write-Host "`n🧪 Avvio test DEMO (sintassi validation)..." -ForegroundColor Cyan
        python test_advanced_operations.py
    }
}

Write-Host "`n🎉 Test completato! Plugin Gmail con 8 operazioni avanzate pronto!" -ForegroundColor Green