# Cartella Credenziali Email Plugin

Questa cartella contiene le credenziali **REALI** per i test con provider email.

⚠️ **ATTENZIONE**: Mai committare credenziali reali nel repository!

## File Supportati

- `gmail_credentials.json` - OAuth2 Gmail da Google Cloud Console
- `outlook_credentials.json` - Username/password Outlook/Exchange  
- `*.json.backup` - Backup credenziali (opzionale)

## Generazione Automatica

```bash
# Crea template vuoti
python real_email_tests.py --create-templates

# Rinomina e compila con credenziali reali
mv gmail_credentials.json.template gmail_credentials.json
mv outlook_credentials.json.template outlook_credentials.json
```

## Sicurezza

- Cartella inclusa in `.gitignore`
- Permessi di lettura limitati
- Non condividere mai via email/chat
- Usa App Password invece di password principali

## Test Disponibili

```bash
# Test completi con credenziali reali
python real_email_tests.py

# Performance con provider veri
python benchmark_email.py

# Debug problemi di connessione
python debug_email.py --interactive
```