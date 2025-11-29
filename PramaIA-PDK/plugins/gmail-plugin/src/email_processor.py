"""
Email Reader Processor - Gestione avanzata lettura email multi-provider.

Supporta Gmail, Outlook, e provider IMAP generici con:
- Autenticazione OAuth2 e password
- Lettura email con filtri avanzati
- Download allegati automatico
- Ricerca semantica
- Gestione cartelle
"""

import os
import sys
import json
import base64
import email
import imaplib
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.utils

# Import condizionali per provider specifici
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

try:
    import exchangelib
    from exchangelib import Credentials as ExchCredentials, Account, DELEGATE
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False

try:
    import ssl
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

# Configurazione logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProcessor:
    """Processore per lettura email multi-provider."""
    
    def __init__(self):
        """Inizializza il processore email."""
        self.gmail_service = None
        self.outlook_account = None
        self.imap_connection = None
        self.current_provider = None
        logger.info("EmailProcessor inizializzato")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue operazione email specificata.
        
        Args:
            inputs: Parametri di input per l'operazione
            
        Returns:
            Dizionario con risultati dell'operazione
        """
        try:
            # Estrai parametri
            operation = inputs.get('operation', '').lower()
            provider = inputs.get('provider', '').lower()
            credentials_path = inputs.get('credentials_path', '')
            
            logger.info(f"Esecuzione operazione: {operation} su provider: {provider}")
            
            # Validazione input base
            if not operation:
                return self._error_result("Operazione non specificata")
            
            if not provider:
                return self._error_result("Provider non specificato")
            
            if not credentials_path:
                return self._error_result("Percorso credenziali richiesto")
            
            # Autentica con provider
            auth_result = await self._authenticate_provider(provider, credentials_path, inputs)
            if not auth_result['success']:
                return auth_result
            
            self.current_provider = provider
            
            # Dispatch operazioni
            operations = {
                'list': self._list_emails,
                'read': self._read_email,
                'search': self._search_emails,
                'get_attachments': self._get_attachments,
                'mark_read': self._mark_as_read,
                'get_folders': self._get_folders
            }
            
            if operation not in operations:
                return self._error_result(f"Operazione '{operation}' non supportata")
            
            # Esegui operazione
            result = await operations[operation](inputs)
            
            # Aggiungi info provider
            result['provider_info'] = auth_result.get('provider_info', {})
            
            logger.info(f"Operazione {operation} completata con successo")
            return result
            
        except Exception as e:
            error_msg = f"Errore durante operazione email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._error_result(error_msg)
        finally:
            # Cleanup connessioni
            await self._cleanup_connections()
    
    async def _authenticate_provider(self, provider: str, credentials_path: str, 
                                   inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Autentica con il provider specificato."""
        try:
            if provider == 'gmail':
                return await self._authenticate_gmail(credentials_path)
            elif provider == 'outlook':
                return await self._authenticate_outlook(credentials_path, inputs)
            elif provider == 'imap':
                return await self._authenticate_imap(inputs)
            else:
                return self._error_result(f"Provider '{provider}' non supportato")
                
        except Exception as e:
            return self._error_result(f"Errore autenticazione {provider}: {e}")
    
    async def _authenticate_gmail(self, credentials_path: str) -> Dict[str, Any]:
        """Autentica con Gmail API."""
        if not GMAIL_AVAILABLE:
            return self._error_result("Dipendenze Gmail non disponibili")
        
        try:
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                     'https://www.googleapis.com/auth/gmail.modify']
            
            creds = None
            token_path = str(Path(credentials_path).parent / 'token.json')
            
            # Carica token esistente
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # Se non valido, esegui flow OAuth
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Salva token per uso futuro
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Costruisci servizio Gmail
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            
            # Ottieni info utente
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            
            return self._success_result("Autenticazione Gmail completata", {
                'provider': 'gmail',
                'authenticated': True,
                'user_email': profile.get('emailAddress'),
                'total_messages': profile.get('messagesTotal', 0),
                'quota_usage': {
                    'messages': profile.get('messagesTotal', 0),
                    'threads': profile.get('threadsTotal', 0)
                }
            })
            
        except Exception as e:
            return self._error_result(f"Errore autenticazione Gmail: {e}")
    
    async def _authenticate_outlook(self, credentials_path: str, 
                                  inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Autentica con Outlook/Exchange."""
        if not OUTLOOK_AVAILABLE:
            return self._error_result("Dipendenze Outlook non disponibili")
        
        try:
            # Carica configurazione
            with open(credentials_path, 'r') as f:
                config = json.load(f)
            
            # Credenziali Exchange
            credentials = ExchCredentials(
                username=config['username'],
                password=config['password']
            )
            
            # Account Exchange
            self.outlook_account = Account(
                primary_smtp_address=config['email'],
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )
            
            # Test connessione
            inbox = self.outlook_account.inbox
            
            return self._success_result("Autenticazione Outlook completata", {
                'provider': 'outlook',
                'authenticated': True,
                'user_email': config['email'],
                'server': self.outlook_account.protocol.service_endpoint,
                'quota_usage': {}
            })
            
        except Exception as e:
            return self._error_result(f"Errore autenticazione Outlook: {e}")
    
    async def _authenticate_imap(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Autentica con server IMAP generico."""
        try:
            server = inputs.get('imap_server')
            port = inputs.get('imap_port', 993)
            username = inputs.get('username')
            password = inputs.get('password')
            
            if not all([server, username, password]):
                return self._error_result("Parametri IMAP incompleti")
            
            # Connessione IMAP SSL
            if SSL_AVAILABLE:
                self.imap_connection = imaplib.IMAP4_SSL(server, port)
            else:
                self.imap_connection = imaplib.IMAP4(server, port)
            
            # Login
            self.imap_connection.login(username, password)
            
            # Test connessione listando cartelle
            folders = self.imap_connection.list()
            
            return self._success_result("Autenticazione IMAP completata", {
                'provider': 'imap',
                'authenticated': True,
                'user_email': username,
                'server': f"{server}:{port}",
                'folders_count': len(folders[1]) if folders[1] else 0,
                'quota_usage': {}
            })
            
        except Exception as e:
            return self._error_result(f"Errore autenticazione IMAP: {e}")
    
    async def _list_emails(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Lista email dal provider."""
        try:
            folder = inputs.get('folder', 'INBOX')
            max_emails = min(inputs.get('max_emails', 50), 500)
            unread_only = inputs.get('unread_only', False)
            date_from = inputs.get('date_from')
            date_to = inputs.get('date_to')
            sender_filter = inputs.get('sender_filter')
            subject_filter = inputs.get('subject_filter')
            include_body = inputs.get('include_body', True)
            include_html = inputs.get('include_html', False)
            
            if self.current_provider == 'gmail':
                return await self._list_emails_gmail(
                    folder, max_emails, unread_only, date_from, date_to,
                    sender_filter, subject_filter, include_body, include_html
                )
            elif self.current_provider == 'outlook':
                return await self._list_emails_outlook(
                    folder, max_emails, unread_only, date_from, date_to,
                    sender_filter, subject_filter, include_body, include_html
                )
            elif self.current_provider == 'imap':
                return await self._list_emails_imap(
                    folder, max_emails, unread_only, date_from, date_to,
                    sender_filter, subject_filter, include_body, include_html
                )
            else:
                return self._error_result("Provider non configurato per list")
                
        except Exception as e:
            return self._error_result(f"Errore durante list emails: {e}")
    
    async def _list_emails_gmail(self, folder: str, max_emails: int, unread_only: bool,
                               date_from: str, date_to: str, sender_filter: str,
                               subject_filter: str, include_body: bool, 
                               include_html: bool) -> Dict[str, Any]:
        """Lista email da Gmail."""
        try:
            # Costruisci query Gmail
            query_parts = []
            
            if folder and folder != 'INBOX':
                query_parts.append(f"in:{folder.lower()}")
            
            if unread_only:
                query_parts.append("is:unread")
            
            if date_from:
                query_parts.append(f"after:{date_from}")
            
            if date_to:
                query_parts.append(f"before:{date_to}")
            
            if sender_filter:
                query_parts.append(f"from:{sender_filter}")
            
            if subject_filter:
                query_parts.append(f"subject:{subject_filter}")
            
            query = ' '.join(query_parts) if query_parts else ""
            
            # Esegui ricerca
            result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_emails
            ).execute()
            
            messages = result.get('messages', [])
            emails = []
            
            # Recupera dettagli per ogni email
            for msg in messages:
                try:
                    email_detail = await self._get_gmail_email_detail(
                        msg['id'], include_body, include_html
                    )
                    if email_detail:
                        emails.append(email_detail)
                except Exception as e:
                    logger.warning(f"Errore recupero email Gmail {msg['id']}: {e}")
                    continue
            
            return self._success_result(
                f"Recuperate {len(emails)} email da Gmail",
                {
                    'emails': emails,
                    'email_count': len(emails),
                    'total_available': result.get('resultSizeEstimate', len(emails))
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore Gmail list: {e}")
    
    async def _get_gmail_email_detail(self, email_id: str, include_body: bool,
                                    include_html: bool) -> Optional[Dict[str, Any]]:
        """Recupera dettagli email Gmail."""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}
            
            # Estrai corpo email
            body_text = ""
            body_html = ""
            attachments = []
            
            if include_body or include_html:
                body_text, body_html, attachments = self._extract_gmail_body(payload)
            
            # Determina se letta
            is_read = 'UNREAD' not in message.get('labelIds', [])
            
            return {
                'id': email_id,
                'subject': headers.get('Subject', 'Senza oggetto'),
                'sender': headers.get('From', 'Mittente sconosciuto'),
                'recipients': [headers.get('To', '')],
                'date': headers.get('Date', ''),
                'body_text': body_text if include_body else "",
                'body_html': body_html if include_html else "",
                'is_read': is_read,
                'attachments': attachments,
                'folder': 'INBOX',  # Gmail non ha cartelle tradizionali
                'labels': message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Errore dettaglio Gmail {email_id}: {e}")
            return None
    
    def _extract_gmail_body(self, payload: Dict[str, Any]) -> Tuple[str, str, List[Dict]]:
        """Estrae corpo e allegati da payload Gmail."""
        body_text = ""
        body_html = ""
        attachments = []
        
        def _extract_parts(part):
            nonlocal body_text, body_html, attachments
            
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            elif mime_type == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_html += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            elif part.get('filename'):
                # Allegato
                attachments.append({
                    'filename': part.get('filename'),
                    'size': part.get('body', {}).get('size', 0),
                    'attachment_id': part.get('body', {}).get('attachmentId'),
                    'content_type': mime_type
                })
            
            # Processa parti annidate
            for subpart in part.get('parts', []):
                _extract_parts(subpart)
        
        _extract_parts(payload)
        return body_text, body_html, attachments
    
    async def _list_emails_imap(self, folder: str, max_emails: int, unread_only: bool,
                              date_from: str, date_to: str, sender_filter: str,
                              subject_filter: str, include_body: bool,
                              include_html: bool) -> Dict[str, Any]:
        """Lista email da server IMAP."""
        try:
            # Seleziona cartella
            self.imap_connection.select(folder)
            
            # Costruisci criteri ricerca IMAP
            criteria = ['ALL']
            
            if unread_only:
                criteria = ['UNSEEN']
            
            if date_from:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                criteria.append(f'SINCE {date_obj.strftime("%d-%b-%Y")}')
            
            if date_to:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                criteria.append(f'BEFORE {date_obj.strftime("%d-%b-%Y")}')
            
            if sender_filter:
                criteria.append(f'FROM "{sender_filter}"')
            
            if subject_filter:
                criteria.append(f'SUBJECT "{subject_filter}"')
            
            # Esegui ricerca
            search_criteria = '(' + ' '.join(criteria) + ')' if len(criteria) > 1 else criteria[0]
            typ, data = self.imap_connection.search(None, search_criteria)
            
            if typ != 'OK':
                return self._error_result("Errore ricerca IMAP")
            
            # Recupera email IDs
            email_ids = data[0].split()
            email_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
            
            emails = []
            for email_id in email_ids:
                try:
                    email_detail = await self._get_imap_email_detail(
                        email_id, include_body, include_html
                    )
                    if email_detail:
                        emails.append(email_detail)
                except Exception as e:
                    logger.warning(f"Errore recupero email IMAP {email_id}: {e}")
                    continue
            
            return self._success_result(
                f"Recuperate {len(emails)} email via IMAP",
                {
                    'emails': emails,
                    'email_count': len(emails),
                    'total_available': len(data[0].split()) if data[0] else 0
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore IMAP list: {e}")
    
    async def _get_imap_email_detail(self, email_id: bytes, include_body: bool,
                                   include_html: bool) -> Optional[Dict[str, Any]]:
        """Recupera dettagli email IMAP."""
        try:
            # Recupera email
            typ, data = self.imap_connection.fetch(email_id, '(RFC822)')
            if typ != 'OK':
                return None
            
            # Parsifica email
            email_message = email.message_from_bytes(data[0][1])
            
            # Estrai headers
            subject = email_message.get('Subject', 'Senza oggetto')
            sender = email_message.get('From', 'Mittente sconosciuto')
            recipients = email_message.get_all('To', [])
            date_str = email_message.get('Date', '')
            
            # Estrai corpo
            body_text = ""
            body_html = ""
            attachments = []
            
            if include_body or include_html:
                body_text, body_html, attachments = self._extract_imap_body(email_message)
            
            # Determina se letta (recupera flags)
            typ, flag_data = self.imap_connection.fetch(email_id, '(FLAGS)')
            is_read = b'\\Seen' in flag_data[0] if flag_data else False
            
            return {
                'id': email_id.decode(),
                'subject': subject,
                'sender': sender,
                'recipients': recipients,
                'date': date_str,
                'body_text': body_text if include_body else "",
                'body_html': body_html if include_html else "",
                'is_read': is_read,
                'attachments': attachments,
                'folder': 'INBOX'  # TODO: recupera cartella corrente
            }
            
        except Exception as e:
            logger.error(f"Errore dettaglio IMAP {email_id}: {e}")
            return None
    
    def _extract_imap_body(self, email_message) -> Tuple[str, str, List[Dict]]:
        """Estrae corpo e allegati da email IMAP."""
        body_text = ""
        body_html = ""
        attachments = []
        
        def _extract_parts(part):
            nonlocal body_text, body_html, attachments
            
            content_type = part.get_content_type()
            
            if content_type == 'text/plain' and not part.get_filename():
                body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            elif content_type == 'text/html' and not part.get_filename():
                body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            elif part.get_filename():
                # Allegato
                attachments.append({
                    'filename': part.get_filename(),
                    'size': len(part.get_payload(decode=True)) if part.get_payload() else 0,
                    'content_type': content_type
                })
        
        if email_message.is_multipart():
            for part in email_message.walk():
                _extract_parts(part)
        else:
            _extract_parts(email_message)
        
        return body_text, body_html, attachments
    
    async def _read_email(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Legge email specifica."""
        email_id = inputs.get('email_id')
        if not email_id:
            return self._error_result("email_id richiesto per operazione read")
        
        # TODO: Implementa lettura email specifica per provider
        return self._error_result("Operazione read non ancora implementata")
    
    async def _search_emails(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Cerca email con query."""
        search_query = inputs.get('search_query')
        if not search_query:
            return self._error_result("search_query richiesta per operazione search")
        
        # TODO: Implementa ricerca avanzata
        return self._error_result("Operazione search non ancora implementata")
    
    async def _get_attachments(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Scarica allegati email."""
        # TODO: Implementa download allegati
        return self._error_result("Operazione get_attachments non ancora implementata")
    
    async def _mark_as_read(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Marca email come letta."""
        # TODO: Implementa mark as read
        return self._error_result("Operazione mark_read non ancora implementata")
    
    async def _get_folders(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Lista cartelle disponibili."""
        try:
            if self.current_provider == 'imap':
                typ, folders = self.imap_connection.list()
                if typ == 'OK':
                    folder_list = []
                    for folder in folders:
                        folder_info = folder.decode().split('"')
                        if len(folder_info) >= 3:
                            folder_list.append({
                                'name': folder_info[-1].strip(),
                                'full_name': folder_info[-1].strip(),
                                'message_count': 0,  # TODO: conta messaggi
                                'unread_count': 0    # TODO: conta non letti
                            })
                    
                    return self._success_result(
                        f"Trovate {len(folder_list)} cartelle",
                        {'folders': folder_list}
                    )
            
            # TODO: Implementa per Gmail e Outlook
            return self._error_result("get_folders non implementato per questo provider")
            
        except Exception as e:
            return self._error_result(f"Errore recupero cartelle: {e}")
    
    async def _cleanup_connections(self):
        """Cleanup connessioni attive."""
        try:
            if self.imap_connection:
                self.imap_connection.logout()
                self.imap_connection = None
            
            # Gmail e Outlook non richiedono cleanup esplicito
            self.gmail_service = None
            self.outlook_account = None
            self.current_provider = None
            
        except Exception as e:
            logger.warning(f"Errore cleanup connessioni: {e}")
    
    def _success_result(self, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crea risultato di successo."""
        result = {
            'success': True,
            'message': message,
            'error': ''
        }
        if data:
            result.update(data)
        return result
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Crea risultato di errore."""
        return {
            'success': False,
            'message': f"Errore: {error_message}",
            'error': error_message,
            'emails': [],
            'email_count': 0,
            'folders': [],
            'attachments_info': [],
            'provider_info': {}
        }