"""
Modulo di registrazione eventi del sistema.
"""

import logging
from datetime import datetime
import uuid
from typing import Dict, Any, Optional
from core.models import LogEntry, LogLevel, LogProject
from core.log_manager import LogManager

logger = logging.getLogger("LogService.SystemEvents")
log_manager = LogManager()

def register_lifecycle_event(
    message: str,
    details: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    module: str = "system_events"
):
    """
    Registra un evento LIFECYCLE nel sistema.
    
    Args:
        message: Messaggio dell'evento
        details: Dettagli aggiuntivi dell'evento
        context: Contesto dell'evento
        module: Nome del modulo che genera l'evento
    
    Returns:
        ID dell'evento registrato
    """
    try:
        if details is None:
            details = {}
        
        if context is None:
            context = {}
        
        # Assicura che il contesto abbia il campo component
        if "component" not in context:
            context["component"] = "logservice"
        
        # Aggiunge l'indicazione che è un evento di lifecycle
        details["log_type"] = "lifecycle"
        details["event_time"] = datetime.now().isoformat()
        
        # Crea l'entry di log
        log_entry = LogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            project=LogProject.SERVER,
            level=LogLevel.LIFECYCLE,
            module=module,
            message=message,
            details=details,
            context=context
        )
        
        # Registra l'evento
        log_id = log_manager.add_log(log_entry)
        logger.info(f"Evento LIFECYCLE registrato: {message} (ID: {log_id})")
        return log_id
    
    except Exception as e:
        logger.error(f"Errore durante la registrazione dell'evento LIFECYCLE: {str(e)}", exc_info=True)
        return None