#!/usr/bin/env python3
"""
Test autenticazione Exchange OAuth2 e listing email.
"""
import sys
import os
import asyncio
import logging

# Aggiungi il percorso del modulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from email_processor import EmailProcessor

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_exchange_auth():
    """Test autenticazione Exchange con diversi metodi."""
    
    processor = EmailProcessor()
    
    print("🔐 Test Autenticazione Exchange OAuth2")
    print("=" * 50)
    
    # Configurazioni di test (sostituire con valori reali)
    # NOTA: Per il test completo servono credenziali Azure AD reali
    
    # Test 1: Device Flow (interattivo)
    print("\n1. Test Device Flow (Interactive)")
    print("⚠️  Richiede interazione utente - commentato per ora")
    
    """
    # Per testare device flow, decommenta e inserisci client_id e tenant_id reali
    success = await processor.authenticate_exchange_oauth2(
        client_id="your-client-id",
        tenant_id="your-tenant-id", 
        use_device_flow=True
    )
    
    if success:
        print("✅ Device Flow authentication successful!")
        
        # Test listing email
        result = await processor._list_emails({
            'folder': 'INBOX',
            'max_emails': 5,
            'unread_only': False,
            'include_body': True
        })
        
        print(f"📧 Email result: {result}")
    else:
        print("❌ Device Flow authentication failed")
    """
    
    # Test 2: Username/Password (ROPC - sconsigliato in produzione)
    print("\n2. Test Username/Password Flow")
    print("⚠️  Richiede ROPC abilitato - commentato per sicurezza")
    
    """
    # Per testare ROPC, decommenta e inserisci credenziali reali
    success = await processor.authenticate_exchange_oauth2(
        client_id="your-client-id",
        tenant_id="your-tenant-id",
        username="user@yourdomain.com",
        password="your-password"
    )
    """
    
    # Test 3: IMAP/SMTP Fallback
    print("\n3. Test IMAP/SMTP Fallback (Office 365)")
    print("⚠️  Richiede credenziali Exchange - test simulato")
    
    # Simula test IMAP/SMTP
    print("📋 Configurazioni server predefinite:")
    print(f"  IMAP: outlook.office365.com:993")
    print(f"  SMTP: smtp.office365.com:587")
    
    # Test configurazione senza credenziali reali
    try:
        # Questo fallirà senza credenziali, ma testa la configurazione
        success = await processor.authenticate_exchange_imap_smtp(
            email="test@yourdomain.com",
            password="fake-password"
        )
        print("❌ (Previsto) - Credenziali di test non valide")
    except Exception as e:
        print(f"❌ (Previsto) - Errore autenticazione: {type(e).__name__}")
    
    # Test 4: Verifica disponibilità Microsoft Graph
    print("\n4. Test Disponibilità Dipendenze")
    print("=" * 30)
    
    try:
        import msal
        print("✅ MSAL (Microsoft Authentication Library) disponibile")
        print(f"   Versione: {msal.__version__}")
    except ImportError:
        print("❌ MSAL non disponibile - installare con: pip install msal")
    
    try:
        import requests
        print("✅ Requests disponibile")
        print(f"   Versione: {requests.__version__}")
    except ImportError:
        print("❌ Requests non disponibile - installare con: pip install requests")
    
    # Test 5: Configurazioni Exchange
    print("\n5. Configurazioni Exchange Precaricate")
    print("=" * 40)
    
    from email_processor import EXCHANGE_CONFIGS
    
    for config_name, config in EXCHANGE_CONFIGS.items():
        print(f"\n📋 Configurazione: {config_name}")
        for key, value in config.items():
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 50)
    print("🔍 Guida Setup Exchange:")
    print("1. Registra app in Azure AD")
    print("2. Configura permessi API (Mail.Read, Mail.Send, Mail.ReadWrite)")
    print("3. Crea client secret (per confidential client)")
    print("4. Sostituisci credenziali nel test")
    print("5. Esegui test con credenziali reali")
    print("=" * 50)

async def test_graph_api_simulation():
    """Simula chiamate Graph API per test."""
    
    print("\n🌐 Simulazione Graph API Endpoints")
    print("=" * 40)
    
    # Simula struttura endpoint Graph
    base_url = "https://graph.microsoft.com/v1.0"
    
    endpoints = {
        "Elenco messaggi": f"{base_url}/me/messages",
        "Cartelle mail": f"{base_url}/me/mailFolders", 
        "Messaggio specifico": f"{base_url}/me/messages/{{id}}",
        "Invio email": f"{base_url}/me/sendMail",
        "Allegati": f"{base_url}/me/messages/{{id}}/attachments",
        "Segna come letto": f"{base_url}/me/messages/{{id}} (PATCH)"
    }
    
    for name, url in endpoints.items():
        print(f"📡 {name}: {url}")
    
    # Simula parametri query comuni
    print(f"\n📋 Parametri Query Comuni:")
    print(f"   $filter: isRead eq false")
    print(f"   $orderby: receivedDateTime desc") 
    print(f"   $top: 50")
    print(f"   $select: id,subject,from,receivedDateTime")
    print(f"   $expand: attachments")

if __name__ == "__main__":
    asyncio.run(test_exchange_auth())
    asyncio.run(test_graph_api_simulation())