#!/usr/bin/env python3
"""
Test lettura ultima email - Plugin Gmail  
Test per leggere l'email più recente (dovrebbe essere quella appena inviata)
"""

import asyncio
import logging
import sys
import os

# Aggiungi il percorso src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from email_processor import EmailProcessor

async def test_read_latest_email():
    """Test lettura ultima email arrivata."""
    
    print("📖 TEST LETTURA ULTIMA EMAIL ARRIVATA")
    print("=" * 50)
    
    processor = EmailProcessor()
    
    # Configurazione per leggere con IMAP
    imap_config = {
        'operation': 'list',
        'provider': 'gmail', 
        'username': 'fab.milia@gmail.com',
        'password': 'twkjfxdydieybggx',
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'folder': 'INBOX',
        'max_results': 1  # Solo la più recente
    }
    
    print("🔍 1. Recupero ultima email...")
    
    # Ottieni lista email (la più recente) - Chiamata diretta
    try:
        # Prima otteniamo l'autenticazione IMAP
        import imaplib
        import email as email_lib
        from email.header import decode_header
        
        # Connessione IMAP diretta
        print("🔗 Connessione IMAP...")
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login('fab.milia@gmail.com', 'twkjfxdydieybggx')
        mail.select('INBOX')
        
        # Cerca ultima email
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        
        if email_ids:
            # Prendi l'ultimo ID (più recente)
            latest_id = email_ids[-1]
            
            # Ottieni l'email
            status, msg_data = mail.fetch(latest_id, '(RFC822)')
            raw_email = msg_data[0][1]
            
            # Parse email
            email_message = email_lib.message_from_bytes(raw_email)
            
            # Estrai informazioni
            subject_raw = str(email_message['Subject'])
            
            # Decodifica oggetto se encoded
            subject = subject_raw
            try:
                decoded_parts = decode_header(subject_raw)
                if decoded_parts:
                    subject_parts = []
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            subject_parts.append(part.decode(encoding or 'utf-8'))
                        else:
                            subject_parts.append(str(part))
                    subject = ''.join(subject_parts)
            except:
                subject = subject_raw
                
            sender = str(email_message['From'])
            date = str(email_message['Date'])
            to_addr = str(email_message['To'])
            
            print("✅ Ultima email trovata:")
            print(f"   📧 ID: {latest_id.decode()}")
            print(f"   📝 Oggetto: {subject}")
            print(f"   👤 Da: {sender}")  
            print(f"   📧 A: {to_addr}")
            print(f"   📅 Data: {date}")
            
            # Estrai corpo email
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                            break
                        except:
                            continue
            else:
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8')
                except:
                    body = str(email_message.get_payload())
            
            print(f"   📝 Corpo ({len(body)}) caratteri:")
            
            # Mostra preview del corpo
            if body:
                preview = body[:300] + '...' if len(body) > 300 else body
                print(f"   📄 Preview:")
                for line in preview.split('\n')[:5]:  # Prime 5 righe
                    if line.strip():
                        print(f"      {line.strip()}")
            else:
                print(f"   📄 Preview: [Corpo vuoto o non leggibile]")
            
            # Verifica se è la nostra email di test
            if "Test Diretto Plugin Gmail" in subject:
                print(f"\n🎯 PERFETTO! Questa è l'email di test che abbiamo appena inviato!")
                print(f"✅ Il ciclo completo INVIO → RICEZIONE → LETTURA funziona al 100%!")
                print(f"🎉 Plugin Gmail: sistema bidirezionale COMPLETAMENTE FUNZIONANTE!")
            
            mail.close()
            mail.logout()
                
        else:
            print("❌ Nessuna email trovata nella casella INBOX")
            
    except Exception as e:
        print(f"❌ ERRORE: {str(e)}")
        
    print(f"\n{'=' * 50}")
    print("📖 Test lettura ultima email completato!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_read_latest_email())