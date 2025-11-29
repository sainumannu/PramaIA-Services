"""
Email Reader Processor - Gestione avanzata lettura email multi-provider.

Supporta Gmail, Outlook, e provider IMAP generici con:
- Autenticazione OAuth2 e password
- Lettura email con filtri avanzati
- Download allegati automatico
- Ricerca semantica
- Gestione cartelle
- Invio email SMTP
"""

import os
import sys
import json
import base64
import email
import imaplib
import smtplib
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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

# Microsoft Graph API per Exchange OAuth2
try:
    import msal
    import requests
    MICROSOFT_GRAPH_AVAILABLE = True
except ImportError:
    MICROSOFT_GRAPH_AVAILABLE = False

try:
    import ssl
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

# Configurazione logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazioni Exchange/Office 365
EXCHANGE_CONFIGS = {
    'office365': {
        'imap_server': 'outlook.office365.com',
        'imap_port': 993,
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'graph_endpoint': 'https://graph.microsoft.com/v1.0',
        'authority': 'https://login.microsoftonline.com',
        'scopes': ['https://graph.microsoft.com/Mail.Read',
                  'https://graph.microsoft.com/Mail.Send',
                  'https://graph.microsoft.com/Mail.ReadWrite']
    },
    'exchange_onprem': {
        'imap_server': None,  # Da configurare
        'imap_port': 993,
        'smtp_server': None,  # Da configurare  
        'smtp_port': 587,
        'ews_url': None  # Da configurare
    }
}

