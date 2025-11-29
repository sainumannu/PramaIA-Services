# 🔧 GUIDA CONFIGURAZIONE PARAMETRI EMAIL PLUGIN

## 📍 Dove Configurare i Parametri

Ci sono **3 modi** per configurare i parametri del plugin:

---

## 🚀 METODO 1: Variabili Ambiente (PIÙ SEMPLICE)

### 1️⃣ Apri PowerShell come Amministratore

### 2️⃣ Configura le variabili per Gmail:
```powershell
# Configura Gmail (metodo App Password - più semplice)
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"

# Verifica configurazione
echo "Username: $env:GMAIL_USERNAME"
echo "Password configurata: $($env:GMAIL_APP_PASSWORD -ne $null)"
```

### 3️⃣ Testa la configurazione:
```powershell
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin"
python real_email_tests.py --gmail-test
```

---

## 🔐 METODO 2: File Credenziali

### 1️⃣ Copia e rinomina i template:
```powershell
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin\credentials"

# Crea file reali dai template
copy gmail_credentials.json.template gmail_credentials.json
copy outlook_credentials.json.template outlook_credentials.json
```

### 2️⃣ Modifica gmail_credentials.json:
```json
{
  "username": "tuaemail@gmail.com",
  "app_password": "abcd efgh ijkl mnop",
  "imap_server": "imap.gmail.com",
  "imap_port": 993
}
```

### 3️⃣ Modifica outlook_credentials.json:
```json
{
  "username": "tuaemail@outlook.com",
  "password": "tua-password",
  "server": "outlook.office365.com"
}
```

---

## ⚙️ METODO 3: Parametri Plugin PDK

### File: plugin.json (già configurato)
Il plugin accetta questi parametri quando chiamato dal PDK:

```json
{
  "provider": "gmail|outlook|imap",
  "gmail_username": "email@gmail.com",
  "gmail_app_password": "password",
  "outlook_username": "email@outlook.com", 
  "outlook_password": "password",
  "imap_server": "imap.server.com",
  "imap_port": 993,
  "imap_username": "username",
  "imap_password": "password",
  "folder": "INBOX",
  "limit": 10,
  "search_query": "from:sender@example.com"
}
```

---

## 📧 COME OTTENERE APP PASSWORD GMAIL

### 1️⃣ Vai su Gmail Settings:
1. Apri Gmail
2. Clicca sull'icona ingranaggio → "Vedi tutte le impostazioni"
3. Vai su "Inoltro e POP/IMAP" 
4. Abilita "Accesso IMAP"

### 2️⃣ Abilita 2FA:
1. Vai su [myaccount.google.com](https://myaccount.google.com)
2. "Sicurezza" → "Verifica in due passaggi"
3. Attiva la verifica

### 3️⃣ Genera App Password:
1. Sempre in "Sicurezza"
2. "Password per le app"
3. Seleziona "Posta" e "Computer Windows"
4. Copia la password generata (16 caratteri)

---

## 🧪 TEST RAPIDO

### Testa la configurazione:
```powershell
# Vai nella cartella del plugin
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin"

# Test veloce Gmail
python debug_email.py --gmail-test

# Test completo
python real_email_tests.py

# Benchmark performance
python benchmark_email.py --quick-test
```

---

## 🔍 VERIFICA CONFIGURAZIONE

### Script di verifica automatica:
```powershell
# Controlla variabili ambiente
echo "=== VERIFICA VARIABILI AMBIENTE ==="
echo "GMAIL_USERNAME: $env:GMAIL_USERNAME"
echo "GMAIL_APP_PASSWORD: $($env:GMAIL_APP_PASSWORD -ne $null)"
echo ""

# Controlla file credenziali
echo "=== VERIFICA FILE CREDENZIALI ==="
if (Test-Path "credentials\gmail_credentials.json") {
    echo "✅ gmail_credentials.json trovato"
} else {
    echo "❌ gmail_credentials.json mancante"
}

if (Test-Path "credentials\outlook_credentials.json") {
    echo "✅ outlook_credentials.json trovato"  
} else {
    echo "❌ outlook_credentials.json mancante"
}
```

---

## 🎯 CONFIGURAZIONE CONSIGLIATA

**Per iniziare velocemente, usa METODO 1** (variabili ambiente):

```powershell
# 1. Configura Gmail con App Password
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "la-tua-app-password"

# 2. Test immediato
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin"
python real_email_tests.py --gmail-test
```

---

## ❌ RISOLUZIONE PROBLEMI

### Errore "Credenziali non configurate":
```powershell
# Verifica variabili
echo $env:GMAIL_USERNAME
echo $env:GMAIL_APP_PASSWORD

# Se vuote, riconfigura
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "tua-app-password"
```

### Errore "Autenticazione fallita":
1. Verifica App Password corretta
2. Controlla IMAP abilitato su Gmail
3. Verifica 2FA attiva

### Errore "Connessione rifiutata":
1. Controlla connessione internet
2. Verifica firewall/antivirus
3. Testa con debug: `python debug_email.py --imap-test`

---

**🎉 Ora sai esattamente dove e come configurare tutto!**