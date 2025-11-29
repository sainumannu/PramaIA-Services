# 📧 Gmail Plugin - Sistema Email Completo Multi-Provider

**Plugin enterprise-grade per gestione email completa con 9 operazioni avanzate, supporto multi-provider (Gmail + Exchange/Office 365) e architettura production-ready.**

## 🏆 **CARATTERISTICHE PRINCIPALI**

✅ **9 Operazioni Email Complete** - Read, Search, Send, Labels, Stats, Attachments  
✅ **Multi-Provider Support** - Gmail API + Exchange/Office 365 + IMAP + SMTP  
✅ **Exchange/Office 365** - OAuth2 con Microsoft Graph API + Shared Mailbox  
✅ **Error Handling Robusto** - Fallback automatico e recovery  
✅ **Test Suite Completa** - Validazione automatica funzionamenti  
✅ **Async Performance** - Operazioni non-blocking ottimizzate  

## 🚀 **SETUP IMMEDIATO**

```powershell
# 1. Naviga nella directory
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\gmail-plugin"

# 2. Test demo (senza credenziali) 
python test_advanced_operations.py

# 3. Test completo con Gmail App Password + invio email
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"
python test_advanced_operations.py

# 4. Test solo invio email
python test_send_email.py

# 5. Script assistito
.\test_gmail_quick.ps1
```

## ✨ **OPERAZIONI SUPPORTATE**

### 📋 **LIST** - Lista Email con Filtri
### 📖 **READ** - Leggi Email Specifica  
### 🔍 **SEARCH** - Ricerca Avanzata
### ✅ **MARK_READ** - Gestione Stato Letto
### 📎 **GET_ATTACHMENTS** - Download Allegati
### 🏷️ **MANAGE_LABELS** - Gestione Etichette Gmail
### 📁 **MOVE_EMAIL** - Sposta Email
### 📊 **GET_STATS** - Statistiche Email
### 📂 **GET_FOLDERS** - Lista Cartelle
### 📧 **SEND_EMAIL** - Invio Email SMTP

```python
# Invio email semplice
result = await processor.process({
    'operation': 'send_email',
    'to': 'destinatario@example.com',
    'subject': 'Test Email',
    'body': 'Corpo email in testo',
    'smtp_username': 'mittente@gmail.com',
    'smtp_password': 'app-password'
})

# Invio email con allegati e HTML
result = await processor.process({
    'operation': 'send_email',
    'to': ['dest1@test.com', 'dest2@test.com'],
    'cc': 'copia@test.com',
    'bcc': 'nascosta@test.com',
    'subject': 'Email Avanzata',
    'body': 'Versione testo',
    'body_html': '<h1>Versione HTML</h1><p>Corpo HTML</p>',
    'attachments': ['documento.pdf', 'immagine.jpg'],
    'smtp_username': 'mittente@gmail.com',
    'smtp_password': 'app-password'
})
```

## 🎯 **FEATURES PRINCIPALI**

✅ **Multi-Provider**: Gmail API, Exchange/Office 365, IMAP, SMTP  
✅ **Exchange/Office 365**: OAuth2 con Microsoft Graph API  
✅ **Shared Mailbox**: Supporto completo per mailbox condivise  
✅ **Invio Email**: SMTP con supporto HTML, allegati, destinatari multipli  
✅ **Ricerca Avanzata**: Filtri complessi per mittente, oggetto, data, allegati  
✅ **Download Allegati**: Con filtri dimensione e tipo file  
✅ **Gestione Stati**: Letto/Non letto con operazioni bulk  
✅ **Etichette Gmail**: Gestione completa etichette Google  
✅ **Statistiche**: Analisi approfondite email e usage  
✅ **Operazioni Bulk**: Gestione multipla email contemporanea  
✅ **Error Handling**: Gestione errori robusta e logging  
✅ **Async Support**: Performance ottimali con operazioni asincrone  

## 🧪 **TEST E ESEMPI**

### Test Completo
```bash
python test_advanced_operations.py  # Test tutte le operazioni + invio
python test_send_email.py          # Test specifico invio email
```

## 📚 **DOCUMENTAZIONE COMPLETA**

- `GMAIL_ACCESS_GUIDE.md` - Setup App Password e OAuth2
- `GMAIL_OPERATIONS_ROADMAP.md` - Roadmap operazioni e complessità
- `GUIDA_CONFIGURAZIONE.md` - Configurazione completa e troubleshooting
- `FINAL_PLUGIN_SUMMARY.md` - Riassunto implementazione completa
- `EXCHANGE_SETUP_GUIDE.md` - **NUOVO** Setup completo Exchange/Office 365

## 💼 **EXCHANGE/OFFICE 365 SETUP**

**🆕 SUPPORTO COMPLETO per Exchange/Office 365!**

```powershell
# Test configurazioni Exchange
python test_exchange_oauth.py

# Guida completa setup Azure AD + OAuth2
Get-Content EXCHANGE_SETUP_GUIDE.md
```

### Quick Start Exchange OAuth2:
```python
from email_processor import EmailProcessor
import asyncio

async def test_exchange():
    processor = EmailProcessor()
    
    # Device Flow (raccomandato per test)
    success = await processor.authenticate_exchange_oauth2(
        client_id="your-azure-app-client-id",
        tenant_id="your-azure-tenant-id",
        use_device_flow=True
    )
    
    if success:
        # Lista email da Exchange/Office 365
        result = await processor._list_emails({
            'folder': 'INBOX',
            'max_emails': 10,
            'unread_only': True
        })
        print(f"📧 {result['data']['email_count']} email trovate")
        
        # Invia via Graph API
        send_result = await processor._send_email({
            'to': 'colleague@company.com',
            'subject': 'Test Exchange Plugin',
            'body': 'Inviato via Microsoft Graph API!'
        })
        
asyncio.run(test_exchange())
```

**Caratteristiche Exchange:**
- ✅ **OAuth2 Microsoft Graph API** - Autenticazione sicura enterprise
- ✅ **Shared Mailbox Support** - Accesso mailbox condivise  
- ✅ **Device Flow** - Autenticazione interattiva MFA-ready
- ✅ **Client Credentials** - Automazione server-to-server
- ✅ **IMAP/SMTP Fallback** - Compatibilità legacy

## 🔗 **PLUGIN CORRELATI**

- **exchange-plugin** ✅ **INTEGRATO** - Microsoft 365/Exchange OAuth2
- **imap-plugin** (futuro) - Server IMAP generici
- **email-automation-plugin** (futuro) - Automazioni email avanzate

## 🏆 **STATO IMPLEMENTAZIONE**

**🟢 COMPLETO** - Plugin production-ready per:
- ✅ Gestione email professionale aziendale (Gmail + Exchange)
- ✅ Automazioni email avanzate e workflow multi-provider
- ✅ Analisi e reportistica email dettagliata  
- ✅ Download e backup automatico allegati
- ✅ Integrazione con sistemi di ticketing/CRM
- ✅ **Exchange/Office 365 OAuth2** con Microsoft Graph API

---

*Parte dell'ecosistema PramaIA - Advanced Email Management*