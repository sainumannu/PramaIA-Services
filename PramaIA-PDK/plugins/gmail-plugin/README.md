# Gmail Plugin

Plugin dedicato per operazioni Gmail via IMAP con App Password.

## 🚀 SETUP VELOCE

```powershell
# 1. Installa
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\gmail-plugin"

# 2. Configura (App Password da myaccount.google.com)
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"

# 3. Test
python test_file_credentials.py
```

## ⚡ Operazioni Supportate

- 📋 **list**: Lista email con filtri avanzati
- 📖 **read**: Lettura email completa con allegati
- 🔍 **search**: Ricerca per mittente, oggetto, data
- 📎 **download_attachments**: Salva allegati
- ✅ **mark_read/unread**: Gestione stato email
- 📁 **get_folders**: Lista cartelle Gmail

## 🎯 Vantaggi Plugin Separato

- ✅ Focus esclusivo Gmail
- ✅ Dipendenze minime (solo imaplib)
- ✅ Codice pulito e manutenibile
- ✅ Facile estensione features Gmail-specific

## 📚 Documentazione

- `GMAIL_ACCESS_GUIDE.md` - Setup App Password
- `GMAIL_OPERATIONS_ROADMAP.md` - Operazioni disponibili
- `GUIDA_CONFIGURAZIONE.md` - Configurazione completa

## 🔗 Plugin Correlati

- **outlook-plugin** (futuro) - Microsoft 365/Exchange
- **imap-plugin** (futuro) - Server IMAP generici

---

*Parte dell'ecosistema PramaIA*