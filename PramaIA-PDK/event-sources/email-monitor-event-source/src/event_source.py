import asyncio
import imaplib
import poplib
import email
import email.utils
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import json
import hashlib
from pathlib import Path

# Aggiungi il path del PDK per importare le utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

try:
    from core.event_source_base import BaseEventSourceProcessor
except ImportError:
    # Fallback per testing locale
    class BaseEventSourceProcessor:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        async def emit_event(self, event_type, data):
            logging.getLogger(__name__).info(f"[EVENT] {event_type}: {json.dumps(data, indent=2)}")
        
        def log_info(self, msg): logging.getLogger(__name__).info(msg)
        def log_warning(self, msg): logging.getLogger(__name__).warning(msg)
        def log_error(self, msg): logging.getLogger(__name__).error(msg)
        def log_debug(self, msg): logging.getLogger(__name__).debug(msg)

    # Adapter logger: prefer local wrapper 'logger', then pramaialog client, otherwise std logging
    try:
        from .logger import debug, info, warning, error, flush, close
    except Exception:
        try:
            from pramaialog import PramaIALogger

            _pramaialogger = PramaIALogger()

            def debug(msg, **kwargs):
                _pramaialogger.debug(msg, **kwargs)

            def info(msg, **kwargs):
                _pramaialogger.info(msg, **kwargs)

            def warning(msg, **kwargs):
                _pramaialogger.warning(msg, **kwargs)

            def error(msg, **kwargs):
                _pramaialogger.error(msg, **kwargs)

            def flush():
                try:
                    _pramaialogger.flush()
                except Exception:
                    pass

            def close():
                try:
                    _pramaialogger.close()
                except Exception:
                    pass

        except Exception:
            import logging as _std_logging

            def debug(msg, **kwargs):
                _std_logging.getLogger(__name__).debug(msg)

            def info(msg, **kwargs):
                _std_logging.getLogger(__name__).info(msg)

            def warning(msg, **kwargs):
                _std_logging.getLogger(__name__).warning(msg)

            def error(msg, **kwargs):
                _std_logging.getLogger(__name__).error(msg)

            def flush():
                return

            def close():
                return

