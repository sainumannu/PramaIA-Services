"""
Esempi di utilizzo Email Reader Plugin

Mostra come usare il plugin per varie operazioni email.
"""

import json
import asyncio
from pathlib import Path

# Esempi configurazione

def gmail_list_emails_example():
    """Esempio lista email Gmail con filtri."""
    return {
        "operation": "list",
        "provider": "gmail",
        "credentials_path": "/path/to/gmail_credentials.json",
        "max_emails": 50,
        "unread_only": True,
        "include_body": True,
        "include_html": False,
        "date_from": "2025-11-01",
        "sender_filter": "notifications@github.com",
        "subject_filter": "Pull Request"
    }

def imap_list_emails_example():
    """Esempio lista email IMAP generico."""
    return {
        "operation": "list",
        "provider": "imap",
        "credentials_path": "/dummy/path",  # Non usato per IMAP
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "user@gmail.com",
        "password": "app-password-here",
        "folder": "INBOX",
        "max_emails": 25,
        "unread_only": False,
        "subject_filter": "Invoice",
        "date_from": "2025-11-15"
    }

def outlook_list_emails_example():
    """Esempio lista email Outlook/Exchange."""
    return {
        "operation": "list",
        "provider": "outlook",
        "credentials_path": "/path/to/outlook_credentials.json",
        "folder": "INBOX",
        "max_emails": 30,
        "unread_only": True,
        "include_body": True,
        "sender_filter": "boss@company.com",
        "date_from": "2025-11-20"
    }

def get_folders_example():
    """Esempio recupero cartelle."""
    return {
        "operation": "get_folders",
        "provider": "imap",
        "credentials_path": "/dummy/path",
        "imap_server": "imap.office365.com",
        "imap_port": 993,
        "username": "user@company.com",
        "password": "password"
    }

def search_emails_example():
    """Esempio ricerca email (quando implementato)."""
    return {
        "operation": "search",
        "provider": "gmail",
        "credentials_path": "/path/to/gmail_credentials.json",
        "search_query": "has:attachment from:important@company.com",
        "max_emails": 20,
        "include_body": False
    }

def read_specific_email_example():
    """Esempio lettura email specifica (quando implementato)."""
    return {
        "operation": "read",
        "provider": "imap",
        "credentials_path": "/dummy/path",
        "imap_server": "imap.gmail.com",
        "username": "user@gmail.com",
        "password": "app-password",
        "email_id": "12345",
        "include_body": True,
        "include_html": True
    }

def get_attachments_example():
    """Esempio download allegati (quando implementato)."""
    return {
        "operation": "get_attachments",
        "provider": "gmail",
        "credentials_path": "/path/to/gmail_credentials.json",
        "email_id": "email-id-with-attachments",
        "download_path": "/path/to/downloads",
        "attachment_download": True
    }

def demo_configurations():
    """Mostra tutte le configurazioni esempio."""
    examples = {
        "Gmail List": gmail_list_emails_example(),
        "IMAP List": imap_list_emails_example(), 
        "Outlook List": outlook_list_emails_example(),
        "Get Folders": get_folders_example(),
        "Search (Future)": search_emails_example(),
        "Read Email (Future)": read_specific_email_example(),
        "Get Attachments (Future)": get_attachments_example()
    }
    
    print("📧 Email Reader Plugin - Esempi Configurazione")
    print("=" * 60)
    
    for name, config in examples.items():
        print(f"\\n{name}:")
        print(json.dumps(config, indent=2))
        print("-" * 40)

# Provider-specific settings

GMAIL_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]

COMMON_IMAP_SERVERS = {
    "gmail": {
        "server": "imap.gmail.com",
        "port": 993,
        "ssl": True,
        "note": "Richiede App Password"
    },
    "outlook": {
        "server": "outlook.office365.com", 
        "port": 993,
        "ssl": True,
        "note": "Supporta OAuth2 e password"
    },
    "yahoo": {
        "server": "imap.mail.yahoo.com",
        "port": 993, 
        "ssl": True,
        "note": "Richiede App Password"
    },
    "icloud": {
        "server": "imap.mail.me.com",
        "port": 993,
        "ssl": True,
        "note": "Richiede App Password"
    }
}

def show_imap_servers():
    """Mostra server IMAP comuni."""
    print("\\n🔧 Server IMAP Comuni:")
    print("=" * 40)
    
    for provider, settings in COMMON_IMAP_SERVERS.items():
        print(f"\\n{provider.upper()}:")
        print(f"  Server: {settings['server']}")
        print(f"  Porta: {settings['port']}")
        print(f"  SSL: {settings['ssl']}")
        print(f"  Note: {settings['note']}")

def setup_instructions():
    """Istruzioni setup per ogni provider."""
    instructions = {
        "Gmail": [
            "1. Vai su Google Cloud Console",
            "2. Crea progetto o seleziona esistente", 
            "3. Abilita Gmail API",
            "4. Crea credenziali OAuth2 per app desktop",
            "5. Scarica file JSON credenziali",
            "6. Prima esecuzione aprirà browser per autorizzazione"
        ],
        "Outlook/Exchange": [
            "1. Prepara username e password aziendale",
            "2. Per Office 365, considera App Password",
            "3. Crea file JSON con credenziali",
            "4. Test connessione con autodiscovery",
            "5. Se autodiscovery fallisce, specifica server manualmente"
        ],
        "IMAP Generico": [
            "1. Verifica server IMAP del provider",
            "2. Attiva IMAP nelle impostazioni email",
            "3. Per Gmail/Yahoo: crea App Password", 
            "4. Testa connessione con client email",
            "5. Usa parametri IMAP diretti nel request"
        ]
    }
    
    print("\\n📋 Istruzioni Setup Provider:")
    print("=" * 50)
    
    for provider, steps in instructions.items():
        print(f"\\n{provider}:")
        for step in steps:
            print(f"  {step}")

if __name__ == "__main__":
    demo_configurations()
    show_imap_servers()
    setup_instructions()
    
    print("\\n✅ Plugin Email Reader pronto per l'uso!")
    print("📖 Consulta README.md per documentazione completa")