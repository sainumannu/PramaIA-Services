"""
Test REALI Email Reader Plugin - Connessioni Provider Veri

Questi test si collegano effettivamente ai provider email per verificare
che il plugin funzioni in condizioni reali di produzione.

NOTA: Richiede credenziali valide configurate!
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Aggiungi path src
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from email_processor import EmailProcessor

class RealEmailTests:
    """Test reali con provider email."""
    
    def __init__(self):
        self.processor = EmailProcessor()
        self.base_dir = Path(__file__).parent
        self.credentials_dir = self.base_dir / "credentials"
        
        # Crea cartella credenziali se non esistente
        self.credentials_dir.mkdir(exist_ok=True)
        
        print("🔧 Test Email Reader Plugin - CONNESSIONI REALI")
        print("=" * 60)
        print("⚠️  ATTENZIONE: Questi test richiedono credenziali valide!")
        print("📁 Posiziona le credenziali in: credentials/")
        print("")
    
    def check_credentials(self):
        """Verifica presenza file credenziali."""
        required_files = {
            'gmail': self.credentials_dir / "gmail_credentials.json",
            'outlook': self.credentials_dir / "outlook_credentials.json"
        }
        
        available_providers = []
        
        print("📋 Controllo credenziali disponibili:")
        
        for provider, file_path in required_files.items():
            if file_path.exists():
                print(f"✅ {provider.upper()}: {file_path}")
                available_providers.append(provider)
            else:
                print(f"❌ {provider.upper()}: Mancante {file_path}")
        
        # IMAP non richiede file se inseriti direttamente
        print("ℹ️  IMAP: Configura parametri direttamente nei test")
        
        return available_providers
    
    async def test_real_gmail(self):
        """Test reale Gmail API."""
        gmail_creds = self.credentials_dir / "gmail_credentials.json"
        
        if not gmail_creds.exists():
            print("❌ Test Gmail saltato: credenziali mancanti")
            return False
        
        print("\\n🧪 TEST GMAIL REALE")
        print("-" * 30)
        
        try:
            inputs = {
                'operation': 'list',
                'provider': 'gmail',
                'credentials_path': str(gmail_creds),
                'max_emails': 5,
                'unread_only': True,
                'include_body': False  # Per velocità
            }
            
            print("🔄 Connessione Gmail in corso...")
            result = await self.processor.process(inputs)
            
            if result['success']:
                print(f"✅ Gmail connesso: {result['email_count']} email trovate")
                
                # Mostra dettagli email
                for i, email in enumerate(result.get('emails', [])[:3], 1):
                    print(f"  {i}. {email.get('subject', 'No subject')[:50]}...")
                    print(f"     Da: {email.get('sender', 'Unknown')}")
                    print(f"     Data: {email.get('date', 'Unknown')}")
                
                # Info provider
                provider_info = result.get('provider_info', {})
                if provider_info:
                    print(f"📊 Account: {provider_info.get('user_email', 'N/A')}")
                    quota = provider_info.get('quota_usage', {})
                    if quota:
                        print(f"📧 Messaggi totali: {quota.get('messages', 'N/A')}")
                
                return True
            else:
                print(f"❌ Errore Gmail: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Eccezione Gmail: {e}")
            return False
    
    async def test_real_imap_gmail(self):
        """Test reale IMAP con Gmail (richiede App Password)."""
        print("\\n🧪 TEST IMAP GMAIL REALE")
        print("-" * 30)
        
        # Leggi credenziali da environment o input utente
        username = os.getenv('GMAIL_USERNAME')
        password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not username or not password:
            print("⚠️  Configura variabili ambiente:")
            print("   set GMAIL_USERNAME=your-email@gmail.com")
            print("   set GMAIL_APP_PASSWORD=your-16-char-app-password")
            print("❌ Test IMAP Gmail saltato: credenziali ambiente mancanti")
            return False
        
        try:
            inputs = {
                'operation': 'list',
                'provider': 'imap',
                'credentials_path': '/dummy',  # Non usato per IMAP
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'username': username,
                'password': password,
                'max_emails': 5,
                'include_body': False
            }
            
            print(f"🔄 Connessione IMAP Gmail per {username}...")
            result = await self.processor.process(inputs)
            
            if result['success']:
                print(f"✅ IMAP Gmail connesso: {result['email_count']} email trovate")
                
                # Mostra email
                for i, email in enumerate(result.get('emails', [])[:3], 1):
                    print(f"  {i}. {email.get('subject', 'No subject')[:50]}...")
                    print(f"     Da: {email.get('sender', 'Unknown')}")
                
                return True
            else:
                print(f"❌ Errore IMAP Gmail: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Eccezione IMAP Gmail: {e}")
            return False
    
    async def test_real_folders(self):
        """Test reale recupero cartelle."""
        print("\\n🧪 TEST CARTELLE IMAP REALE")
        print("-" * 30)
        
        username = os.getenv('GMAIL_USERNAME')
        password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not username or not password:
            print("❌ Test cartelle saltato: credenziali ambiente mancanti")
            return False
        
        try:
            inputs = {
                'operation': 'get_folders',
                'provider': 'imap',
                'credentials_path': '/dummy',
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'username': username,
                'password': password
            }
            
            print("🔄 Recupero cartelle Gmail...")
            result = await self.processor.process(inputs)
            
            if result['success']:
                folders = result.get('folders', [])
                print(f"✅ Trovate {len(folders)} cartelle:")
                
                for folder in folders[:10]:  # Prime 10 cartelle
                    name = folder.get('name', 'Unknown')
                    print(f"  📁 {name}")
                
                return True
            else:
                print(f"❌ Errore cartelle: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Eccezione cartelle: {e}")
            return False
    
    async def test_real_outlook(self):
        """Test reale Outlook/Exchange."""
        outlook_creds = self.credentials_dir / "outlook_credentials.json"
        
        if not outlook_creds.exists():
            print("❌ Test Outlook saltato: credenziali mancanti")
            return False
        
        print("\\n🧪 TEST OUTLOOK REALE")
        print("-" * 30)
        
        try:
            inputs = {
                'operation': 'list',
                'provider': 'outlook',
                'credentials_path': str(outlook_creds),
                'max_emails': 5,
                'include_body': False
            }
            
            print("🔄 Connessione Outlook in corso...")
            result = await self.processor.process(inputs)
            
            if result['success']:
                print(f"✅ Outlook connesso: {result['email_count']} email trovate")
                
                for i, email in enumerate(result.get('emails', [])[:3], 1):
                    print(f"  {i}. {email.get('subject', 'No subject')[:50]}...")
                    print(f"     Da: {email.get('sender', 'Unknown')}")
                
                return True
            else:
                print(f"❌ Errore Outlook: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Eccezione Outlook: {e}")
            return False
    
    async def test_performance(self):
        """Test performance con recupero email multiple."""
        print("\\n⚡ TEST PERFORMANCE")
        print("-" * 30)
        
        username = os.getenv('GMAIL_USERNAME')
        password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not username or not password:
            print("❌ Test performance saltato: credenziali ambiente mancanti")
            return False
        
        import time
        
        try:
            # Test con 50 email
            inputs = {
                'operation': 'list',
                'provider': 'imap',
                'credentials_path': '/dummy',
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'username': username,
                'password': password,
                'max_emails': 50,
                'include_body': True  # Include corpo per test reale
            }
            
            print("🔄 Test performance con 50 email...")
            start_time = time.time()
            
            result = await self.processor.process(inputs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result['success']:
                email_count = result['email_count']
                print(f"✅ Performance: {email_count} email in {duration:.2f} secondi")
                print(f"📊 Velocità: {email_count/duration:.1f} email/secondo")
                
                # Statistiche corpo email
                total_chars = sum(len(email.get('body_text', '')) for email in result.get('emails', []))
                print(f"📝 Testo totale: {total_chars:,} caratteri")
                
                return True
            else:
                print(f"❌ Errore performance: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Eccezione performance: {e}")
            return False
    
    def create_sample_credentials(self):
        """Crea file credenziali esempio."""
        print("\\n📝 Creazione file credenziali esempio...")
        
        # Gmail template
        gmail_template = {
            "installed": {
                "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                "client_secret": "YOUR_CLIENT_SECRET",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        gmail_file = self.credentials_dir / "gmail_credentials.json.template"
        gmail_file.write_text(json.dumps(gmail_template, indent=2))
        print(f"📧 Gmail template: {gmail_file}")
        
        # Outlook template
        outlook_template = {
            "username": "YOUR_USERNAME@company.com",
            "password": "YOUR_PASSWORD",
            "email": "YOUR_EMAIL@company.com",
            "server": "outlook.office365.com"
        }
        
        outlook_file = self.credentials_dir / "outlook_credentials.json.template"
        outlook_file.write_text(json.dumps(outlook_template, indent=2))
        print(f"📨 Outlook template: {outlook_file}")
        
        print("\\n📋 Per usare:")
        print("1. Rinomina file .template rimuovendo .template")
        print("2. Inserisci le tue credenziali reali")
        print("3. Per IMAP Gmail, configura App Password in variabili ambiente")

async def run_real_tests():
    """Esegue tutti i test reali disponibili."""
    tester = RealEmailTests()
    
    # Controlla credenziali disponibili
    available_providers = tester.check_credentials()
    
    print("\\n🚀 AVVIO TEST REALI")
    print("=" * 40)
    
    results = []
    
    # Test Gmail API se disponibile
    if 'gmail' in available_providers:
        result = await tester.test_real_gmail()
        results.append(('Gmail API', result))
    
    # Test IMAP Gmail
    result = await tester.test_real_imap_gmail()
    results.append(('IMAP Gmail', result))
    
    # Test cartelle
    result = await tester.test_real_folders()
    results.append(('Cartelle IMAP', result))
    
    # Test Outlook se disponibile
    if 'outlook' in available_providers:
        result = await tester.test_real_outlook()
        results.append(('Outlook', result))
    
    # Test performance
    result = await tester.test_performance()
    results.append(('Performance', result))
    
    # Riepilogo risultati
    print("\\n📊 RIEPILOGO TEST REALI")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSATO" if result else "❌ FALLITO"
        print(f"{test_name:20} {status}")
    
    print(f"\\n📈 Risultato finale: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 Tutti i test reali sono passati!")
        print("💪 Plugin Email Reader pronto per produzione!")
    else:
        print(f"⚠️  {total - passed} test hanno problemi")
        print("🔧 Controlla credenziali e connessioni di rete")
    
    return passed == total

def setup_instructions():
    """Mostra istruzioni setup per test reali."""
    print("\\n📋 SETUP TEST REALI")
    print("=" * 40)
    print()
    print("🔧 Per Gmail API:")
    print("1. Google Cloud Console → Nuovo progetto")
    print("2. Abilita Gmail API")  
    print("3. Crea credenziali OAuth2 → App Desktop")
    print("4. Scarica JSON → credentials/gmail_credentials.json")
    print()
    print("🔐 Per IMAP Gmail:")
    print("1. Gmail → Gestisci account Google → Sicurezza")
    print("2. Verifica 2 passaggi → Password app")
    print("3. Genera password app 16 caratteri")
    print("4. Variabili ambiente:")
    print("   set GMAIL_USERNAME=your-email@gmail.com")
    print("   set GMAIL_APP_PASSWORD=abcd-efgh-ijkl-mnop")
    print()
    print("📨 Per Outlook:")
    print("1. Crea credentials/outlook_credentials.json")
    print("2. Username/password aziendale")
    print("3. Per Office 365 usa App Password")
    print()
    print("▶️  Poi esegui: python real_email_tests.py")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test reali Email Reader Plugin')
    parser.add_argument('--setup', action='store_true', help='Mostra istruzioni setup')
    parser.add_argument('--create-templates', action='store_true', help='Crea file template credenziali')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_instructions()
    elif args.create_templates:
        tester = RealEmailTests()
        tester.create_sample_credentials()
    else:
        # Esegui test reali
        success = asyncio.run(run_real_tests())
        exit(0 if success else 1)