class EmailProcessor:
    """Processore per lettura email multi-provider con supporto Exchange."""
    
    def __init__(self):
        """Inizializza il processore email."""
        self.gmail_service = None
        self.outlook_account = None
        self.imap_connection = None
        self.microsoft_app = None  # MSAL app per OAuth2
        self.access_token = None   # Token Microsoft Graph
        self.current_provider = None
        logger.info("EmailProcessor inizializzato con supporto Exchange")
    
    async def authenticate_exchange_oauth2(self, client_id: str, tenant_id: str, 
                                         client_secret: Optional[str] = None,
                                         username: Optional[str] = None,
                                         password: Optional[str] = None,
                                         use_device_flow: bool = False):
        """Autentica con Exchange/Office 365 usando OAuth2 e Microsoft Graph.
        
        Args:
            client_id: ID dell'applicazione Azure AD
            tenant_id: ID del tenant Azure AD
            client_secret: Secret dell'applicazione (per confidential client)
            username: Username per Resource Owner Password Credential flow
            password: Password per ROPC flow
            use_device_flow: Se usare device code flow per interactive auth
            
        Returns:
            bool: True se autenticazione riuscita
        """
        if not MICROSOFT_GRAPH_AVAILABLE:
            logger.error("Microsoft Graph (msal) non disponibile")
            return False
            
        try:
            authority_url = f"{EXCHANGE_CONFIGS['office365']['authority']}/{tenant_id}"
            
            if client_secret:
                # Confidential client application (con secret)
                self.microsoft_app = msal.ConfidentialClientApplication(
                    client_id=client_id,
                    client_credential=client_secret,
                    authority=authority_url
                )
                
                # Prova prima silent acquisition (token cache)
                accounts = self.microsoft_app.get_accounts()
                if accounts:
                    result = self.microsoft_app.acquire_token_silent(
                        EXCHANGE_CONFIGS['office365']['scopes'],
                        account=accounts[0]
                    )
                else:
                    result = None
                
                # Se non c'è token cached, usa client credentials flow
                if not result:
                    result = self.microsoft_app.acquire_token_for_client(
                        scopes=EXCHANGE_CONFIGS['office365']['scopes']
                    )
                    
            elif username and password:
                # Public client con Resource Owner Password Credentials
                self.microsoft_app = msal.PublicClientApplication(
                    client_id=client_id,
                    authority=authority_url
                )
                
                result = self.microsoft_app.acquire_token_by_username_password(
                    username=username,
                    password=password,
                    scopes=EXCHANGE_CONFIGS['office365']['scopes']
                )
                
            elif use_device_flow:
                # Device code flow per autenticazione interattiva
                self.microsoft_app = msal.PublicClientApplication(
                    client_id=client_id,
                    authority=authority_url
                )
                
                flow = self.microsoft_app.initiate_device_flow(
                    scopes=EXCHANGE_CONFIGS['office365']['scopes']
                )
                
                if "user_code" not in flow:
                    raise Exception("Device flow non riuscito")
                    
                logger.info(f"Device Code: {flow['message']}")
                print(f"\n{flow['message']}")
                
                result = self.microsoft_app.acquire_token_by_device_flow(flow)
                
            else:
                logger.error("Parametri di autenticazione insufficienti")
                return False
                
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.current_provider = "exchange"
                logger.info("Autenticazione Exchange OAuth2 riuscita")
                return True
            else:
                logger.error(f"Errore autenticazione Exchange: {result.get('error_description', result)}")
                return False
                
        except Exception as e:
            logger.error(f"Errore durante autenticazione Exchange: {str(e)}")
            return False
    
    def _make_graph_request(self, endpoint: str, method: str = "GET", data: dict = None):
        """Effettua richiesta autenticata a Microsoft Graph API.
        
        Args:
            endpoint: Endpoint Graph API (relativo a /v1.0/)
            method: Metodo HTTP (GET, POST, PATCH, DELETE)
            data: Dati per richieste POST/PATCH
            
        Returns:
            dict: Risposta JSON dell'API
        """
        if not self.access_token:
            raise Exception("Token di accesso non disponibile")
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{EXCHANGE_CONFIGS['office365']['graph_endpoint']}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Metodo HTTP non supportato: {method}")
            
        if response.status_code == 401:
            raise Exception("Token di accesso scaduto o non valido")
        elif response.status_code >= 400:
            raise Exception(f"Errore Graph API: {response.status_code} - {response.text}")
            
        return response.json() if response.content else {}
        
    async def authenticate_exchange_imap_smtp(self, email: str, password: str, 
                                           imap_server: str = None, smtp_server: str = None,
                                           imap_port: int = 993, smtp_port: int = 587):
        """Autentica con Exchange usando IMAP/SMTP (fallback).
        
        Args:
            email: Indirizzo email
            password: Password dell'account
            imap_server: Server IMAP personalizzato
            smtp_server: Server SMTP personalizzato  
            imap_port: Porta IMAP (default 993)
            smtp_port: Porta SMTP (default 587)
            
        Returns:
            bool: True se autenticazione riuscita
        """
        try:
            # Usa server Office 365 di default se non specificati
            if not imap_server:
                imap_server = EXCHANGE_CONFIGS['office365']['imap_server']
            if not smtp_server:
                smtp_server = EXCHANGE_CONFIGS['office365']['smtp_server']
                
            # Test connessione IMAP
            self.imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
            self.imap_connection.login(email, password)
            
            # Salva credenziali per SMTP
            self.smtp_email = email
            self.smtp_password = password
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
            
            self.current_provider = "exchange_imap"
            logger.info(f"Autenticazione Exchange IMAP/SMTP riuscita per {email}")
            return True
            
        except Exception as e:
            logger.error(f"Errore autenticazione Exchange IMAP/SMTP: {str(e)}")
            if self.imap_connection:
                try:
                    self.imap_connection.close()
                except:
                    pass
                self.imap_connection = None
            return False
    
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
                'get_stats': self._get_email_stats,
                'send_email': self._send_email
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
            elif self.current_provider == 'exchange':
                return await self._list_emails_exchange(
                    folder, max_emails, unread_only, date_from, date_to,
                    sender_filter, subject_filter, include_body, include_html
                )
            elif self.current_provider == 'exchange_imap':
                return await self._list_emails_imap(
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
    
    async def _list_emails_exchange(self, folder: str, max_emails: int, unread_only: bool,
                                  date_from: str = None, date_to: str = None, 
                                  sender_filter: str = None, subject_filter: str = None,
                                  include_body: bool = True, include_html: bool = False) -> Dict[str, Any]:
        """Lista email usando Microsoft Graph API.
        
        Args:
            folder: Nome cartella (default 'INBOX')
            max_emails: Numero massimo email da recuperare
            unread_only: Solo email non lette
            date_from: Data minima (YYYY-MM-DD)
            date_to: Data massima (YYYY-MM-DD)
            sender_filter: Filtra per mittente
            subject_filter: Filtra per oggetto
            include_body: Include corpo email
            include_html: Include corpo HTML
            
        Returns:
            Dict con risultato operazione
        """
        try:
            # Costruisci endpoint Graph API per messaggi
            if folder.upper() == 'INBOX':
                endpoint = "me/messages"
            else:
                # Per cartelle personalizzate, prima cerchiamo l'ID della cartella
                folders_response = self._make_graph_request("me/mailFolders")
                folder_id = None
                for f in folders_response.get('value', []):
                    if f.get('displayName', '').upper() == folder.upper():
                        folder_id = f.get('id')
                        break
                
                if not folder_id:
                    return self._error_result(f"Cartella '{folder}' non trovata")
                    
                endpoint = f"me/mailFolders/{folder_id}/messages"
            
            # Parametri query
            params = []
            
            # Limita risultati
            params.append(f"$top={min(max_emails, 1000)}")
            
            # Ordinamento per data (più recenti prima)
            params.append("$orderby=receivedDateTime desc")
            
            # Filtro per email non lette
            filters = []
            if unread_only:
                filters.append("isRead eq false")
            
            # Filtro per date
            if date_from:
                try:
                    date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    filters.append(f"receivedDateTime ge {date_obj.strftime('%Y-%m-%d')}T00:00:00Z")
                except ValueError:
                    pass
                    
            if date_to:
                try:
                    date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                    filters.append(f"receivedDateTime le {date_obj.strftime('%Y-%m-%d')}T23:59:59Z")
                except ValueError:
                    pass
            
            # Filtro per mittente
            if sender_filter:
                filters.append(f"from/emailAddress/address eq '{sender_filter}'")
            
            # Filtro per oggetto (contiene)
            if subject_filter:
                filters.append(f"contains(subject,'{subject_filter}')")
            
            # Aggiungi filtri alla query
            if filters:
                params.append(f"$filter={' and '.join(filters)}")
            
            # Seleziona campi necessari
            select_fields = [
                'id', 'subject', 'from', 'toRecipients', 'ccRecipients', 
                'receivedDateTime', 'isRead', 'importance', 'hasAttachments'
            ]
            
            if include_body or include_html:
                select_fields.append('body')
            
            params.append(f"$select={','.join(select_fields)}")
            
            # Esegui richiesta
            full_endpoint = f"{endpoint}?" + "&".join(params)
            response = self._make_graph_request(full_endpoint)
            
            # Processa risultati
            emails = []
            for msg in response.get('value', []):
                email_data = self._parse_exchange_email(msg, include_body, include_html)
                if email_data:
                    emails.append(email_data)
            
            return self._success_result(
                f"Recuperate {len(emails)} email via Exchange Graph API",
                {
                    'emails': emails,
                    'email_count': len(emails),
                    'total_available': len(response.get('value', []))
                }
            )
            
        except Exception as e:
            return self._error_result(f"Errore Exchange Graph API list: {e}")
    
    def _parse_exchange_email(self, msg: dict, include_body: bool, include_html: bool) -> Dict[str, Any]:
        """Converte messaggio Exchange Graph API in formato standardizzato.
        
        Args:
            msg: Messaggio raw da Graph API
            include_body: Include corpo email
            include_html: Include corpo HTML
            
        Returns:
            Dict con dati email formattati
        """
        try:
            # Estrai mittente
            from_data = msg.get('from', {}).get('emailAddress', {})
            sender = from_data.get('address', 'sconosciuto')
            sender_name = from_data.get('name', sender)
            
            # Estrai destinatari
            recipients = []
            for recipient in msg.get('toRecipients', []):
                email_addr = recipient.get('emailAddress', {})
                recipients.append({
                    'email': email_addr.get('address', ''),
                    'name': email_addr.get('name', email_addr.get('address', ''))
                })
            
            # Estrai CC
            cc_recipients = []
            for recipient in msg.get('ccRecipients', []):
                email_addr = recipient.get('emailAddress', {})
                cc_recipients.append({
                    'email': email_addr.get('address', ''),
                    'name': email_addr.get('name', email_addr.get('address', ''))
                })
            
            # Data ricezione
            received_date = msg.get('receivedDateTime', '')
            if received_date:
                try:
                    # Converte da formato ISO a timestamp
                    date_obj = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                    received_timestamp = int(date_obj.timestamp() * 1000)
                except:
                    received_timestamp = 0
            else:
                received_timestamp = 0
            
            # Corpo email
            body_text = ""
            body_html = ""
            if include_body or include_html:
                body_data = msg.get('body', {})
                content = body_data.get('content', '')
                content_type = body_data.get('contentType', '').lower()
                
                if content_type == 'html':
                    body_html = content
                    if include_body:
                        # Converte HTML in testo
                        from html import unescape
                        import re
                        text = re.sub('<[^<]+?>', '', content)
                        body_text = unescape(text).strip()
                else:
                    body_text = content
            
            # Costruisci dati email
            email_data = {
                'id': msg.get('id', ''),
                'subject': msg.get('subject', 'Nessun oggetto'),
                'sender': sender,
                'sender_name': sender_name,
                'recipients': recipients,
                'cc_recipients': cc_recipients,
                'date': received_timestamp,
                'is_read': msg.get('isRead', False),
                'importance': msg.get('importance', 'normal'),
                'has_attachments': msg.get('hasAttachments', False),
                'folder': 'INBOX',  # TODO: determinare cartella effettiva
                'provider': 'exchange'
            }
            
            if include_body:
                email_data['body'] = body_text
            if include_html:
                email_data['body_html'] = body_html
            
            return email_data
            
        except Exception as e:
            logger.warning(f"Errore parsing email Exchange: {e}")
            return None
    
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

    # ===============================
    # OPERAZIONE: SEND EMAIL
    # ===============================
    
    async def _send_email(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invia email tramite SMTP.
        
        Parametri inputs:
        - to: destinatario (str) o lista destinatari
        - cc: destinatari in copia (optional)
        - bcc: destinatari in copia nascosta (optional)  
        - subject: oggetto email
        - body: corpo email (testo)
        - body_html: corpo email HTML (optional)
        - attachments: lista file da allegare (optional)
        - smtp_server: server SMTP (default gmail)
        - smtp_port: porta SMTP (default 587)
        - smtp_username: username SMTP 
        - smtp_password: password SMTP (App Password)
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Validazione parametri obbligatori
            required_params = ['to', 'subject', 'body']
            for param in required_params:
                if not inputs.get(param):
                    return self._error_result(f"Parametro obbligatorio mancante: {param}")
            
            # Configurazione SMTP
            smtp_config = self._get_smtp_config(inputs)
            if not smtp_config['success']:
                return smtp_config
            
            # Creazione messaggio
            msg_result = self._create_email_message(inputs)
            if not msg_result['success']:
                return msg_result
                
            message = msg_result['message']
            
            # Invio email
            send_result = await self._send_via_smtp(message, smtp_config['config'])
            
            if send_result['success']:
                logger.info(f"Email inviata con successo a: {inputs['to']}")
                return self._success_result("Email inviata con successo", {
                    'sent_to': inputs['to'],
                    'subject': inputs['subject'],
                    'message_id': send_result.get('message_id'),
                    'sent_at': datetime.now().isoformat(),
                    'smtp_server': smtp_config['config']['server'],
                    'attachments_count': len(inputs.get('attachments', []))
                })
            else:
                return send_result
                
        except Exception as e:
            logger.error(f"Errore invio email: {str(e)}")
            return self._error_result(f"Errore invio email: {str(e)}")
    
    def _get_smtp_config(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Ottiene configurazione SMTP."""
        try:
            # SMTP Gmail di default
            smtp_server = inputs.get('smtp_server', 'smtp.gmail.com')
            smtp_port = inputs.get('smtp_port', 587)
            
            # Credenziali
            smtp_username = inputs.get('smtp_username') or inputs.get('username')
            smtp_password = inputs.get('smtp_password') or inputs.get('password') or inputs.get('app_password')
            
            if not smtp_username or not smtp_password:
                return self._error_result("Credenziali SMTP mancanti: smtp_username e smtp_password richiesti")
            
            return {
                'success': True,
                'config': {
                    'server': smtp_server,
                    'port': smtp_port,
                    'username': smtp_username,
                    'password': smtp_password,
                    'use_tls': inputs.get('use_tls', True)
                }
            }
            
        except Exception as e:
            return self._error_result(f"Errore configurazione SMTP: {str(e)}")
    
    def _create_email_message(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Crea messaggio email con allegati."""
        try:
            # Destinatari
            to_addresses = self._normalize_addresses(inputs['to'])
            cc_addresses = self._normalize_addresses(inputs.get('cc', []))
            bcc_addresses = self._normalize_addresses(inputs.get('bcc', []))
            
            # Creazione messaggio
            if inputs.get('body_html') or inputs.get('attachments'):
                message = MIMEMultipart('alternative' if inputs.get('body_html') else 'mixed')
            else:
                message = MIMEText(inputs['body'], 'plain', 'utf-8')
                message['To'] = ', '.join(to_addresses)
                message['Subject'] = inputs['subject']
                if cc_addresses:
                    message['Cc'] = ', '.join(cc_addresses)
                return {'success': True, 'message': message}
            
            # Headers
            message['To'] = ', '.join(to_addresses)
            message['Subject'] = inputs['subject']
            if cc_addresses:
                message['Cc'] = ', '.join(cc_addresses)
            
            # Corpo testo
            text_part = MIMEText(inputs['body'], 'plain', 'utf-8')
            message.attach(text_part)
            
            # Corpo HTML (se presente)
            if inputs.get('body_html'):
                html_part = MIMEText(inputs['body_html'], 'html', 'utf-8')
                message.attach(html_part)
            
            # Allegati
            if inputs.get('attachments'):
                attach_result = self._add_attachments(message, inputs['attachments'])
                if not attach_result['success']:
                    return attach_result
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            return self._error_result(f"Errore creazione messaggio: {str(e)}")
    
    def _normalize_addresses(self, addresses) -> List[str]:
        """Normalizza indirizzi email."""
        if isinstance(addresses, str):
            return [addr.strip() for addr in addresses.split(',')]
        elif isinstance(addresses, list):
            return [str(addr).strip() for addr in addresses]
        return []
    
    def _add_attachments(self, message: MIMEMultipart, attachments: List[str]) -> Dict[str, Any]:
        """Aggiunge allegati al messaggio."""
        try:
            attached_files = []
            
            for file_path in attachments:
                if not os.path.exists(file_path):
                    return self._error_result(f"File allegato non trovato: {file_path}")
                
                # Leggi file
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Crea allegato
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(file_data)
                encoders.encode_base64(attachment)
                
                # Headers
                filename = os.path.basename(file_path)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                
                message.attach(attachment)
                attached_files.append(filename)
            
            return {'success': True, 'attached_files': attached_files}
            
        except Exception as e:
            return self._error_result(f"Errore allegati: {str(e)}")
    
    async def _send_via_smtp(self, message: MIMEText, smtp_config: Dict[str, Any]) -> Dict[str, Any]:
        """Invia email via SMTP."""
        logger = logging.getLogger(__name__)
        
        try:
            # Connessione SMTP
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            
            if smtp_config.get('use_tls', True):
                server.starttls()
            
            # Login
            server.login(smtp_config['username'], smtp_config['password'])
            
            # Invio
            from_addr = smtp_config['username']
            to_addrs = []
            
            # Raccogli tutti i destinatari
            if message['To']:
                to_addrs.extend(self._normalize_addresses(message['To']))
            if message['Cc']:
                to_addrs.extend(self._normalize_addresses(message['Cc']))
            if message['Bcc']:
                to_addrs.extend(self._normalize_addresses(message['Bcc']))
            
            # Headers mittente
            message['From'] = from_addr
            message['Date'] = email.utils.formatdate(localtime=True)
            message['Message-ID'] = email.utils.make_msgid()
            
            # Invio messaggio
            text = message.as_string()
            server.sendmail(from_addr, to_addrs, text)
            server.quit()
            
            logger.info(f"Email inviata via SMTP a {len(to_addrs)} destinatari")
            
            return {
                'success': True,
                'message_id': message['Message-ID'],
                'recipients_count': len(to_addrs),
                'smtp_server': smtp_config['server']
            }
            
        except Exception as e:
            logger.error(f"Errore SMTP: {str(e)}")
            return self._error_result(f"Errore SMTP: {str(e)}")

    # ===============================
    # METODI HELPER
    # ===============================