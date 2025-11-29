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
                'get_folders': self._get_folders,
                'manage_labels': self._manage_labels,
                'move_email': self._move_email,
                'get_stats': self._get_email_stats
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
    
    # NUOVE FUNZIONI DI SUPPORTO PER OPERAZIONI AGGIUNTIVE
    
    async def _get_gmail_attachments_detail(self, email_id: str) -> List[Dict[str, Any]]:
        """Recupera info dettagliate allegati Gmail."""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            attachments = []
            payload = message['payload']
            
            def _extract_attachment_info(part):
                if part.get('filename') and part.get('body', {}).get('attachmentId'):
                    attachments.append({
                        'filename': part['filename'],
                        'attachment_id': part['body']['attachmentId'],
                        'size': part['body'].get('size', 0),
                        'content_type': part.get('mimeType', ''),
                        'downloadable': True
                    })
                
                for subpart in part.get('parts', []):
                    _extract_attachment_info(subpart)
            
            _extract_attachment_info(payload)
            return attachments
            
        except Exception as e:
            logger.error(f"Errore info allegati Gmail {email_id}: {e}")
            return []
    
    async def _search_emails_gmail(self, search_query: str, search_from: str,
                                 search_to: str, search_subject: str, search_body: str,
                                 date_from: str, date_to: str, has_attachments: bool,
                                 is_unread: bool, max_results: int, folder: str) -> Dict[str, Any]:
        """Ricerca avanzata email Gmail."""
        try:
            # Costruisci query Gmail avanzata
            query_parts = []
            
            if search_query:
                query_parts.append(search_query)
            
            if search_from:
                query_parts.append(f"from:{search_from}")
            
            if search_to:
                query_parts.append(f"to:{search_to}")
            
            if search_subject:
                query_parts.append(f"subject:({search_subject})")
            
            if search_body:
                query_parts.append(f"({search_body})")
            
            if date_from:
                query_parts.append(f"after:{date_from}")
            
            if date_to:
                query_parts.append(f"before:{date_to}")
            
            if has_attachments:
                query_parts.append("has:attachment")
            
            if is_unread:
                query_parts.append("is:unread")
            
            if folder and folder != 'INBOX':
                query_parts.append(f"in:{folder.lower()}")
            
            query = ' '.join(query_parts) if query_parts else ""
            
            # Esegui ricerca
            result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            emails = []
            
            # Recupera dettagli email
            for msg in messages:
                try:
                    email_detail = await self._get_gmail_email_detail(
                        msg['id'], True, False  # Include body, non HTML
                    )
                    if email_detail:
                        emails.append(email_detail)
                except Exception as e:
                    logger.warning(f"Errore recupero email ricerca Gmail {msg['id']}: {e}")
                    continue
            
            return self._success_result(
                f"Trovate {len(emails)} email corrispondenti alla ricerca",
                {
                    'emails': emails,
                    'email_count': len(emails),
                    'query_used': query,
                    'total_results': result.get('resultSizeEstimate', len(emails))
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore ricerca Gmail: {e}")
    
    async def _read_email(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Legge email specifica."""
        email_id = inputs.get('email_id')
        if not email_id:
            return self._error_result("email_id richiesto per operazione read")
        
        try:
            include_body = inputs.get('include_body', True)
            include_html = inputs.get('include_html', False)
            include_attachments = inputs.get('include_attachments', True)
            
            if self.current_provider == 'gmail':
                email_detail = await self._get_gmail_email_detail(
                    email_id, include_body, include_html
                )
                if email_detail and include_attachments:
                    # Aggiungi info dettagliate allegati
                    email_detail['attachments'] = await self._get_gmail_attachments_detail(email_id)
                
                if email_detail:
                    return self._success_result(
                        f"Email {email_id} recuperata con successo",
                        {'email': email_detail}
                    )
                else:
                    return self._error_result(f"Email {email_id} non trovata")
            
            elif self.current_provider == 'imap':
                email_detail = await self._get_imap_email_detail(
                    email_id.encode(), include_body, include_html
                )
                if email_detail:
                    return self._success_result(
                        f"Email {email_id} recuperata con successo",
                        {'email': email_detail}
                    )
                else:
                    return self._error_result(f"Email {email_id} non trovata")
            
            else:
                return self._error_result("Provider non supportato per read")
                
        except Exception as e:
            return self._error_result(f"Errore lettura email {email_id}: {e}")
    
    async def _search_emails(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Cerca email con query avanzata."""
        try:
            # Parametri ricerca
            search_query = inputs.get('search_query', '')
            search_from = inputs.get('search_from', '')
            search_to = inputs.get('search_to', '')
            search_subject = inputs.get('search_subject', '')
            search_body = inputs.get('search_body', '')
            date_from = inputs.get('date_from')
            date_to = inputs.get('date_to')
            has_attachments = inputs.get('has_attachments')
            is_unread = inputs.get('is_unread')
            max_results = min(inputs.get('max_results', 100), 500)
            folder = inputs.get('folder', 'INBOX')
            
            if self.current_provider == 'gmail':
                return await self._search_emails_gmail(
                    search_query, search_from, search_to, search_subject,
                    search_body, date_from, date_to, has_attachments,
                    is_unread, max_results, folder
                )
            
            elif self.current_provider == 'imap':
                return await self._search_emails_imap(
                    search_query, search_from, search_to, search_subject,
                    search_body, date_from, date_to, has_attachments,
                    is_unread, max_results, folder
                )
            
            else:
                return self._error_result("Provider non supportato per search")
                
        except Exception as e:
            return self._error_result(f"Errore ricerca Gmail: {e}")
    
    async def _search_emails_imap(self, search_query: str, search_from: str,
                                search_to: str, search_subject: str, search_body: str,
                                date_from: str, date_to: str, has_attachments: bool,
                                is_unread: bool, max_results: int, folder: str) -> Dict[str, Any]:
        """Ricerca avanzata email IMAP."""
        try:
            # Seleziona cartella
            self.imap_connection.select(folder)
            
            # Costruisci criteri ricerca IMAP
            criteria = []
            
            if search_from:
                criteria.append(f'FROM "{search_from}"')
            
            if search_to:
                criteria.append(f'TO "{search_to}"')
            
            if search_subject:
                criteria.append(f'SUBJECT "{search_subject}"')
            
            if search_body:
                criteria.append(f'BODY "{search_body}"')
            
            if date_from:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                criteria.append(f'SINCE {date_obj.strftime("%d-%b-%Y")}')
            
            if date_to:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                criteria.append(f'BEFORE {date_obj.strftime("%d-%b-%Y")}')
            
            if is_unread:
                criteria.append('UNSEEN')
            
            # Se nessun criterio specifico, cerca tutto
            if not criteria:
                if search_query:
                    criteria.append(f'TEXT "{search_query}"')
                else:
                    criteria.append('ALL')
            
            # Esegui ricerca
            search_criteria = '(' + ' '.join(criteria) + ')' if len(criteria) > 1 else criteria[0]
            typ, data = self.imap_connection.search(None, search_criteria)
            
            if typ != 'OK':
                return self._error_result("Errore ricerca IMAP")
            
            # Recupera email IDs
            email_ids = data[0].split()
            email_ids = email_ids[-max_results:] if len(email_ids) > max_results else email_ids
            
            emails = []
            for email_id in email_ids:
                try:
                    email_detail = await self._get_imap_email_detail(
                        email_id, True, False  # Include body, non HTML
                    )
                    if email_detail:
                        # Filtro allegati se richiesto
                        if has_attachments and not email_detail.get('attachments'):
                            continue
                        emails.append(email_detail)
                except Exception as e:
                    logger.warning(f"Errore recupero email ricerca IMAP {email_id}: {e}")
                    continue
            
            return self._success_result(
                f"Trovate {len(emails)} email corrispondenti alla ricerca",
                {
                    'emails': emails,
                    'email_count': len(emails),
                    'criteria_used': search_criteria,
                    'total_results': len(data[0].split()) if data[0] else 0
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore ricerca IMAP: {e}")
    
    async def _mark_emails_gmail(self, email_ids: List[str], mark_as_read: bool) -> Dict[str, Any]:
        """Marca email Gmail come lette/non lette."""
        try:
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                try:
                    if mark_as_read:
                        # Rimuovi label UNREAD
                        self.gmail_service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                    else:
                        # Aggiungi label UNREAD
                        self.gmail_service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'addLabelIds': ['UNREAD']}
                        ).execute()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Errore modifica Gmail {email_id}: {e}")
                    failed_count += 1
            
            status = "lette" if mark_as_read else "non lette"
            return self._success_result(
                f"Marcate {success_count} email come {status} ({failed_count} errori)",
                {
                    'processed_count': success_count,
                    'failed_count': failed_count,
                    'mark_as_read': mark_as_read
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore modifica email Gmail: {e}")
    
    async def _mark_emails_imap(self, email_ids: List[str], mark_as_read: bool) -> Dict[str, Any]:
        """Marca email IMAP come lette/non lette."""
        try:
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                try:
                    if mark_as_read:
                        # Aggiungi flag \\Seen
                        self.imap_connection.store(email_id, '+FLAGS', '\\\\Seen')
                    else:
                        # Rimuovi flag \\Seen
                        self.imap_connection.store(email_id, '-FLAGS', '\\\\Seen')
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Errore modifica IMAP {email_id}: {e}")
                    failed_count += 1
            
            status = "lette" if mark_as_read else "non lette"
            return self._success_result(
                f"Marcate {success_count} email come {status} ({failed_count} errori)",
                {
                    'processed_count': success_count,
                    'failed_count': failed_count,
                    'mark_as_read': mark_as_read
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore modifica email IMAP: {e}")
    
    async def _download_gmail_attachments(self, email_id: str, save_path: str,
                                        attachment_filter: List[str], max_size_mb: int) -> Dict[str, Any]:
        """Download allegati Gmail."""
        try:
            attachments_info = await self._get_gmail_attachments_detail(email_id)
            downloaded = []
            skipped = []
            
            for attachment in attachments_info:
                filename = attachment['filename']
                attachment_id = attachment['attachment_id']
                size_mb = attachment['size'] / (1024 * 1024)
                
                # Controlli filtri
                if attachment_filter and not any(f in filename.lower() for f in attachment_filter):
                    skipped.append({'filename': filename, 'reason': 'filtered'})
                    continue
                
                if size_mb > max_size_mb:
                    skipped.append({'filename': filename, 'reason': 'too_large', 'size_mb': size_mb})
                    continue
                
                try:
                    # Download allegato
                    attachment_data = self.gmail_service.users().messages().attachments().get(
                        userId='me',
                        messageId=email_id,
                        id=attachment_id
                    ).execute()
                    
                    # Decodifica e salva
                    file_data = base64.urlsafe_b64decode(attachment_data['data'])
                    file_path = Path(save_path) / filename
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    downloaded.append({
                        'filename': filename,
                        'file_path': str(file_path),
                        'size': len(file_data),
                        'content_type': attachment['content_type']
                    })
                    
                except Exception as e:
                    skipped.append({'filename': filename, 'reason': 'download_error', 'error': str(e)})
            
            return self._success_result(
                f"Scaricati {len(downloaded)} allegati, saltati {len(skipped)}",
                {
                    'downloaded_attachments': downloaded,
                    'skipped_attachments': skipped,
                    'download_path': save_path
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore download allegati Gmail: {e}")
    
    async def _download_imap_attachments(self, email_id: str, save_path: str,
                                       attachment_filter: List[str], max_size_mb: int) -> Dict[str, Any]:
        """Download allegati IMAP."""
        try:
            # Recupera email completa
            typ, data = self.imap_connection.fetch(email_id.encode(), '(RFC822)')
            if typ != 'OK':
                return self._error_result("Errore recupero email IMAP")
            
            email_message = email.message_from_bytes(data[0][1])
            downloaded = []
            skipped = []
            
            def _download_parts(part):
                if part.get_filename():
                    filename = part.get_filename()
                    content = part.get_payload(decode=True)
                    size_mb = len(content) / (1024 * 1024) if content else 0
                    
                    # Controlli filtri
                    if attachment_filter and not any(f in filename.lower() for f in attachment_filter):
                        skipped.append({'filename': filename, 'reason': 'filtered'})
                        return
                    
                    if size_mb > max_size_mb:
                        skipped.append({'filename': filename, 'reason': 'too_large', 'size_mb': size_mb})
                        return
                    
                    try:
                        # Salva allegato
                        file_path = Path(save_path) / filename
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        downloaded.append({
                            'filename': filename,
                            'file_path': str(file_path),
                            'size': len(content),
                            'content_type': part.get_content_type()
                        })
                        
                    except Exception as e:
                        skipped.append({'filename': filename, 'reason': 'save_error', 'error': str(e)})
            
            # Processa tutte le parti email
            if email_message.is_multipart():
                for part in email_message.walk():
                    _download_parts(part)
            else:
                _download_parts(email_message)
            
            return self._success_result(
                f"Scaricati {len(downloaded)} allegati, saltati {len(skipped)}",
                {
                    'downloaded_attachments': downloaded,
                    'skipped_attachments': skipped,
                    'download_path': save_path
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore download allegati IMAP: {e}")
    
    async def _manage_labels(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Gestisce etichette Gmail."""
        try:
            if self.current_provider != 'gmail':
                return self._error_result("Gestione etichette disponibile solo per Gmail")
            
            email_ids = inputs.get('email_ids', [])
            if isinstance(email_ids, str):
                email_ids = [email_ids]
            
            if not email_ids:
                email_id = inputs.get('email_id')
                if email_id:
                    email_ids = [email_id]
            
            if not email_ids:
                return self._error_result("email_id o email_ids richiesti")
            
            add_labels = inputs.get('add_labels', [])
            remove_labels = inputs.get('remove_labels', [])
            
            if not add_labels and not remove_labels:
                return self._error_result("Specificare add_labels o remove_labels")
            
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                try:
                    body = {}
                    if add_labels:
                        body['addLabelIds'] = add_labels
                    if remove_labels:
                        body['removeLabelIds'] = remove_labels
                    
                    self.gmail_service.users().messages().modify(
                        userId='me',
                        id=email_id,
                        body=body
                    ).execute()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Errore modifica etichette Gmail {email_id}: {e}")
                    failed_count += 1
            
            return self._success_result(
                f"Modificate etichette per {success_count} email ({failed_count} errori)",
                {
                    'processed_count': success_count,
                    'failed_count': failed_count,
                    'added_labels': add_labels,
                    'removed_labels': remove_labels
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore gestione etichette: {e}")
    
    async def _move_email(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Sposta email tra cartelle."""
        try:
            email_ids = inputs.get('email_ids', [])
            if isinstance(email_ids, str):
                email_ids = [email_ids]
            
            if not email_ids:
                email_id = inputs.get('email_id')
                if email_id:
                    email_ids = [email_id]
            
            if not email_ids:
                return self._error_result("email_id o email_ids richiesti")
            
            destination_folder = inputs.get('destination_folder')
            if not destination_folder:
                return self._error_result("destination_folder richiesta")
            
            if self.current_provider == 'gmail':
                # Gmail usa etichette invece di cartelle
                return await self._move_emails_gmail(email_ids, destination_folder)
            
            elif self.current_provider == 'imap':
                return await self._move_emails_imap(email_ids, destination_folder)
            
            else:
                return self._error_result("Provider non supportato per move_email")
                
        except Exception as e:
            return self._error_result(f"Errore spostamento email: {e}")
    
    async def _move_emails_gmail(self, email_ids: List[str], destination_folder: str) -> Dict[str, Any]:
        """Sposta email Gmail (gestione etichette)."""
        try:
            success_count = 0
            failed_count = 0
            
            # Mappatura cartelle comuni -> etichette Gmail
            folder_mapping = {
                'trash': 'TRASH',
                'spam': 'SPAM',
                'archive': '',  # Rimuove INBOX
                'important': 'IMPORTANT',
                'inbox': 'INBOX'
            }
            
            gmail_label = folder_mapping.get(destination_folder.lower(), destination_folder.upper())
            
            for email_id in email_ids:
                try:
                    if destination_folder.lower() == 'archive':
                        # Archivia (rimuovi INBOX)
                        self.gmail_service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'removeLabelIds': ['INBOX']}
                        ).execute()
                    else:
                        # Sposta a nuova etichetta
                        self.gmail_service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'addLabelIds': [gmail_label]}
                        ).execute()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Errore spostamento Gmail {email_id}: {e}")
                    failed_count += 1
            
            return self._success_result(
                f"Spostate {success_count} email in {destination_folder} ({failed_count} errori)",
                {
                    'processed_count': success_count,
                    'failed_count': failed_count,
                    'destination_folder': destination_folder
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore spostamento Gmail: {e}")
    
    async def _move_emails_imap(self, email_ids: List[str], destination_folder: str) -> Dict[str, Any]:
        """Sposta email IMAP."""
        try:
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                try:
                    # Copia email nella destinazione
                    self.imap_connection.copy(email_id, destination_folder)
                    
                    # Marca come eliminata nella cartella originale
                    self.imap_connection.store(email_id, '+FLAGS', '\\\\Deleted')
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Errore spostamento IMAP {email_id}: {e}")
                    failed_count += 1
            
            # Espunge email marcate come eliminate
            try:
                self.imap_connection.expunge()
            except Exception as e:
                logger.warning(f"Errore expunge IMAP: {e}")
            
            return self._success_result(
                f"Spostate {success_count} email in {destination_folder} ({failed_count} errori)",
                {
                    'processed_count': success_count,
                    'failed_count': failed_count,
                    'destination_folder': destination_folder
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore spostamento IMAP: {e}")
    
    async def _get_email_stats(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Ottiene statistiche email."""
        try:
            folder = inputs.get('folder', 'INBOX')
            date_range_days = inputs.get('date_range_days', 30)
            
            if self.current_provider == 'gmail':
                return await self._get_gmail_stats(folder, date_range_days)
            
            elif self.current_provider == 'imap':
                return await self._get_imap_stats(folder, date_range_days)
            
            else:
                return self._error_result("Provider non supportato per get_stats")
                
        except Exception as e:
            return self._error_result(f"Errore statistiche: {e}")
    
    async def _get_gmail_stats(self, folder: str, date_range_days: int) -> Dict[str, Any]:
        """Statistiche Gmail."""
        try:
            # Data limite
            date_limit = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y/%m/%d')
            
            # Query per statistiche
            queries = {
                'total_recent': f'after:{date_limit}',
                'unread_recent': f'is:unread after:{date_limit}',
                'with_attachments': f'has:attachment after:{date_limit}',
                'important': f'is:important after:{date_limit}'
            }
            
            stats = {}
            
            for stat_name, query in queries.items():
                try:
                    result = self.gmail_service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=1  # Solo per conteggio
                    ).execute()
                    
                    stats[stat_name] = result.get('resultSizeEstimate', 0)
                    
                except Exception as e:
                    logger.warning(f"Errore stat Gmail {stat_name}: {e}")
                    stats[stat_name] = 0
            
            # Info profilo
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            
            return self._success_result(
                "Statistiche Gmail recuperate",
                {
                    'stats': {
                        'total_messages': profile.get('messagesTotal', 0),
                        'total_threads': profile.get('threadsTotal', 0),
                        'recent_period_days': date_range_days,
                        **stats
                    },
                    'account_info': {
                        'email': profile.get('emailAddress'),
                        'quota_usage': {
                            'messages': profile.get('messagesTotal', 0),
                            'threads': profile.get('threadsTotal', 0)
                        }
                    }
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore statistiche Gmail: {e}")
    
    async def _get_imap_stats(self, folder: str, date_range_days: int) -> Dict[str, Any]:
        """Statistiche IMAP."""
        try:
            # Seleziona cartella
            self.imap_connection.select(folder)
            
            # Conta totali
            typ, data = self.imap_connection.search(None, 'ALL')
            total_count = len(data[0].split()) if data[0] else 0
            
            # Conta non lette
            typ, data = self.imap_connection.search(None, 'UNSEEN')
            unread_count = len(data[0].split()) if data[0] else 0
            
            # Conta recenti (ultimi N giorni)
            date_limit = (datetime.now() - timedelta(days=date_range_days)).strftime('%d-%b-%Y')
            typ, data = self.imap_connection.search(None, f'SINCE {date_limit}')
            recent_count = len(data[0].split()) if data[0] else 0
            
            return self._success_result(
                "Statistiche IMAP recuperate",
                {
                    'stats': {
                        'total_messages': total_count,
                        'unread_messages': unread_count,
                        'recent_messages': recent_count,
                        'recent_period_days': date_range_days,
                        'folder': folder
                    }
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore statistiche IMAP: {e}")
    
    async def _get_attachments(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Scarica allegati da email."""
        try:
            email_id = inputs.get('email_id')
            if not email_id:
                return self._error_result("email_id richiesto per download allegati")
            
            save_path = inputs.get('save_path', './downloads')
            attachment_filter = inputs.get('attachment_filter', [])  # Filtro per nomi file
            max_size_mb = inputs.get('max_size_mb', 25)  # Limite dimensione
            
            # Crea directory se non esiste
            os.makedirs(save_path, exist_ok=True)
            
            if self.current_provider == 'gmail':
                return await self._download_gmail_attachments(
                    email_id, save_path, attachment_filter, max_size_mb
                )
            
            elif self.current_provider == 'imap':
                return await self._download_imap_attachments(
                    email_id, save_path, attachment_filter, max_size_mb
                )
            
            else:
                return self._error_result("Provider non supportato per get_attachments")
                
        except Exception as e:
            return self._error_result(f"Errore download allegati: {e}")
    
    async def _mark_as_read(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Marca email come letta/non letta."""
        try:
            email_ids = inputs.get('email_ids', [])
            if isinstance(email_ids, str):
                email_ids = [email_ids]
            
            if not email_ids:
                email_id = inputs.get('email_id')
                if email_id:
                    email_ids = [email_id]
            
            if not email_ids:
                return self._error_result("email_id o email_ids richiesti")
            
            mark_as_read = inputs.get('mark_as_read', True)  # True=letto, False=non letto
            
            if self.current_provider == 'gmail':
                return await self._mark_emails_gmail(email_ids, mark_as_read)
            
            elif self.current_provider == 'imap':
                return await self._mark_emails_imap(email_ids, mark_as_read)
            
            else:
                return self._error_result("Provider non supportato per mark_read")
                
        except Exception as e:
            return self._error_result(f"Errore modifica stato email: {e}")
    
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