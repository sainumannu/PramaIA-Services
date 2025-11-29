#!/usr/bin/env python3
"""
Test DIRETTO invio email - Plugin Gmail
Test semplificato che bypassa l'autenticazione complessa
"""

import asyncio
import logging
import sys
import os

# Aggiungi il percorso src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from email_processor import EmailProcessor

async def test_direct_send():
    """Test invio email diretto."""
    
    print("📧 TEST DIRETTO INVIO EMAIL")
    print("=" * 40)
    
    processor = EmailProcessor()
    
    # Configurazione diretta senza autenticazione complessa
    inputs = {
        'operation': 'send_email',
        'to': 'fab.milia@gmail.com',
        'subject': '🚀 Test Diretto Plugin Gmail',
        'body': '''Ciao Fab!

Questo è un test DIRETTO dell'operazione send_email del Plugin Gmail.

✅ Invio email SMTP implementato
✅ Test bypassa autenticazione complessa  
✅ Usa credenziali dirette

Se ricevi questa email, l'implementazione funziona perfettamente! 🎯

Timestamp: ''' + str(asyncio.get_event_loop().time()) + '''

Saluti,
Plugin Gmail PramaIA-PDK''',
        'smtp_username': 'fab.milia@gmail.com',
        'smtp_password': 'twkjfxdydieybggx',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587
    }
    
    print("🚀 Invio in corso...")
    
    # Test chiamata diretta al metodo
    try:
        result = await processor._send_email(inputs)
        
        if result['success']:
            print("✅ EMAIL INVIATA CON SUCCESSO!")
            print(f"   📧 Destinatario: {result.get('sent_to')}")
            print(f"   📝 Oggetto: {result.get('subject')}")
            print(f"   🕒 Orario: {result.get('sent_at')}")
            print(f"   📍 Server: {result.get('smtp_server')}")
            print(f"   🆔 Message ID: {result.get('message_id', 'N/A')}")
            
            print(f"\n🎯 Controlla la casella email: fab.milia@gmail.com")
            print("📧 Dovresti ricevere l'email di test!")
            
        else:
            print("❌ ERRORE INVIO:")
            print(f"   {result.get('error', 'Errore sconosciuto')}")
            
    except Exception as e:
        print(f"❌ ERRORE ECCEZIONE: {str(e)}")
        
    print(f"\n{'=' * 40}")
    print("🚀 Test diretto completato!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_direct_send())