"""
Test suite per Email Reader Plugin

Testa tutte le operazioni email supportate con mock providers.
"""

import os
import sys
import asyncio
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Aggiungi path del src
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from email_processor import EmailProcessor

class MockIMAPConnection:
    """Mock IMAP connection per test."""
    
    def __init__(self):
        self.selected_folder = None
        self.logged_in = False
    
    def login(self, username, password):
        if username and password:
            self.logged_in = True
        else:
            raise Exception("Credenziali non valide")
    
    def select(self, folder):
        self.selected_folder = folder
        return ('OK', [b'10'])  # 10 messaggi
    
    def search(self, charset, criteria):
        # Simula ricerca con alcuni ID email
        return ('OK', [b'1 2 3 4 5'])
    
    def fetch(self, email_id, parts):
        if parts == '(RFC822)':
            # Simula email completa
            email_content = b"""From: test@example.com
To: user@example.com
Subject: Test Email
Date: Mon, 29 Nov 2025 10:00:00 +0000

This is a test email body."""
            return ('OK', [(b'1 (RFC822 {123}', email_content), b')'])
        
        elif parts == '(FLAGS)':
            # Simula flags email
            return ('OK', [b'1 (FLAGS (\\Seen))'])
    
    def list(self):
        # Simula lista cartelle
        folders = [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Sent"',
            b'(\\HasNoChildren) "/" "Drafts"'
        ]
        return ('OK', folders)
    
    def logout(self):
        self.logged_in = False