class EmailMonitorEventSource(BaseEventSourceProcessor):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.running = False
        self.monitoring_task = None
        self.processed_emails = set()  # Set di email ID già processate
        self.failed_emails = {}  # Dict di email fallite con retry count
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza l'event source con la configurazione"""
        try:
            self.config = config
            
            # Verifica configurazione connessione
            conn_config = config.get('connection', {})
            if not all(key in conn_config for key in ['server', 'username', 'password']):
                self.log_error("Configurazione connessione incompleta")
                return False
            
            # Crea directory per allegati se necessaria
            att_config = config.get('attachments', {})
            if att_config.get('extract_attachments', True):
                save_path = att_config.get('save_path', './attachments')
                Path(save_path).mkdir(parents=True, exist_ok=True)
                self.log_info(f"Directory allegati: {save_path}")
            
            self.log_info("Email Monitor Event Source inizializzato correttamente")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'inizializzazione: {e}")
            return False
    
    async def start(self) -> bool:
        """Avvia il monitoraggio email"""
        try:
            if self.running:
                return True
            
            self.running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            conn_config = self.config.get('connection', {})
            server = conn_config.get('server')
            protocol = conn_config.get('protocol', 'IMAP')
            
            self.log_info(f"Email monitoring avviato - {protocol} su {server}")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'avvio: {e}")
            return False
    
    async def stop(self) -> bool:
        """Ferma il monitoraggio email"""
        try:
            self.running = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self.log_info("Email monitoring fermato")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante lo stop: {e}")
            return False
    
    async def cleanup(self):
        """Pulizia risorse"""
        await self.stop()
    
    async def _monitoring_loop(self):
        """Loop principale di monitoraggio email"""
        polling_interval = self.config.get('polling_interval', 60)
        
        try:
            while self.running:
                try:
                    await self._check_emails()
                except Exception as e:
                    self.log_error(f"Errore durante il controllo email: {e}")
                    await self._emit_processing_error("email_check", str(e))
                
                # Attendi il prossimo ciclo
                await asyncio.sleep(polling_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log_error(f"Errore critico nel loop di monitoraggio: {e}")
    
    async def _check_emails(self):
        """Controlla nuove email sui server configurati"""
        conn_config = self.config.get('connection', {})
        protocol = conn_config.get('protocol', 'IMAP')
        
        if protocol.upper() == 'IMAP':
            await self._check_imap_emails()
        elif protocol.upper() == 'POP3':
            await self._check_pop3_emails()
        else:
            self.log_error(f"Protocollo non supportato: {protocol}")
    
    async def _check_imap_emails(self):
        """Controlla email via IMAP"""
        conn_config = self.config.get('connection', {})
        server = conn_config.get('server')
        port = conn_config.get('port', 993)
        use_ssl = conn_config.get('use_ssl', True)
        username = conn_config.get('username')
        password = conn_config.get('password')
        
        try:
            # Connessione IMAP
            if use_ssl:
                mail = imaplib.IMAP4_SSL(server, port)
            else:
                mail = imaplib.IMAP4(server, port)
            
            mail.login(username, password)
            
            # Controlla ogni cartella configurata
            folders = self.config.get('folders', ['INBOX'])
            for folder in folders:
                try:
                    await self._process_imap_folder(mail, folder)
                except Exception as e:
                    self.log_error(f"Errore processando cartella {folder}: {e}")
            
            mail.logout()
            
        except Exception as e:
            self.log_error(f"Errore connessione IMAP: {e}")
            await self._emit_processing_error("imap_connection", str(e))
    
    async def _process_imap_folder(self, mail, folder: str):
        """Processa email in una cartella IMAP"""
        try:
            status, messages = mail.select(folder)
            if status != 'OK':
                self.log_warning(f"Impossibile selezionare cartella {folder}")
                return
            
            # Cerca email non lette o recenti
            search_criteria = self._build_search_criteria()
            status, message_ids = mail.search(None, search_criteria)
            
            if status != 'OK':
                return
            
            message_list = message_ids[0].split()
            max_emails = self.config.get('processing', {}).get('max_emails_per_check', 50)
            
            # Limita il numero di email per ciclo
            if len(message_list) > max_emails:
                message_list = message_list[-max_emails:]  # Prende le più recenti
            
            self.log_debug(f"Trovate {len(message_list)} email in {folder}")
            
            # Processa email in gruppi per concorrenza
            concurrent_limit = self.config.get('processing', {}).get('concurrent_processing', 3)
            
            for i in range(0, len(message_list), concurrent_limit):
                batch = message_list[i:i + concurrent_limit]
                tasks = []
                
                for msg_id in batch:
                    task = self._process_single_email(mail, msg_id.decode(), folder)
                    tasks.append(task)
                
                # Esegui batch in parallelo
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            self.log_error(f"Errore processando cartella IMAP {folder}: {e}")
    
    def _build_search_criteria(self) -> str:
        """Costruisce criteri di ricerca IMAP basati sui filtri"""
        criteria = []
        
        filters = self.config.get('filters', {})
        
        # Filtro età
        max_age_days = filters.get('max_age_days', 7)
        if max_age_days > 0:
            since_date = (datetime.now() - timedelta(days=max_age_days)).strftime('%d-%b-%Y')
            criteria.append(f'SINCE {since_date}')
        
        # Altri criteri potrebbero essere aggiunti qui
        
        if not criteria:
            criteria.append('UNSEEN')  # Default: solo non lette
        
        return ' '.join(criteria)
    
    async def _process_single_email(self, mail, msg_id: str, folder: str):
        """Processa una singola email"""
        try:
            # Evita di processare email già elaborate
            email_key = f"{folder}:{msg_id}"
            if email_key in self.processed_emails:
                return
            
            # Scarica email
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return
            
            # Parsing email
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Verifica filtri
            if not await self._passes_filters(email_message):
                self.processed_emails.add(email_key)
                return
            
            # Estrai dati email
            email_data = await self._extract_email_data(email_message, msg_id, folder)
            
            # Processa allegati se configurato
            attachments_data = []
            att_config = self.config.get('attachments', {})
            if att_config.get('extract_attachments', True):
                attachments_data = await self._extract_attachments(email_message, email_data['email_id'])
            
            email_data['attachments'] = attachments_data
            
            # Emetti evento
            await self.emit_event("email_received", email_data)
            
            # Marca come processata
            self.processed_emails.add(email_key)
            
            # Post-processing (marca come letta, sposta, etc.)
            await self._post_process_email(mail, msg_id, email_message)
            
            self.log_info(f"Email processata: {email_data['subject'][:50]}...")
            
        except Exception as e:
            self.log_error(f"Errore processando email {msg_id}: {e}")
            await self._emit_processing_error("email_processing", str(e), msg_id)
    
    async def _passes_filters(self, email_message) -> bool:
        """Verifica se l'email passa i filtri configurati"""
        filters = self.config.get('filters', {})
        
        try:
            # Filtro mittente whitelist
            sender_whitelist = filters.get('sender_whitelist', [])
            if sender_whitelist:
                sender = email_message.get('From', '').lower()
                if not any(allowed.lower() in sender for allowed in sender_whitelist):
                    return False
            
            # Filtro mittente blacklist
            sender_blacklist = filters.get('sender_blacklist', [])
            if sender_blacklist:
                sender = email_message.get('From', '').lower()
                if any(blocked.lower() in sender for blocked in sender_blacklist):
                    return False
            
            # Filtro parole chiave oggetto
            subject_keywords = filters.get('subject_keywords', [])
            if subject_keywords:
                subject = email_message.get('Subject', '').lower()
                if not any(keyword.lower() in subject for keyword in subject_keywords):
                    return False
            
            # Filtro regex oggetto
            subject_regex = filters.get('subject_regex', '')
            if subject_regex:
                subject = email_message.get('Subject', '')
                if not re.search(subject_regex, subject):
                    return False
            
            # Filtro allegati
            has_attachments_filter = filters.get('has_attachments', False)
            if has_attachments_filter:
                has_attachments = any(part.get_content_disposition() == 'attachment' 
                                    for part in email_message.walk())
                if not has_attachments:
                    return False
            
            # Filtro età minima
            min_age_minutes = filters.get('min_age_minutes', 2)
            if min_age_minutes > 0:
                date_str = email_message.get('Date', '')
                if date_str:
                    email_date = email.utils.parsedate_to_datetime(date_str)
                    age_minutes = (datetime.now(email_date.tzinfo) - email_date).total_seconds() / 60
                    if age_minutes < min_age_minutes:
                        return False
            
            return True
            
        except Exception as e:
            self.log_warning(f"Errore nella verifica filtri: {e}")
            return False
    
    async def _extract_email_data(self, email_message, msg_id: str, folder: str) -> Dict[str, Any]:
        """Estrae dati strutturati dall'email"""
        # Genera ID univoco
        email_id = str(uuid.uuid4())
        
        # Estrai intestazioni di base
        from_header = email_message.get('From', '')
        to_header = email_message.get('To', '')
        subject_header = email_message.get('Subject', '')
        date_header = email_message.get('Date', '')
        
        # Parsing data e ora
        email_date = email.utils.parsedate_to_datetime(date_header) if date_header else datetime.now()
        
        # Costruisci il payload dell'email
        email_payload = {
            "email_id": email_id,
            "folder": folder,
            "subject": subject_header,
            "from": from_header,
            "to": to_header,
            "date": email_date.isoformat(),
            "raw_content": email_message.as_bytes().decode('utf-8', errors='replace'),
            "headers": dict(email_message.items()),
            "body": await self._extract_email_body(email_message)
        }
        
        return email_payload
    
    async def _extract_email_body(self, email_message) -> str:
        """Estrae il corpo dell'email, gestendo multipart e codifiche"""
        try:
            # Se l'email è multipart, unisci i parti del corpo
            if email_message.is_multipart():
                parts = email_message.get_payload()
                
                # Estrai il corpo da ogni parte, gestendo la codifica
                body = ""
                for part in parts:
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition")
                    
                    # Salta le parti vuote o gli allegati
                    if part.get_content_maintype() == 'multipart' or content_disposition and 'attachment' in content_disposition:
                        continue
                    
                    # Decodifica il contenuto se necessario
                    charset = part.get_content_charset()
                    if charset is None:
                        charset = 'utf-8'  # Default charset
                    
                    try:
                        part_body = part.get_payload(decode=True).decode(charset, errors='replace')
                        body += part_body
                    except Exception as e:
                        self.log_warning(f"Errore decodificando il corpo dell'email: {e}")
                        continue
                
                return body.strip()
            
            else:
                # Email non multipart
                return email_message.get_payload(decode=True).decode('utf-8', errors='replace').strip()
        
        except Exception as e:
            self.log_warning(f"Errore estraendo il corpo dell'email: {e}")
            return ""
    
    async def _extract_email_data(self, email_message, msg_id: str, folder: str) -> Dict[str, Any]:
        """Estrae dati strutturati dall'email"""
        # Genera ID univoco
        email_id = str(uuid.uuid4())
        
        # Estrai intestazioni di base
        subject = email_message.get('Subject', '')
        from_addr = email_message.get('From', '')
        to_addr = email_message.get('To', '')
        date_str = email_message.get('Date', '')
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()
        except Exception:
            parsed_date = datetime.now()
        
        # Estrarre plain text e html
        body_text = ''
        body_html = ''
        for part in email_message.walk():
            content_type = part.get_content_type()
            disp = part.get_content_disposition()
            if content_type == 'text/plain' and disp != 'attachment':
                try:
                    body_text = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='replace')
                except Exception:
                    body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')
            elif content_type == 'text/html' and disp != 'attachment':
                try:
                    body_html = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='replace')
                except Exception:
                    body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
        
        # Estrai mittente e destinatari in formati semplici
        def _simplify_address(addr):
            if not addr:
                return ''
            name, email_addr = email.utils.parseaddr(addr)
            return email_addr
        
        sender = _simplify_address(from_addr)
        recipients = [_simplify_address(a.strip()) for a in to_addr.split(',')] if to_addr else []
        
        data = {
            'email_id': email_id,
            'msg_id': msg_id,
            'folder': folder,
            'subject': subject,
            'from': sender,
            'to': recipients,
            'date': parsed_date.isoformat() if isinstance(parsed_date, datetime) else str(parsed_date),
            'body_text': body_text,
            'body_html': body_html,
            'raw_headers': dict(email_message.items()),
        }
        
        return data
    
    async def _extract_attachments(self, email_message, email_id: str) -> List[Dict[str, Any]]:
        """Estrae gli allegati e li salva su disco se configurato"""
        attachments = []
        att_config = self.config.get('attachments', {})
        save_path = att_config.get('save_path', './attachments')
        allowed_types = att_config.get('allowed_types', [])
        max_size = att_config.get('max_size_bytes', 50 * 1024 * 1024)  # 50MB
        
        for part in email_message.walk():
            disposition = part.get_content_disposition()
            if disposition != 'attachment':
                continue
            
            filename = part.get_filename()
            if not filename:
                ext = part.get_content_subtype()
                filename = f'attachment-{uuid.uuid4()}.{ext}'
            
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            
            if allowed_types:
                ctype = part.get_content_type()
                if ctype not in allowed_types:
                    continue
            
            if len(payload) > max_size:
                self.log_warning(f'Allegato {filename} troppo grande: {len(payload)} bytes')
                continue
            
            # Salva su disco
            Path(save_path).mkdir(parents=True, exist_ok=True)
            file_path = os.path.join(save_path, filename)
            try:
                with open(file_path, 'wb') as f:
                    f.write(payload)
                file_hash = hashlib.sha256(payload).hexdigest()
                attachments.append({
                    'filename': filename,
                    'path': file_path,
                    'content_type': part.get_content_type(),
                    'size': len(payload),
                    'sha256': file_hash,
                })
                
                # Emetti evento per allegato estratto
                await self.emit_event('attachment_extracted', {
                    'email_id': email_id,
                    'filename': filename,
                    'path': file_path,
                    'sha256': file_hash,
                })
                
            except Exception as e:
                self.log_error(f'Errore salvando allegato {filename}: {e}')
                await self._emit_processing_error('attachment_save', str(e))
        
        return attachments
    
    async def _post_process_email(self, mail, msg_id: str, email_message):
        """Azioni post-processing: marca come letta o sposta la mail, in base alla configurazione"""
        try:
            processing_cfg = self.config.get('processing', {})
            mark_read = processing_cfg.get('mark_as_seen', True)
            move_to = processing_cfg.get('move_to_folder', None)
            
            if mark_read:
                mail.store(msg_id, '+FLAGS', '\\Seen')
            
            if move_to:
                # Copia e cancella
                mail.copy(msg_id, move_to)
                mail.store(msg_id, '+FLAGS', '\\Deleted')
                mail.expunge()
        except Exception as e:
            self.log_warning(f'Errore post-processing email {msg_id}: {e}')
    
    async def _check_pop3_emails(self):
        """Controlla email via POP3 (semplice implementazione)"""
        conn_config = self.config.get('connection', {})
        server = conn_config.get('server')
        port = conn_config.get('port', 995)
        username = conn_config.get('username')
        password = conn_config.get('password')
        use_ssl = conn_config.get('use_ssl', True)
        
        try:
            if use_ssl:
                pop_conn = poplib.POP3_SSL(server, port)
            else:
                pop_conn = poplib.POP3(server, port)
            
            pop_conn.user(username)
            pop_conn.pass_(password)
            
            # Recupera elenco messaggi
            resp, items, octets = pop_conn.list()
            msg_nums = [int(x.split()[0]) for x in items]
            
            for num in msg_nums:
                try:
                    resp, lines, octets = pop_conn.retr(num)
                    raw_message = b"\r\n".join(lines)
                    email_message = email.message_from_bytes(raw_message)
                    # Per POP3 non abbiamo un msg_id facile; usiamo hash
                    msg_hash = hashlib.sha256(raw_message).hexdigest()
                    msg_id = msg_hash
                    folder = 'POP3'
                    # Filtri
                    if not await self._passes_filters(email_message):
                        continue
                    email_data = await self._extract_email_data(email_message, msg_id, folder)
                    if self.config.get('attachments', {}).get('extract_attachments', True):
                        attachments = await self._extract_attachments(email_message, email_data['email_id'])
                        email_data['attachments'] = attachments
                    await self.emit_event('email_received', email_data)
                    
                    # Cancella se richiesto
                    if self.config.get('processing', {}).get('delete_after_retrieve', False):
                        pop_conn.dele(num)
                except Exception as e:
                    self.log_error(f'Errore processando messaggio POP3 {num}: {e}')
                    await self._emit_processing_error('pop3_processing', str(e))
            
            pop_conn.quit()
        except Exception as e:
            self.log_error(f'Errore connessione POP3: {e}')
            await self._emit_processing_error('pop3_connection', str(e))
    
    async def _emit_processing_error(self, error_type: str, message: str, reference: Optional[str] = None):
        payload = {
            'error_type': error_type,
            'message': message,
            'reference': reference,
            'timestamp': datetime.utcnow().isoformat()
        }
        try:
            await self.emit_event('email_processing_error', payload)
        except Exception:
            self.log_error('Impossibile emettere evento di errore')
    
    # Wrapper generico per emissione eventi (compatibile con PDK)
    async def emit_event(self, event_type: str, payload: Dict[str, Any]):
        try:
            # Metodo presente in BaseEventSourceProcessor; qui fallback
            await super().emit_event(event_type, payload)
        except Exception:
            # Fallback: loggare
            self.log_info(f'Emit {event_type}: {json.dumps(payload)}')


# Se eseguito come script per test rapido
if __name__ == '__main__':
    import asyncio
    async def main():
        logging.basicConfig(level=logging.DEBUG)
        src = EmailMonitorEventSource()
        cfg = {
            'connection': {
                'server': 'imap.example.com',
                'username': 'user@example.com',
                'password': 'secret',
                'protocol': 'IMAP',
                'port': 993,
                'use_ssl': True,
            },
            'folders': ['INBOX'],
            'polling_interval': 10,
            'attachments': {
                'extract_attachments': True,
                'save_path': './tmp_attachments',
                'allowed_types': [],
            },
            'processing': {
                'mark_as_seen': True,
                'move_to_folder': None,
            }
        }
        await src.initialize(cfg)
        await src.start()
        # aspetta un ciclo
        await asyncio.sleep(2)
        await src.stop()
    asyncio.run(main())
