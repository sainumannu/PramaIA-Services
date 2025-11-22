import os
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Optional

# Logger adapter: prefer local .logger, fallback to pramaialog client, else stdlib
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except Exception:
    try:
        from PramaIA_LogService.clients.pramaialog import PramaIALogger

        _pl = PramaIALogger()

        def log_debug(*a, **k):
            try:
                _pl.debug(*a, **k)
            except Exception:
                pass

        def log_info(*a, **k):
            try:
                _pl.info(*a, **k)
            except Exception:
                pass

        def log_warning(*a, **k):
            try:
                _pl.warning(*a, **k)
            except Exception:
                pass

        def log_error(*a, **k):
            try:
                _pl.error(*a, **k)
            except Exception:
                pass
    except Exception:
        import logging as _std_logging
        _logger = _std_logging.getLogger(__name__)

        def log_debug(*a, **k):
            _logger.debug(*a, **k)

        def log_info(*a, **k):
            _logger.info(*a, **k)

        def log_warning(*a, **k):
            _logger.warning(*a, **k)

        def log_error(*a, **k):
            _logger.error(*a, **k)

class EmailOutputProcessor:
    """
    Processore per il nodo di output email.
    Invia email con il contenuto specificato.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.smtp_server = config.get("smtp_server", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username", "")
        self.smtp_password = config.get("smtp_password", "")
        self.default_recipient = config.get("default_recipient", "")
        self.default_subject = config.get("default_subject", "Output dal workflow PramaIA")
        self.from_name = config.get("from_name", "PramaIA Workflow")
        self.from_email = config.get("from_email", "")
        
        # Verifica configurazione minima
        if not all([self.smtp_server, self.smtp_username, 
                   self.smtp_password, self.from_email]):
            self._log_warning("Configurazione SMTP incompleta. L'invio delle email potrebbe fallire.")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e invia un'email.
        
        Args:
            inputs: Dizionario contenente l'input 'content' e opzionalmente 'subject',
                   'recipient' e 'attachments'
            
        Returns:
            Dizionario con lo stato dell'invio dell'email
        """
        if "content" not in inputs:
            raise ValueError("Input 'content' richiesto ma non fornito")
        
        content = inputs["content"]
        subject = inputs.get("subject", self.default_subject)
        recipient = inputs.get("recipient", self.default_recipient)
        attachments = inputs.get("attachments", [])
        
        if not recipient:
            raise ValueError("Nessun destinatario specificato, né nell'input né nella configurazione")
        
        try:
            # Prepara il messaggio email
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Aggiungi il corpo dell'email
            msg.attach(MIMEText(content, 'plain'))
            
            # Aggiungi gli allegati se presenti
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as file:
                            attachment = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
                            attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                            msg.attach(attachment)
                    else:
                        self._log_warning(f"Allegato non trovato: {attachment_path}")
            
            # Connessione al server SMTP e invio dell'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Abilita la crittografia TLS
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            # Prepara l'output con lo stato di successo
            return {
                "status": {
                    "success": True,
                    "message": f"Email inviata con successo a {recipient}",
                    "timestamp": self._get_current_timestamp()
                }
            }
            
        except Exception as e:
            # Gestione degli errori
            error_message = str(e)
            self._log_error(f"Errore nell'invio dell'email: {error_message}")
            
            # Prepara l'output con lo stato di errore
            return {
                "status": {
                    "success": False,
                    "message": f"Errore nell'invio dell'email: {error_message}",
                    "timestamp": self._get_current_timestamp(),
                    "error": error_message
                }
            }
    
    def _get_current_timestamp(self) -> str:
        """Ottiene un timestamp corrente in formato stringa."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        log_warning(f"[EmailOutputProcessor] ATTENZIONE: {message}")
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        log_error(f"[EmailOutputProcessor] ERRORE: {message}")