class TestEmailProcessor(unittest.TestCase):
    """Test case per Email Processor."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.processor = EmailProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Crea file credenziali mock
        self.gmail_creds = self.temp_path / "gmail_credentials.json"
        self.gmail_creds.write_text(json.dumps({
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }))
        
        self.outlook_creds = self.temp_path / "outlook_credentials.json"
        self.outlook_creds.write_text(json.dumps({
            "username": "test@outlook.com",
            "password": "test_password",
            "email": "test@outlook.com"
        }))
    
    def tearDown(self):
        """Cleanup dopo test."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    @patch('email_processor.imaplib')
    async def test_invalid_operation(self, mock_imaplib):
        """Test operazione non valida."""
        # Setup mock IMAP per autenticazione
        mock_connection = MockIMAPConnection()
        mock_imaplib.IMAP4_SSL.return_value = mock_connection
        
        inputs = {
            'operation': 'operazione_inesistente',
            'provider': 'imap',
            'credentials_path': '/dummy/path',
            'imap_server': 'imap.test.com',
            'username': 'test@test.com',
            'password': 'password'
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("non supportata", result['error'])
        print(f"✅ Test invalid_operation: {result['message']}")
    
    async def test_missing_parameters(self):
        """Test parametri mancanti."""
        # Test senza operazione
        inputs = {
            'provider': 'gmail',
            'credentials_path': str(self.gmail_creds)
        }
        
        result = await self.processor.process(inputs)
        self.assertFalse(result['success'])
        self.assertIn("Operazione non specificata", result['error'])
        
        # Test senza provider
        inputs = {
            'operation': 'list',
            'credentials_path': str(self.gmail_creds)
        }
        
        result = await self.processor.process(inputs)
        self.assertFalse(result['success'])
        self.assertIn("Provider non specificato", result['error'])
        
        print("✅ Test missing_parameters completato")
    
    @patch('email_processor.imaplib')
    async def test_imap_authentication(self, mock_imaplib):
        """Test autenticazione IMAP."""
        # Setup mock
        mock_connection = MockIMAPConnection()
        mock_imaplib.IMAP4_SSL.return_value = mock_connection
        
        inputs = {
            'operation': 'get_folders',
            'provider': 'imap',
            'credentials_path': '/dummy/path',
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'username': 'test@gmail.com',
            'password': 'test_password'
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertIn('folders', result)
        print(f"✅ Test IMAP authentication: {result['message']}")
    
    @patch('email_processor.imaplib')
    async def test_imap_list_emails(self, mock_imaplib):
        """Test lista email IMAP."""
        # Setup mock
        mock_connection = MockIMAPConnection()
        mock_imaplib.IMAP4_SSL.return_value = mock_connection
        
        inputs = {
            'operation': 'list',
            'provider': 'imap',
            'credentials_path': '/dummy/path',
            'imap_server': 'imap.gmail.com',
            'username': 'test@gmail.com',
            'password': 'test_password',
            'max_emails': 5,
            'include_body': True
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertIn('emails', result)
        self.assertGreater(result['email_count'], 0)
        print(f"✅ Test IMAP list emails: {result['message']}")
    
    @patch('email_processor.GMAIL_AVAILABLE', False)
    async def test_gmail_unavailable(self):
        """Test Gmail quando dipendenze non disponibili."""
        inputs = {
            'operation': 'list',
            'provider': 'gmail',
            'credentials_path': str(self.gmail_creds)
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("Dipendenze Gmail non disponibili", result['error'])
        print(f"✅ Test Gmail unavailable: {result['message']}")
    
    @patch('email_processor.OUTLOOK_AVAILABLE', False)
    async def test_outlook_unavailable(self):
        """Test Outlook quando dipendenze non disponibili."""
        inputs = {
            'operation': 'list',
            'provider': 'outlook',
            'credentials_path': str(self.outlook_creds)
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("Dipendenze Outlook non disponibili", result['error'])
        print(f"✅ Test Outlook unavailable: {result['message']}")
    
    async def test_unsupported_provider(self):
        """Test provider non supportato."""
        inputs = {
            'operation': 'list',
            'provider': 'yahoo',  # Non supportato
            'credentials_path': '/dummy/path'
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("Provider 'yahoo' non supportato", result['error'])
        print(f"✅ Test unsupported provider: {result['message']}")
    
    @patch('email_processor.imaplib')
    async def test_imap_search_filters(self, mock_imaplib):
        """Test filtri ricerca IMAP."""
        mock_connection = MockIMAPConnection()
        mock_imaplib.IMAP4_SSL.return_value = mock_connection
        
        inputs = {
            'operation': 'list',
            'provider': 'imap',
            'credentials_path': '/dummy/path',
            'imap_server': 'imap.gmail.com',
            'username': 'test@gmail.com',
            'password': 'test_password',
            'unread_only': True,
            'date_from': '2025-11-01',
            'date_to': '2025-11-29',
            'sender_filter': 'noreply@example.com',
            'subject_filter': 'Important'
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertIn('emails', result)
        print(f"✅ Test IMAP search filters: {result['message']}")
    
    async def test_incomplete_imap_credentials(self):
        """Test credenziali IMAP incomplete."""
        inputs = {
            'operation': 'list',
            'provider': 'imap',
            'credentials_path': '/dummy/path',
            'imap_server': 'imap.gmail.com',
            # Mancano username e password
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("Parametri IMAP incompleti", result['error'])
        print(f"✅ Test incomplete IMAP credentials: {result['message']}")
    
    async def test_unimplemented_operations(self):
        """Test operazioni non ancora implementate."""
        operations_to_test = ['read', 'search', 'get_attachments', 'mark_read']
        
        for operation in operations_to_test:
            inputs = {
                'operation': operation,
                'provider': 'imap',
                'credentials_path': '/dummy/path',
                'imap_server': 'imap.gmail.com',
                'username': 'test@gmail.com',
                'password': 'test_password',
                'email_id': 'test123' if operation in ['read', 'get_attachments', 'mark_read'] else None,
                'search_query': 'test query' if operation == 'search' else None
            }
            
            with patch('email_processor.imaplib') as mock_imaplib:
                mock_connection = MockIMAPConnection()
                mock_imaplib.IMAP4_SSL.return_value = mock_connection
                
                result = await self.processor.process(inputs)
                
                # Dovrebbe fallire perché non implementato
                self.assertFalse(result['success'])
                self.assertIn("non ancora implementata", result['error'])
        
        print("✅ Test unimplemented operations completato")

async def run_all_tests():
    """Esegue tutti i test in modo asincrono."""
    print("🚀 Avvio test Email Reader Plugin...")
    print("=" * 60)
    
    test_case = TestEmailProcessor()
    
    # Lista test da eseguire
    tests = [
        test_case.test_invalid_operation,
        test_case.test_missing_parameters,
        test_case.test_imap_authentication,
        test_case.test_imap_list_emails,
        test_case.test_gmail_unavailable,
        test_case.test_outlook_unavailable,
        test_case.test_unsupported_provider,
        test_case.test_imap_search_filters,
        test_case.test_incomplete_imap_credentials,
        test_case.test_unimplemented_operations
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            # Setup
            test_case.setUp()
            
            # Esegui test
            await test_func()
            passed += 1
            
            # Cleanup
            test_case.tearDown()
            
        except Exception as e:
            print(f"❌ Test {test_func.__name__} fallito: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 Risultati test Email Reader:")
    print(f"✅ Passati: {passed}")
    print(f"❌ Falliti: {failed}")
    print(f"📈 Totale: {passed + failed}")
    
    if failed == 0:
        print("🎉 Tutti i test sono passati!")
        print("📧 Plugin Email Reader pronto per integrazione!")
    else:
        print(f"⚠️  {failed} test hanno fallimenti")
    
    return failed == 0

def demo_configuration():
    """Mostra configurazioni esempio per i provider."""
    print("\\n🔧 Configurazioni esempio Email Reader Plugin")
    print("=" * 50)
    
    print("\\n📧 Gmail (OAuth2):")
    print("File credentials.json da Google Cloud Console")
    gmail_example = {
        "installed": {
            "client_id": "your-client-id.apps.googleusercontent.com",
            "client_secret": "your-client-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    print(json.dumps(gmail_example, indent=2))
    
    print("\\n📨 Outlook/Exchange:")
    print("File outlook_credentials.json")
    outlook_example = {
        "username": "your-username@company.com",
        "password": "your-password",
        "email": "your-email@company.com",
        "server": "outlook.office365.com"  # Opzionale
    }
    print(json.dumps(outlook_example, indent=2))
    
    print("\\n🔐 IMAP Generico:")
    print("Parametri diretti nel request")
    imap_example = {
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "your-email@gmail.com",
        "password": "your-app-password"
    }
    print(json.dumps(imap_example, indent=2))

if __name__ == "__main__":
    # Esegui test
    success = asyncio.run(run_all_tests())
    
    # Mostra configurazioni se test passano
    if success:
        demo_configuration()
    
    # Exit code
    sys.exit(0 if success else 1)