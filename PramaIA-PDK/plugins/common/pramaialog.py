"""
Client Python per il servizio di logging PramaIA.

Questo modulo fornisce un client per inviare log al servizio
PramaIA-LogService. Può essere utilizzato da qualsiasi componente
Python dell'ecosistema PramaIA.

Esempio di utilizzo:
```python
from pramaialog import PramaIALogger, LogLevel, LogProject

# Crea un'istanza del logger
logger = PramaIALogger(
    api_key="your_api_key",
    project=LogProject.SERVER,
    module="workflow_service"
)

# Invia log di diversi livelli
logger.info("Servizio avviato")
logger.warning("Attenzione: file di configurazione non trovato", 
               details={"config_path": "/path/to/config"})
logger.error("Errore durante il caricamento del workflow", 
             details={"workflow_id": "123", "error": str(e)},
             context={"user_id": "admin"})
```
"""

import requests
import os
import logging
import json
import queue
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union
import uuid

# Imposta il logger standard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pramaialog-client")

class LogLevel(str, Enum):
    """Livelli di log supportati."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    LIFECYCLE = "lifecycle"  # Livello speciale per tracciare il ciclo di vita dei documenti

class LogProject(str, Enum):
    """Progetti PramaIA supportati."""
    SERVER = "PramaIAServer"
    PDK = "PramaIA-PDK"
    AGENTS = "PramaIA-Agents"
    PLUGINS = "PramaIA-Plugins"
    OTHER = "other"

class PramaIALogger:
    """
    Client per il servizio di logging PramaIA.
    
    Fornisce metodi per inviare log di diversi livelli al servizio
    PramaIA-LogService.
    """
    
    def __init__(
        self,
        api_key: str,
        project: LogProject,
        module: str,
        host: Optional[str] = None,
        buffer_size: int = 100,
        auto_flush: bool = True,
        flush_interval: int = 5,
        retry_max_attempts: int = 3,
        retry_delay: int = 1
    ):
        """
        Inizializza il client di logging.
        
        Args:
            api_key: API key per l'autenticazione con il servizio
            project: Progetto a cui appartiene il modulo che genera i log
            module: Nome del modulo che genera i log
            host: Host del servizio di logging (incluso protocollo e porta)
            buffer_size: Dimensione massima del buffer prima del flush automatico
            auto_flush: Se True, invia automaticamente i log in batch
            flush_interval: Intervallo in secondi tra i flush automatici
            retry_max_attempts: Numero massimo di tentativi in caso di errore
            retry_delay: Ritardo in secondi tra i tentativi
        """
        self.api_key = api_key
        self.project = project
        self.module = module
        # Determina host dal parametro, oppure dalla variabile d'ambiente PRAMAIALOG_HOST,
        # o usa il fallback "http://localhost:8081"
        if host:
            resolved_host = host
        else:
            resolved_host = os.getenv('PRAMAIALOG_HOST') or os.getenv('BACKEND_URL') or 'http://localhost:8081'
        # Se PRAMAIALOG_PORT è impostata e resolved_host non contiene già una porta, aggiungila
        port_env = os.getenv('PRAMAIALOG_PORT')
        if port_env and ':' not in resolved_host.split('//')[-1]:
            resolved_host = f"{resolved_host.rstrip('/') }:{port_env}"
        self.host = resolved_host.rstrip("/")
        self.buffer_size = buffer_size
        self.auto_flush = auto_flush
        self.flush_interval = flush_interval
        self.retry_max_attempts = retry_max_attempts
        self.retry_delay = retry_delay
        
        # Buffer per i log
        self.log_buffer = queue.Queue(maxsize=buffer_size * 2)
        
        # Crea thread per flush automatico
        if auto_flush:
            self.running = True
            self.flush_thread = threading.Thread(target=self._auto_flush_worker)
            self.flush_thread.daemon = True
            self.flush_thread.start()
    
    def debug(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invia un log di livello DEBUG."""
        return self.log(LogLevel.DEBUG, message, details, context)
    
    def info(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invia un log di livello INFO."""
        return self.log(LogLevel.INFO, message, details, context)
    
    def warning(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invia un log di livello WARNING."""
        return self.log(LogLevel.WARNING, message, details, context)
    
    def error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invia un log di livello ERROR."""
        return self.log(LogLevel.ERROR, message, details, context)
    
    def critical(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invia un log di livello CRITICAL."""
        return self.log(LogLevel.CRITICAL, message, details, context)
        
    def lifecycle(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Invia un log di livello LIFECYCLE.
        
        Questo livello è specifico per tracciare gli eventi del ciclo di vita dei documenti
        come creazione, modifica, cancellazione, upload, ecc.
        
        Args:
            message: Il messaggio da registrare
            details: Dizionario con dettagli aggiuntivi
            context: Contesto dell'evento
            
        Returns:
            ID del log creato
        """
        # Aggiungi automaticamente un marker al messaggio
        marked_message = f"🔄 [LIFECYCLE] {message}"
        
        # Aggiungi il tag log_type per garantire la compatibilità con le versioni precedenti
        lifecycle_details = details.copy() if details else {}
        lifecycle_details["log_type"] = "lifecycle"
            
        # Se non c'è già un lifecycle_event, aggiungiamolo
        if "lifecycle_event" not in lifecycle_details:
            # Estrai un nome di evento dal messaggio o usa un valore predefinito
            import re
            event_match = re.search(r'\b([A-Z_]+)\b', message)
            lifecycle_details["lifecycle_event"] = event_match.group(1) if event_match else "GENERIC_EVENT"
        
        # Usa il livello LIFECYCLE direttamente
        return self.log(LogLevel.LIFECYCLE, marked_message, lifecycle_details, context)
    
    def log(
        self,
        level: LogLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Aggiunge un log al buffer.
        
        Args:
            level: Livello del log
            message: Messaggio del log
            details: Dettagli aggiuntivi (opzionale)
            context: Contesto del log (opzionale)
            
        Returns:
            ID del log creato
        """
        log_id = str(uuid.uuid4())
        
        # Assicurati che i dettagli del lifecycle abbiano il tag appropriato
        if level == LogLevel.LIFECYCLE:
            if not details:
                details = {}
            if isinstance(details, dict) and "log_type" not in details:
                details["log_type"] = "lifecycle"
        
        log_entry = {
            "id": log_id,
            "timestamp": datetime.now().isoformat(),
            "project": self.project,
            "level": level,  # Usa il livello originale, non convertire LIFECYCLE in INFO!
            "module": self.module,
            "message": message,
            "details": details,
            "context": context
        }
        
        try:
            self.log_buffer.put(log_entry, block=False)
            
            # Se il buffer è pieno, fai un flush
            if self.log_buffer.qsize() >= self.buffer_size:
                self.flush()
        except queue.Full:
            # Buffer pieno, fai un flush e poi aggiungi
            logger.warning("Buffer dei log pieno, flush forzato")
            self.flush()
            self.log_buffer.put(log_entry)
        
        return log_id
    
    def flush(self) -> bool:
        """
        Invia tutti i log in coda al servizio.
        
        Returns:
            True se tutti i log sono stati inviati con successo, False altrimenti
        """
        if self.log_buffer.empty():
            return True
        
        # Estrai tutti i log dal buffer
        logs = []
        try:
            while not self.log_buffer.empty():
                logs.append(self.log_buffer.get(block=False))
                self.log_buffer.task_done()
        except queue.Empty:
            pass
        
        if not logs:
            return True
        
        # Invia i log al servizio
        url = f"{self.host}/api/logs/batch"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        # Fai più tentativi in caso di errore
        attempt = 0
        while attempt < self.retry_max_attempts:
            try:
                response = requests.post(url, headers=headers, json=logs, timeout=10)
                
                if response.status_code == 201:
                    return True
                else:
                    logger.error(f"Errore nell'invio dei log: {response.status_code} - {response.text}")
                    attempt += 1
                    if attempt < self.retry_max_attempts:
                        time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Errore durante l'invio dei log: {str(e)}")
                attempt += 1
                if attempt < self.retry_max_attempts:
                    time.sleep(self.retry_delay)
        
        # Se arriviamo qui, tutti i tentativi sono falliti
        # Riinserire i log nel buffer
        for log in logs:
            try:
                self.log_buffer.put(log, block=False)
            except queue.Full:
                logger.error(f"Impossibile riaggiungere un log al buffer: {log}")
        
        return False
    
    def _auto_flush_worker(self):
        """Thread worker per il flush automatico."""
        while self.running:
            time.sleep(self.flush_interval)
            try:
                self.flush()
            except Exception as e:
                logger.error(f"Errore durante il flush automatico: {str(e)}")
    
    def close(self):
        """
        Chiude il logger, flushando tutti i log in coda.
        """
        self.running = False
        if hasattr(self, 'flush_thread') and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=2)
        
        self.flush()


# Funzione di utilità per configurare facilmente il logger
def setup_logger(
    api_key: str,
    project: Union[LogProject, str],
    module: str,
    host: Optional[str] = None
) -> PramaIALogger:
    """
    Configura e restituisce un'istanza di PramaIALogger.
    
    Args:
        api_key: API key per l'autenticazione
        project: Progetto PramaIA (LogProject o stringa)
        module: Nome del modulo
        host: Host del servizio di logging
        
    Returns:
        Un'istanza configurata di PramaIALogger
    """
    # Converti la stringa in enum se necessario
    if isinstance(project, str):
        try:
            project = LogProject(project)
        except ValueError:
            project = LogProject.OTHER
    
    return PramaIALogger(
        api_key=api_key,
        project=project,
        module=module,
        host=host
    )
