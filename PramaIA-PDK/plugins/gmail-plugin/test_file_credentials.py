#!/usr/bin/env python3
"""
🔧 TEST GMAIL CON FILE CREDENZIALI
"""

import json
import imaplib
import os

def test_gmail_from_file():
    """Test Gmail usando credenziali da file"""
    
    print("📧 TEST GMAIL DA FILE CREDENZIALI")
    print("=================================")
    print()
    
    # Percorso file credenziali
    creds_file = "credentials/gmail_credentials.json"
    
    if not os.path.exists(creds_file):
        print(f"❌ File {creds_file} non trovato!")
        print("   Assicurati di aver creato il file dalle credenziali reali")
        return False
    
    try:
        # Carica credenziali da file
        print("📂 Caricamento credenziali da file...")
        with open(creds_file, 'r', encoding='utf-8') as f:
            creds = json.load(f)
        
        username = creds.get('username')
        app_password = creds.get('app_password')
        imap_server = creds.get('imap_server', 'imap.gmail.com')
        imap_port = creds.get('imap_port', 993)
        
        print(f"👤 Username: {username}")
        print(f"🔑 App Password: {'*' * len(app_password)}")
        print(f"🌐 Server: {imap_server}:{imap_port}")
        print()
        
        if not username or not app_password:
            print("❌ Username o password mancanti nel file!")
            return False
        
        # Test connessione IMAP
        print("🔌 Connessione IMAP...")
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        
        print("✅ Connessione SSL stabilita")
        print("🔐 Tentativo login...")
        
        # Login
        mail.login(username, app_password)
        print("✅ LOGIN RIUSCITO!")
        print()
        
        # Test operazioni
        print("📁 Lista cartelle...")
        status, folders = mail.list()
        if status == 'OK':
            for folder in folders[:3]:
                folder_name = folder.decode().split('"')[3] if '"' in folder.decode() else folder.decode()
                print(f"   📂 {folder_name}")
        
        # Conta messaggi INBOX
        mail.select('INBOX')
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            msg_count = len(messages[0].split())
            print(f"\n✅ INBOX: {msg_count} messaggi trovati")
        
        # Test email più recente
        if msg_count > 0:
            print("\n📧 Test lettura email più recente...")
            msg_list = messages[0].split()
            latest_msg = msg_list[-1]
            
            status, msg_data = mail.fetch(latest_msg, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
            if status == 'OK':
                headers = msg_data[0][1].decode()
                print(f"   📩 {headers.replace(chr(10), ' ').replace(chr(13), '').strip()[:150]}...")
        
        # Cleanup
        mail.close()
        mail.logout()
        
        print("\n🎉 TEST COMPLETATO CON SUCCESSO!")
        print("✅ File credenziali funziona correttamente")
        print("✅ Plugin email pronto per l'uso!")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Errore IMAP: {e}")
        print("\n🔧 POSSIBILI CAUSE:")
        print("   1. App Password non corretta")
        print("   2. IMAP non abilitato su Gmail")
        print("   3. 2FA non abilitata")
        return False
        
    except json.JSONDecodeError as e:
        print(f"❌ Errore JSON nel file credenziali: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

if __name__ == "__main__":
    test_gmail_from_file()