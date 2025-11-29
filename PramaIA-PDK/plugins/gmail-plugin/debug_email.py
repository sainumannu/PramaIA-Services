"""
Debug Tool Email Reader Plugin - Diagnosi Problemi Reali

Tool per diagnosticare problemi di connessione, autenticazione,
e performance con provider email reali.
"""

import asyncio
import sys
import json
import imaplib
import ssl
import socket
from pathlib import Path

# Setup path
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from email_processor import EmailProcessor

class EmailDebugger:
    """Tool debug per problemi email."""
    
    def __init__(self):
        self.processor = EmailProcessor()
    
    async def diagnose_imap_connection(self, server, port, username, password):
        """Diagnosi dettagliata connessione IMAP."""
        print(f"🔍 DIAGNOSI CONNESSIONE IMAP")
        print(f"Server: {server}:{port}")
        print(f"User: {username}")
        print("-" * 50)
        
        # Test risoluzione DNS
        print("\\n1. 🌐 Test risoluzione DNS...")
        try:
            import socket
            ip = socket.gethostbyname(server)
            print(f"   ✅ DNS OK: {server} → {ip}")
        except Exception as e:
            print(f"   ❌ DNS ERRORE: {e}")
            return False
        
        # Test connessione TCP
        print("\\n2. 🔌 Test connessione TCP...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ TCP OK: Porta {port} aperta")
            else:
                print(f"   ❌ TCP ERRORE: Porta {port} non raggiungibile")
                return False
                
        except Exception as e:
            print(f"   ❌ TCP ECCEZIONE: {e}")
            return False
        
        # Test SSL/TLS
        print("\\n3. 🔐 Test SSL/TLS...")
        try:
            context = ssl.create_default_context()
            with socket.create_connection((server, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=server) as ssock:
                    cert = ssock.getpeercert()
                    print(f"   ✅ SSL OK: {cert.get('subject', 'N/A')}")
        except Exception as e:
            print(f"   ❌ SSL ERRORE: {e}")
            return False
        
        # Test login IMAP
        print("\\n4. 📧 Test login IMAP...")
        try:
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            
            # Test lista cartelle
            folders = mail.list()
            if folders[0] == 'OK':
                folder_count = len(folders[1])
                print(f"   ✅ IMAP LOGIN OK: {folder_count} cartelle trovate")
                
                # Mostra prime cartelle
                print("   📁 Prime cartelle:")
                for folder in folders[1][:5]:
                    folder_name = folder.decode().split('"')[-1]
                    print(f"      • {folder_name}")
                
                # Test selezione INBOX
                status, count = mail.select('INBOX')
                if status == 'OK':
                    message_count = int(count[0])
                    print(f"   📫 INBOX: {message_count} messaggi")
                
            mail.logout()
            return True
            
        except imaplib.IMAP4.error as e:
            print(f"   ❌ IMAP ERRORE: {e}")
            print("   💡 Suggerimenti:")
            print("      • Verifica username/password")
            print("      • Per Gmail usa App Password")
            print("      • Controlla che IMAP sia abilitato")
            return False
        except Exception as e:
            print(f"   ❌ IMAP ECCEZIONE: {e}")
            return False
    
    async def debug_gmail_oauth(self, credentials_path):
        """Debug OAuth2 Gmail."""
        print(f"🔍 DEBUG GMAIL OAUTH2")
        print(f"Credenziali: {credentials_path}")
        print("-" * 50)
        
        # Verifica file credenziali
        print("\\n1. 📄 Verifica file credenziali...")
        creds_file = Path(credentials_path)
        
        if not creds_file.exists():
            print(f"   ❌ File non trovato: {credentials_path}")
            return False
        
        try:
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
            
            # Verifica struttura
            if 'installed' in creds_data:
                installed = creds_data['installed']
                required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
                
                missing_fields = [field for field in required_fields 
                                if field not in installed]
                
                if missing_fields:
                    print(f"   ❌ Campi mancanti: {missing_fields}")
                    return False
                else:
                    print("   ✅ Struttura credenziali OK")
                    print(f"   🆔 Client ID: {installed['client_id'][:20]}...")
            else:
                print("   ❌ Campo 'installed' mancante")
                return False
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON malformato: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Errore lettura: {e}")
            return False
        
        # Test dipendenze Gmail
        print("\\n2. 📦 Verifica dipendenze Gmail...")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            print("   ✅ Tutte le dipendenze Gmail disponibili")
        except ImportError as e:
            print(f"   ❌ Dipendenza mancante: {e}")
            print("   💡 Installa con: pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
        
        # Test token esistente
        print("\\n3. 🎫 Verifica token esistente...")
        token_path = creds_file.parent / 'token.json'
        
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path))
                if creds.valid:
                    print("   ✅ Token valido esistente")
                elif creds.expired and creds.refresh_token:
                    print("   ⚠️  Token scaduto ma refresh disponibile")
                    try:
                        creds.refresh(Request())
                        print("   ✅ Token refreshato con successo")
                    except Exception as e:
                        print(f"   ❌ Errore refresh: {e}")
                        return False
                else:
                    print("   ❌ Token non valido, serve nuova autorizzazione")
            except Exception as e:
                print(f"   ❌ Errore token: {e}")
        else:
            print("   ℹ️  Nessun token esistente, serve autorizzazione")
        
        return True
    
    async def test_email_operation(self, config):
        """Test operazione email specifica con debug dettagliato."""
        print(f"🧪 TEST OPERAZIONE EMAIL")
        print(f"Provider: {config.get('provider', 'N/A')}")
        print(f"Operazione: {config.get('operation', 'N/A')}")
        print("-" * 50)
        
        try:
            print("\\n🔄 Esecuzione operazione...")
            start_time = asyncio.get_event_loop().time()
            
            result = await self.processor.process(config)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            print(f"⏱️  Durata: {duration:.2f} secondi")
            
            if result['success']:
                print("\\n✅ OPERAZIONE RIUSCITA")
                print(f"Messaggio: {result['message']}")
                
                # Dettagli specifici per operazione
                if 'emails' in result:
                    emails = result['emails']
                    print(f"\\n📧 Email recuperate: {len(emails)}")
                    
                    if emails:
                        print("\\n📋 Prime 3 email:")
                        for i, email in enumerate(emails[:3], 1):
                            print(f"  {i}. {email.get('subject', 'No subject')[:60]}...")
                            print(f"     Da: {email.get('sender', 'Unknown')}")
                            print(f"     Data: {email.get('date', 'Unknown')}")
                            
                            # Mostra dimensioni corpo se presente
                            body = email.get('body_text', '')
                            if body:
                                print(f"     Corpo: {len(body)} caratteri")
                
                if 'folders' in result:
                    folders = result['folders']
                    print(f"\\n📁 Cartelle trovate: {len(folders)}")
                    for folder in folders[:10]:
                        name = folder.get('name', 'Unknown')
                        count = folder.get('message_count', '?')
                        print(f"  📁 {name} ({count} messaggi)")
                
                # Info provider
                provider_info = result.get('provider_info', {})
                if provider_info:
                    print(f"\\n🔌 Info provider:")
                    print(f"  Provider: {provider_info.get('provider', 'N/A')}")
                    print(f"  Autenticato: {provider_info.get('authenticated', False)}")
                    print(f"  Email utente: {provider_info.get('user_email', 'N/A')}")
                
                return True
                
            else:
                print("\\n❌ OPERAZIONE FALLITA")
                print(f"Errore: {result.get('error', 'Unknown error')}")
                print(f"Messaggio: {result.get('message', 'No message')}")
                
                # Suggerimenti debug
                error = result.get('error', '').lower()
                print("\\n💡 Suggerimenti debug:")
                
                if 'authentication' in error or 'login' in error:
                    print("  • Verifica username/password")
                    print("  • Per Gmail usa App Password")
                    print("  • Controlla abilitazione IMAP")
                elif 'connection' in error or 'timeout' in error:
                    print("  • Verifica connessione internet")
                    print("  • Controlla firewall/proxy")
                    print("  • Testa server/porta manualmente")
                elif 'ssl' in error or 'certificate' in error:
                    print("  • Problema certificato SSL")
                    print("  • Verifica data/ora sistema")
                    print("  • Aggiorna certificati CA")
                else:
                    print("  • Controlla logs dettagliati")
                    print("  • Verifica configurazione provider")
                
                return False
                
        except Exception as e:
            print(f"\\n💥 ECCEZIONE DURANTE TEST")
            print(f"Tipo: {type(e).__name__}")
            print(f"Messaggio: {e}")
            
            import traceback
            print("\\n🔍 Stack trace:")
            traceback.print_exc()
            
            return False
    
    def interactive_mode(self):
        """Modalità debug interattiva."""
        print("🛠️  MODALITÀ DEBUG INTERATTIVA")
        print("=" * 50)
        print("Seleziona test da eseguire:")
        print("1. Diagnosi IMAP")
        print("2. Debug Gmail OAuth2") 
        print("3. Test operazione email")
        print("4. Esci")
        
        while True:
            try:
                choice = input("\\n👉 Scelta (1-4): ").strip()
                
                if choice == '1':
                    asyncio.run(self._interactive_imap_debug())
                elif choice == '2':
                    asyncio.run(self._interactive_gmail_debug())
                elif choice == '3':
                    asyncio.run(self._interactive_email_test())
                elif choice == '4':
                    print("👋 Ciao!")
                    break
                else:
                    print("❌ Scelta non valida")
                    
            except KeyboardInterrupt:
                print("\\n👋 Interruzione utente, ciao!")
                break
            except Exception as e:
                print(f"❌ Errore: {e}")
    
    async def _interactive_imap_debug(self):
        """Debug IMAP interattivo."""
        print("\\n📧 DEBUG IMAP INTERATTIVO")
        try:
            server = input("Server IMAP (es. imap.gmail.com): ").strip()
            port = int(input("Porta (default 993): ") or "993")
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            if all([server, username, password]):
                await self.diagnose_imap_connection(server, port, username, password)
            else:
                print("❌ Tutti i campi sono obbligatori")
                
        except ValueError:
            print("❌ Porta deve essere un numero")
        except Exception as e:
            print(f"❌ Errore: {e}")
    
    async def _interactive_gmail_debug(self):
        """Debug Gmail interattivo."""
        print("\\n🔍 DEBUG GMAIL OAUTH2 INTERATTIVO")
        try:
            creds_path = input("Percorso credenziali JSON: ").strip()
            
            if creds_path:
                await self.debug_gmail_oauth(creds_path)
            else:
                print("❌ Percorso credenziali richiesto")
                
        except Exception as e:
            print(f"❌ Errore: {e}")
    
    async def _interactive_email_test(self):
        """Test email interattivo."""
        print("\\n🧪 TEST EMAIL INTERATTIVO")
        try:
            provider = input("Provider (gmail/outlook/imap): ").strip().lower()
            operation = input("Operazione (list/get_folders): ").strip().lower()
            
            if provider == 'imap':
                config = {
                    'operation': operation,
                    'provider': 'imap',
                    'credentials_path': '/dummy',
                    'imap_server': input("Server IMAP: ").strip(),
                    'imap_port': int(input("Porta (993): ") or "993"),
                    'username': input("Username: ").strip(),
                    'password': input("Password: ").strip(),
                    'max_emails': int(input("Max email (10): ") or "10")
                }
            else:
                config = {
                    'operation': operation,
                    'provider': provider,
                    'credentials_path': input("Percorso credenziali: ").strip(),
                    'max_emails': int(input("Max email (10): ") or "10")
                }
            
            await self.test_email_operation(config)
            
        except ValueError:
            print("❌ Valore numerico non valido")
        except Exception as e:
            print(f"❌ Errore: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug tool Email Reader Plugin')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Modalità interattiva')
    parser.add_argument('--imap-test', nargs=4, metavar=('SERVER', 'PORT', 'USER', 'PASS'),
                       help='Test IMAP diretto')
    parser.add_argument('--gmail-debug', metavar='CREDENTIALS_PATH',
                       help='Debug Gmail OAuth2')
    
    args = parser.parse_args()
    
    debugger = EmailDebugger()
    
    if args.interactive:
        debugger.interactive_mode()
    elif args.imap_test:
        server, port, user, password = args.imap_test
        asyncio.run(debugger.diagnose_imap_connection(server, int(port), user, password))
    elif args.gmail_debug:
        asyncio.run(debugger.debug_gmail_oauth(args.gmail_debug))
    else:
        debugger.interactive_mode()