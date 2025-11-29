# 📧 Gmail Plugin - Sistema Email Completo

**Plugin enterprise-grade per gestione email completa con 9 operazioni avanzate, supporto multi-provider e architettura production-ready.**

## 🏆 **CARATTERISTICHE PRINCIPALI**

✅ **9 Operazioni Email Complete** - Read, Search, Send, Labels, Stats, Attachments  
✅ **Multi-Provider Support** - Gmail API + IMAP + SMTP universale  
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

✅ **Multi-Provider**: Gmail, IMAP, SMTP, Outlook  
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

## 🔗 **PLUGIN CORRELATI**

- **outlook-plugin** (futuro) - Microsoft 365/Exchange
- **imap-plugin** (futuro) - Server IMAP generici
- **email-automation-plugin** (futuro) - Automazioni email avanzate

## 🏆 **STATO IMPLEMENTAZIONE**

**🟢 COMPLETO** - Plugin production-ready per:
- ✅ Gestione email professionale aziendale
- ✅ Automazioni email avanzate e workflow  
- ✅ Analisi e reportistica email dettagliata
- ✅ Download e backup automatico allegati
- ✅ Integrazione con sistemi di ticketing/CRM

---

*Parte dell'ecosistema PramaIA - Advanced Email Management*