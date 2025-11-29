#!/usr/bin/env python3
"""
🔧 SIMPLE EMAIL TESTER - Test rapido credenziali Gmail
"""

import os
import sys
import imaplib
import ssl
import json
from typing import Dict, Any

def test_gmail_app_password():
    """Test Gmail con App Password (metodo semplice)"""
    
    print("📧 TEST GMAIL APP PASSWORD")
    print("==========================")
    
    # Ottieni credenziali da variabili ambiente
    username = os.getenv('GMAIL_USERNAME')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not username:
        print("❌ GMAIL_USERNAME non configurata!")
        print("   Configura con: $env:GMAIL_USERNAME = 'tuaemail@gmail.com'")
        return False
        
    if not app_password:
        print("❌ GMAIL_APP_PASSWORD non configurata!")
        print("   Configura con: $env:GMAIL_APP_PASSWORD = 'abcd efgh ijkl mnop'")
        return False
    
    print(f"👤 Username: {username}")
    print(f"🔑 App Password: {'*' * len(app_password)}")
    print()
    
    try:
        print("🔌 Connessione a imap.gmail.com:993...")
        
        # Connessione IMAP SSL a Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        
        print("✅ Connessione SSL stabilita")
        print("🔐 Tentativo login...")
        
        # Login con App Password
        mail.login(username, app_password)
        
        print("✅ LOGIN RIUSCITO!")
        print()
        
        # Test operazioni base
        print("📁 Lista cartelle disponibili:")
        status, folders = mail.list()
        if status == 'OK':
            for folder in folders[:5]:  # Prime 5 cartelle
                folder_name = folder.decode().split('"')[3] if '"' in folder.decode() else folder.decode()
                print(f"   📂 {folder_name}")
        
        # Seleziona INBOX
        print("\n📥 Selezione INBOX...")
        mail.select('INBOX')
        
        # Conta messaggi
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            msg_count = len(messages[0].split())
            print(f"✅ Trovati {msg_count} messaggi in INBOX")
        
        # Test email recenti (ultime 3)
        print("\n📧 Test lettura email recenti:")
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            msg_list = messages[0].split()
            recent_msgs = msg_list[-3:] if len(msg_list) >= 3 else msg_list
            
            for i, msg_num in enumerate(recent_msgs):
                status, msg_data = mail.fetch(msg_num, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                if status == 'OK':
                    headers = msg_data[0][1].decode()
                    print(f"   📩 Email #{i+1}: {headers.replace('\\n', ' ').replace('\\r', '').strip()[:100]}...")
        
        # Chiudi connessione
        mail.close()
        mail.logout()
        
        print("\n🎉 TEST COMPLETATO CON SUCCESSO!")
        print("✅ Gmail App Password funziona correttamente")
        print("✅ IMAP abilitato e funzionante")
        print("✅ Plugin email pronto per l'uso!")
        
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Errore IMAP: {e}")
        print("\n🔧 POSSIBILI SOLUZIONI:")
        print("   1. Verifica App Password corretta (16 caratteri)")
        print("   2. Controlla 2FA abilitata su Gmail")
        print("   3. Verifica IMAP abilitato: Gmail Settings → Forwarding/IMAP")
        return False
        
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        print("\n🔧 POSSIBILI SOLUZIONI:")
        print("   1. Controlla connessione internet")
        print("   2. Verifica firewall/antivirus")
        print("   3. Riprova tra qualche minuto")
        return False

def setup_gmail_credentials():
    """Guida setup credenziali Gmail"""
    
    print("⚙️ SETUP CREDENZIALI GMAIL")
    print("===========================")
    print()
    
    print("📋 PASSI DA SEGUIRE:")
    print("1. Vai su: https://myaccount.google.com")
    print("2. Clicca 'Sicurezza' nel menu laterale")
    print("3. Sotto 'Accesso a Google', abilita 'Verifica in due passaggi'")
    print("4. Sempre in 'Sicurezza', clicca 'Password per le app'")
    print("5. Seleziona 'Posta' come app e 'Computer Windows' come dispositivo")
    print("6. Copia la password di 16 caratteri generata")
    print()
    
    email = input("📧 Inserisci il tuo email Gmail: ")
    app_password = input("🔑 Inserisci l'App Password (16 caratteri): ")
    
    print()
    print("💾 Configurazione variabili ambiente...")
    
    # Mostra comandi PowerShell
    print("📋 ESEGUI QUESTI COMANDI IN POWERSHELL:")
    print(f'$env:GMAIL_USERNAME = "{email}"')
    print(f'$env:GMAIL_APP_PASSWORD = "{app_password}"')
    print()
    print("Poi riavvia questo script per testare!")

def show_status():
    """Mostra status configurazione"""
    
    print("📊 STATUS CONFIGURAZIONE")
    print("========================")
    
    username = os.getenv('GMAIL_USERNAME')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    
    print(f"👤 GMAIL_USERNAME: {'✅ ' + username if username else '❌ NON CONFIGURATA'}")
    print(f"🔑 GMAIL_APP_PASSWORD: {'✅ CONFIGURATA' if app_password else '❌ NON CONFIGURATA'}")
    print()
    
    if username and app_password:
        print("✅ Configurazione completa! Puoi eseguire il test.")
        return True
    else:
        print("❌ Configurazione incompleta. Usa setup per configurare.")
        return False

def main():
    """Menu principale"""
    
    print("🚀 GMAIL EMAIL PLUGIN TESTER")
    print("=============================")
    print()
    print("1. 📊 Mostra status configurazione")
    print("2. ⚙️ Setup credenziali Gmail")  
    print("3. 🧪 Test connessione Gmail")
    print("4. 🔄 Test completo (status + test)")
    print("5. ❌ Esci")
    print()
    
    try:
        choice = input("Scelta (1-5): ").strip()
        print()
        
        if choice == "1":
            show_status()
            
        elif choice == "2":
            setup_gmail_credentials()
            
        elif choice == "3":
            if show_status():
                print()
                test_gmail_app_password()
            
        elif choice == "4":
            if show_status():
                print()
                test_gmail_app_password()
                
        elif choice == "5":
            print("👋 Arrivederci!")
            
        else:
            print("❌ Scelta non valida!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore: {e}")

if __name__ == "__main__":
    main()